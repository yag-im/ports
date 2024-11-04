# Yag's Ports Collection

## Terms

* Paths below are valid only when running inside a devcontainer.

** the-pink-panther-hokus-pokus-pink: igdb slug
   780a21c5-5635-4a6d-aece-c9267b4ac8ff: app release uuid (randomly generated uuid4)
   50000: user id

DATA_DIR=/mnt/data - ports data directory mounted into the devcontainer.

`APP_SRC` - original apps' artifacts, e.g. a release image (CD/DVD), archived folder or GOG's innosetup exe file as well
as patches and language packs, reside in:

    $DATA_DIR/apps_src

Example:

    $DATA_DIR/apps_src/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/HPP.mdf

`RUNNER_BUNDLE` - folder containing common OS and runtime specific data, e.g. WINE bottles, Win3.11 folders for DosBox
etc, reside in:

    $DATA_DIR/runners

Example: TODO

`APP_BUNDLE` - combined RUNNER_BUNDLE and the APP_SRC data with all patches and config changes applied on the top,
reside in:

    $DATA_DIR/apps

Example:

    $DATA_DIR/apps/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/...

`APP_CLONE` - users' copy of an APP_BUNDLE, resides in:

    $DATA_DIR/clones

Example:

    $DATA_DIR/clones/50000/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/...

## Prerequisite

Before opening this project as devcontainer, make sure ports data directory (`~/yag/data/ports`) is created on the
host machine:

Example 1: ports directory backed with a dedicated SSD drive:

    sudo mount -t ntfs-3g -o rw,user,exec,uid=1000,gid=1000,dmask=0007,fmask=0007 /dev/sda1 /mnt/yag_data_drive
    ln -s /mnt/yag_data_drive/yag_data/ports ~/yag/data/ports

Example 2: simple ports directory

    mkdir -p ~/yag/data/ports

and mounted inside the devcontainer as: $DATA_DIR.

From the ports data drive, `apps` will be distributed to appstor nodes in other regions (see lsyncd).

### Publish ports

In order to publish ports to remote appstor instances (optional step), you'll need to propagate bastion host keys inside
the  devcontainer. For this copy:

    infra/tofu/modules/bastion/files/secrets/prod/id_ed25519
    infra/tofu/modules/bastion/files/secrets/prod/id_ed25519.pub

into:

    .devcontainer/secrets

folder.

## Online databases

Game entry must exist at least in [IGDB](https://www.igdb.com/). If not - it should be added by request.
Preferrably it should be also present in:
- [QuestZone](https://questzone.ru/enzi)
- [MobyGames](https://www.mobygames.com)
- [Lutris](https://lutris.net/games)
- [Adventure Gamer](https://adventuregamers.com)
- [PC Gaming Wiki](https://www.pcgamingwiki.com/wiki/Home)

TODO: scrapers should sync SQLDB with IGDB periodically.
