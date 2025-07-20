# Adding a new port

## Vars

    DATA_DIR=/mnt/data - ports data dir mounted into the ports' devcontainer
    TMP_APP_SRC_DIR=$DATA_DIR/tmp - temporary dir for apps sources
    IGDB_SLUG - apps' IGDB slug (e.g. the-pink-panther-hokus-pokus-pink)
    APP_RELEASE_UUID - unique id generated for every new app release (e.g. 780a21c5-5635-4a6d-aece-c9267b4ac8ff)

## Initial setup

**Step 1**

Run:

    scripts/setup.sh $IGDB_SLUG

This step performs following actions:

- generates a new release uuid;
- creates empty dir for app source files:
    $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID;
- creates an app installer template:
    $PORTS_ROOT_DIR/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml
- updates vscode launch script (for local debugging):
    $PORTS_ROOT_DIR/.vscode/launch.json
- generates requests.http (to simplify local publishing):
    $PORTS_ROOT_DIR/scripts/tmp/requests.http

## Sources artifacts

**Step 2**

Download port sources artifacts (ISO images, GOG setup files, patches etc) or prepare yours if you own any.

Make sure you're performing this step from a third-party remote server to avoid internet providers' rules violation.

Examples:

    transmission-cli "magnet:?xt=urn:btih:B2ADE7450A687065153896C0C70463D7C4003BF5&tr=http%3A%2F%2Fbt.t-ru.org%2Fann%3Fmagnet&dn=%5BCD%5D%20Safecracker%20%5BENG%5D%20(1996%2C%20Adventure)" \
        -w $TMP_APP_SRC_DIR \
        -b http://john.bitsurge.net/public/biglist.p2p.gz

    wget https://archive.org/download/SOLARSYS_WIN/SOLARSYS.zip -o $TMP_APP_SRC_DIR/SOLARSYS.zip

**Step 2.1**

Unpack all archived sources (iso, mdf etc) into the local app sources storage, e.g.:

    $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID/CD1.iso
    $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID/CD2.iso

and remove original archives.

**Step 2.2 (optional, when localized media assets are available)**

Download any available localized media assets (such as covers and screenshots) into the $DATA_DIR/media directory. The
default assets should be accessible from IGDB, so start by checking the game's page to ensure it includes a cover and
screenshots. If any are missing, add them (to IGDB) and refresh the local SQL DB using scrapers [TODO: ref].

## Writing a new installer

**Step 3**

This step includes writing a new runner and installer.

Creating a new runner in the `$DATA_DIR/runners` folder; This step is almost never required as most popular runners are
already there.

The app installer and descriptor are contained within the same YAML file:

    /workspaces/ports/ports/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml

In order to fill in app descriptor details, search for all available references in the third-party catalogs (MobyGames,
QuestZone etc). Update appropriate fields in the file above with the discovered info.

In order to write a new installer follow [Writing installers](installers.md) instruction.

## Local install and test

**Step 4**

Make sure `SQL DB` and `portsvc` services are up and running locally. Update local `SQL DB` instance by invoking
`upsertAppRelease` function from `scripts/tmp/requests.http`. Alternatively, you can run `curl` directly:

    curl -v --request POST \
        --socks5-hostname 0:8022 \
        --header 'content-type: application/x-yaml' \
        --data-binary @/workspaces/ports/ports/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml \
        http://portsvc/ports/apps/$IGDB_SLUG/releases/$APP_RELEASE_UUID

**Step 4.1**

We need to make sure everything works as expected locally. For that we need to install a new app. Installing an app can
be performed from command line:

        yag install games/$IGDB_SLUG --release=$APP_RELEASE_UUID

or from IDE (recommended):

    Select "yag cli" in the launcher menu and hit "F5" (start debugging).

$PORTS_ROOT_DIR/.vscode/launch.json will be updated for you by the setup.sh script on step 1.

**Step 4.2**

Run all relevant services [TODO: ref] and open http://localhost:8080/ in the browser. Select and run installed app.
Make sure all golden flows (start/play/save/exit) are working as expected.

## Prod publishing (optional, for cloud deployments only)

At that point, app sources should be located at:

    $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID

and app bundle installed into:

    $DATA_DIR/apps/$IGDB_SLUG/$APP_RELEASE_UUID

**Step 5**

Invoke:

    scripts/publish.sh $IGDB_SLUG $APP_RELEASE_UUID

This performs steps below:

    - Uploads app bundle files into the clouds' primary appstor instance (will be lsynced to all secondary appstor
        instances from there automatically);
    - Archives and uploads game sources into the cold storage (AWS Glacier);
    - Uploads all media assets (including custom localized) into the media artifacts storage (AWS S3 CDN);
    - Updates prod SQL DB with a new release entry.

### Test app in prod.

**Step 6**

Make sure all golden flows (start/play/save/exit) are working as expected. If something went wrong then hide the failing
app (use the `games.releases.is_visible` flag) and fix the issue ASAP.

### Announce a new app release.

**Step 7**
Post a new release message to the https://discord.com/channels/1251206620822638684/1251209249460060180 channel and
reddit group: https://www.reddit.com/r/yagim.

## FAQ:

Q: Game cursor appears in a semi-transparent square (e.g. "James Camerons' Titanic", "Escape From The Haunted House",
"Peter Gabriel: Eve")
A: Set color_bits to 24

Q: How to rip audio tracks?
A: Use CD audio ripper "freac" (can't be run from docker, AppImage requires FUSE kernel module):

    wget -O /tmp/freac-1.1.7-linux-x86_64.AppImage https://github.com/enzo1982/freac/releases/download/v1.1.7/freac-1.1.7-linux-x86_64.AppImage
    chmod a+x /tmp/freac-1.1.7-linux-x86_64.AppImage
    /tmp/freac-1.1.7-linux-x86_64.AppImage

Q: dosbox win9x installer closes immediately
A: use runexit=False

Q: LCOPY hangs in dosbox when copying from mounted CDROM image
A: make sure your CDROM source is an image, not a directory

Q: no midi sound in dosbox-x
A: check sound font availability (/usr/share/sounds/sf2/default-GM.sf2) and a "midi" section in dosbox.conf

Q: how to propagate files into dosbox-x disk images from host?
A:
    - create a folder X and put files there
    - update dosbox.conf with:

        mount X X

    - copy files from X: into C:
    - unmount X (otherwise windows will hang on boot):

        mount -u X

    - boot system:

        boot C:

Q: The app runs in one environment but not in another, even though both use the same Docker image. Why?
A: It's likely due to differences in CPU clock speed. Some older applications are sensitive to processor speed and may
fail or behave unpredictably on faster systems. Try adjusting the environment's CPU performance - either slowing it down
or speeding it up. For example, "Star Wars: Yoda's Challenge Activity Center" may require throttling when running on
high clock-rate CPUs in cloud environments. You can slow wine down using:

    export WINEDEBUG=+warn,+loaddll

or something similar

Q: How to upgrade existing port?
A: Just run setup.sh / publish.sh as usual; After upgrade, you might want to delete old malfunctioned cloned versions.
For this login into appstor-master host and run:

    find /opt/yag/data/appstor/clones -type d -name "d117352e-b8b6-40bc-853f-25dd8f62c472" -exec rm -r {} +

where `d117352e-b8b6-40bc-853f-25dd8f62c472` is a UUID of updated port. Be careful and remove only broken clones.
Otherwise (in case it's just e.g. a more performant runner update) better leave cloned versions as is as it may contain users' saves.
