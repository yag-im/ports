# Yag Ports Collection

Yag Ports Collection is a project designed to manage application installers and their associated dependencies.

## Terms

### Application (app)

Main entity, while `yag.im` primarily focuses on cloud gaming, it can also support any runnable applications. These apps (games) are identified by their IGDB slugs, for example:

    the-pink-panther-hokus-pokus-pink

### App release

`App Release` is a distribution instance of an app, characterized by factors such as distribution media, language,
publisher, and more, and is identified by a unique random ID. For instance, the 1CD russian version distribution of the
game `The Pink Panther: Hokus Pokus Pink` has this specific release ID:

    780a21c5-5635-4a6d-aece-c9267b4ac8ff

### Runner

An application that enables other applications to run through emulation or native binding. Examples of runners include:
DosBox, ScummVM, and Wine. Each runner has its own distinct set of attributes and characteristics. For more details,
continue reading [runners documentation](docs/runners.md).

### Data

* Paths below are valid only when running inside a devcontainer.

`DATA_DIR` - the root data directory of the ports; mounted inside the devcontainer as:

    DATA_DIR=/mnt/data

Has a following internal structure:

    /mnt/data
            /apps
            /apps_src
            /clones
            /media
            /runners
            /tmp

`APP_SRC` - original app artifacts, such as a release image (CD/DVD), archived folders, GOG's Inno Setup EXE files, as
well as patches and language packs., reside in:

    $DATA_DIR/apps_src

Example:

    $DATA_DIR/apps_src/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/HPP.mdf

`RUNNER_SRC` - directory containing runner source artifacts, reside in:

    $DATA_DIR/runners/src

Example:

    $DATA_DIR/runners/src/win9x/win98se-en/win98se.iso

`RUNNER_BUNDLE` - directory containing common OS and runtime-specific data, such as WINE bottles, Win3.11 folders for
DOSBox, and more. It typically consists of a combination of installed OS images from `RUNNER_SRC` along with drivers and utilities, reside in:

    $DATA_DIR/runners/bundles

Example:

    $DATA_DIR/runners/bundles/dosbox-x/win311-en/...

`APP_RELEASE_BUNDLE` - combined `RUNNER_BUNDLE` and the `APP_SRC` data with all patches and config changes applied on
the top, reside in:

    $DATA_DIR/apps

Example:

    $DATA_DIR/apps/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/...

`APP_CLONE` - users' own copy of an `APP_RELEASE_BUNDLE`, resides in:

    $DATA_DIR/clones

Example:

    $DATA_DIR/clones/50000/the-pink-panther-hokus-pokus-pink/780a21c5-5635-4a6d-aece-c9267b4ac8ff/...

* 50000 is a unique user's ID within a system.

## Development

Before opening this project as devcontainer, make sure ports data directory (`~/yag/data/ports`) is created on the
host machine:

Example 1: ports directory backed with a dedicated SSD drive:

    sudo mount -t ntfs-3g -o rw,user,exec,uid=1000,gid=1000,dmask=0007,fmask=0007 /dev/sda1 /mnt/yag_data_drive
    ln -s /mnt/yag_data_drive/yag_data/ports ~/yag/data/ports

Example 2: basic ports directory

    mkdir -p ~/yag/data/ports

and mounted inside the devcontainer as: $DATA_DIR (check `.devcontainer/devcontainer.json` - `mounts` parameter).

## Cloud environment

For cloud deployments, `APP_RELEASE_BUNDLE`s from the ports data directory should be distributed to `appstor` nodes in
all regions, and `APP_SRC` artifacts will be stored to the cloud backup persistent storage (e.g. AWS S3 Glacier).

### Publish ports

In order to publish ports to remote appstor instances, you'll need to copy `bastion` host keys into the devcontainer.
For that copy files below:

    infra/tofu/modules/bastion/files/secrets/prod/id_ed25519
    infra/tofu/modules/bastion/files/secrets/prod/id_ed25519.pub

into:

    .devcontainer/secrets

directory and rebuild the devcontainer instance.

## Online databases

Every new game port entry must be listed in [IGDB](https://www.igdb.com/). If it's not, it should be added upon request.
Ideally, it should also be available in:
- [QuestZone](https://questzone.ru/enzi)
- [MobyGames](https://www.mobygames.com)
- [Lutris](https://lutris.net/games)
- [Adventure Gamer](https://adventuregamers.com)
- [PC Gaming Wiki](https://www.pcgamingwiki.com/wiki/Home)

## What's next

Continue reading [Add new port](docs/new-port.md) manual.
