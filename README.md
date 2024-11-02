# Yag ports collection

## Terms

* Paths below are valid only when running inside a devcontainer.

** the-pink-panther-hokus-pokus-pink: igdb slug
   780a21c5-5635-4a6d-aece-c9267b4ac8ff: app release uuid (randomly generated uuid4)
   50000: user id

PORTS_DATA_DIR=/mnt/ports_data - ports data dir mounted into the devcontainer.

`APP_SRC` - original apps' artifacts, e.g. a release image (CD/DVD), archived folder or GOG's innosetup exe file as well as patches and language packs, residing in:

    $PORTS_DATA_DIR/apps_src

Example:

    $PORTS_DATA_DIR/apps_src/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/HPP.mdf

`RUNNER_BUNDLE` - folder containing common OS and runtime specific data, e.g. WINE bottle, Win3.11 folder for DosBox etc, resides in:

    $PORTS_DATA_DIR/runners

Example: TODO

`APP_BUNDLE` - combined RUNNER_BUNDLE and the APP_SRC data with all patches and config changes applied on the top, resides in:

    $PORTS_DATA_DIR/apps

Example:

    $PORTS_DATA_DIR/apps/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/...

`APP_CLONE` - users' copy of an APP_BUNDLE, resides in:

    $PORTS_DATA_DIR/clones

Example:

    $PORTS_DATA_DIR/clones/50000/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/...

## Prerequisite

Make sure that on the host machine:

- ports data drive is properly mounted:

    Local folder (backed with a dedicated SSD drive):

        sudo mount -t ntfs-3g -o rw,user,exec,uid=1000,gid=1000,dmask=0007,fmask=0007 /dev/sda1 /mnt/ports_data_drive
        # ln -s /mnt/ports_data_drive/ports_data /mnt/ports_data

    (mounted inside the devcontainer as: $PORTS_DATA_DIR)

Update `mounts` in devcontainer.json afterwards.

From the ports data drive, `apps` will be distributed to appstor nodes in other regions (see lsyncd).

## Online databases

Game entry must exist at least in [IGDB](https://www.igdb.com/). If not - it should be added by request.
Preferrably it should be also present in:
- [QuestZone](https://questzone.ru/enzi)
- [MobyGames](https://www.mobygames.com)
- [Lutris](https://lutris.net/games)
- [Adventure Gamer](https://adventuregamers.com)
- [PC Gaming Wiki](https://www.pcgamingwiki.com/wiki/Home)

TODO: scrapers should sync SQLDB with IGDB periodically.
