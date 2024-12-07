# Writing a new installer

A typical installer is a yaml-formatted document with a following structure:

    installer:
        vars:
            ...
        tasks:
            ...

## Variables

The `vars` section defines custom variables that you can use in your installer:

    vars:
        DATA_FILENAME: US

In addition to the custom variables you define, a set of global variables available for use is listed below:

    Name                   Description            Env         Example
    DEST_DIR               Destination dir        Host        $DATA_DIR/apps/voyeur-ii/5f7b9929-4501-40c2-b42e-82d5ec3e0bcd
    SRC_DIR                Source directory       Host        $DATA_DIR//apps_src/voyeur-ii/5f7b9929-4501-40c2-b42e-82d5ec3e0bcd
    DEST_APP_DIR           Destination app dir    Host        dynamic, e.g. for dosbox and wine it's: $DATA_DIR/apps/voyeur-ii/5f7b9929-4501-40c2-b42e-82d5ec3e0bcd/D/APP, for scummvm - drive letter is omitted
    SRC_FILES_DIR          Source files dir       Host        $PORTS_ROOT_PATH/games/voyeur-ii/files
    SYSTEM_DRIVE_LETTER    System drive letter    NA          C
    APP_DRIVE_LETTER       App drive letter       NA          D
    FIRST_CD_DRIVE_LETTER  First CD drive letter  NA          E
    SECOND_CD_DRIVE_LETTER Second CD drive letter NA          F
    THIRD_CD_DRIVE_LETTER  Third CD drive letter  NA          G
    SYSTEM_DRIVE           System drive           DosBox      C:\
    APP_DRIVE              App drive              DosBox      D:\
    APP_DIR                App dir                DosBox      D:\APP
    FIRST_CD_DRIVE         First CD drive dir     DosBox      E:\
    SECOND_CD_DRIVE        Second CD drive dir    DosBox      F:\
    THIRD_CD_DRIVE         Third CD drive dir     DosBox      G:\

## Loops

Installation scripts support basic loops, as demonstrated below:

    - move:
        src: "{DEST_APP_DIR}/{DATA_FILENAME}.{item}"
        dest: "{DEST_APP_DIR}/{DATA_FILENAME}1.{item}"
        loop:
            - TXT
            - SMP
            - IDX

## Tasks

The `tasks` section is a series of Ansible-like tasks with parameters, executed in the order they are defined.
