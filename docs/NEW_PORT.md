# Adding a new port

## Vars

    DATA_DIR=/mnt/data - ports data dir mounted into the ports' devcontainer
    TMP_APP_SRC_DIR=$DATA_DIR/tmp - dir for apps sources
    IGDB_SLUG - apps' IGDB slug (e.g. the-pink-panther-hokus-pokus-pink)
    APP_RELEASE_UUID - unique id generated for every new app release (e.g. 780a21c5-5635-4a6d-aece-c9267b4ac8ff)

## Initial setup

**Step 1**
Run:

    scripts/setup.sh $IGDB_SLUG

This step includes following actions:

    - generating a new release uuid;
    - creating dir for app source files:
        $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID;
    - creating dir and templates for descriptor and installer script:
        $PORTS_ROOT_DIR/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml
        $PORTS_ROOT_DIR/ports/games/$IGDB_SLUG/install.py
    - updating vscode launch script (for debugging):
        $PORTS_ROOT_DIR/.vscode/launch.json
    - generating requests.http:
        $PORTS_ROOT_DIR/scripts/tmp/requests.http

## Sources artifacts

**Step 2**
Download port sources artifacts (ISO images, gog setup files, patches etc).

Make sure you're performing this step from a third-party remote server to avoid internet providers' rules violation.

Examples:

    transmission-cli "magnet:?xt=urn:btih:B2ADE7450A687065153896C0C70463D7C4003BF5&tr=http%3A%2F%2Fbt.t-ru.org%2Fann%3Fmagnet&dn=%5BCD%5D%20Safecracker%20%5BENG%5D%20(1996%2C%20Adventure)" \
        -w $TMP_APP_SRC_DIR \
        -b http://john.bitsurge.net/public/biglist.p2p.gz

    wget https://archive.org/download/SOLARSYS_WIN/SOLARSYS.zip -o $TMP_APP_SRC_DIR/SOLARSYS.zip

**Step 2.1**
Unpack all archived sources (iso, mdf etc) into the local app sources storage, e.g.:

    $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID

and remove original archives.

**Step 2.2 [optional]**
Download localized media assets (covers, screenshots) if any into the $DATA_DIR/media folder.

## Local install and test

**Step 3**
Search for all available refs in the third-party catalogs (MobyGames, QuestZone etc). Update app descriptor at
`$PORTS_ROOT_DIR/games/$IGDB_SLUG/$APP_RELEASE_UUID.yaml` with the discovered info.

**Step 3.1**
Update local SQL DB instance by invoking `upsertAppRelease` function from `scripts/tmp/requests.http`.

**Step 3.2**
We need to make sure everything works as expected locally. For that we need to install a new app into the local
cluster first. This step includes:

    - creating a new runner (if needed) in the `$DATA_DIR/runners` folder;
    - creating a new installer:

        /workspaces/ports/ports/games/$IGDB_SLUG/install.py

    - installing a new release:

        yag install games/$IGDB_SLUG --release=$APP_RELEASE_UUID

**Step 3.3**
Run all devcontainers and open http://localhost:8080/ in the browser. Select and run installed app.

## Prod publishing

At that point, app sources should be located at:

    $DATA_DIR/apps_src/$IGDB_SLUG/$APP_RELEASE_UUID

and app installed into:

    $DATA_DIR/apps/$IGDB_SLUG/$APP_RELEASE_UUID

**Step 4**
Invoke:

    scripts/publish.sh

which performs steps below:

    - Uploading app bundle files into the clouds' primary instance;
    - Uploading game sources into the cold storage (AWS glacier);
    - Uploading all media assets (including custom localized) into the media artifacts storage (S3 CDN);
    - Updating prod SQL DB with new release entries.

## Test app in prod.

**Step 5**
Make sure all golden flows (start/play/save/exit) are working as expected. If something went wrong then hide the failing
app (use the `games.releases.is_visible` flag) and fix the issue ASAP.

## Announce new app release.

**Step 6**
Post a new release message to the https://discord.com/channels/1251206620822638684/1251209249460060180 channel.

## FAQ:

Q: Game cursor appears in a semi-transparent square (e.g. "James Camerons' Titanic", "Escape From The Haunted House", "Peter Gabriel: Eve")
A: Set color_bits to 24

Q: How to rip audio tracks?
A: Use CD audio ripper "freac" (can't be run from docker, AppImage requires FUSE kernel module):

    wget -O /ara/portable/freac-1.1.7-linux-x86_64.AppImage https://github.com/enzo1982/freac/releases/download/v1.1.7/freac-1.1.7-linux-x86_64.AppImage
    chmod a+x /ara/portable/freac-1.1.7-linux-x86_64.AppImage
    /ara/portable/freac-1.1.7-linux-x86_64.AppImage
