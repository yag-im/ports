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

    Name                   Description            Context     Example
    SRC_DIR                Source directory       Host        $DATA_DIR//apps_src/voyeur-ii/5f7b9929-4501-40c2-b42e-82d5ec3e0bcd
    DEST_DIR               Destination dir        Host        $DATA_DIR/apps/voyeur-ii/5f7b9929-4501-40c2-b42e-82d5ec3e0bcd
    APP_DIR                Destination app dir    Host        dynamic, e.g. for dosbox and wine it's: $DATA_DIR/apps/voyeur-ii/5f7b9929-4501-40c2-b42e-82d5ec3e0bcd/D/APP, for scummvm - drive letter is omitted
    PORT_FILES_DIR         Ports' files dir       Host        $PORTS_ROOT_PATH/games/voyeur-ii/files
    SYSTEM_DRIVE_LETTER    System drive letter    Guest (win) C
    APP_DRIVE_LETTER       App drive letter       Guest (win) D
    FIRST_CD_DRIVE_LETTER  First CD drive letter  Guest (win) E
    SECOND_CD_DRIVE_LETTER Second CD drive letter Guest (win) F
    THIRD_CD_DRIVE_LETTER  Third CD drive letter  Guest (win) G
    FOURTH_CD_DRIVE_LETTER Fourth CD drive letter Guest (win) H
    FIFTH_CD_DRIVE_LETTER  Fifth CD drive letter  Guest (win) I
    SIXTH_CD_DRIVE_LETTER  Sixth CD drive letter  Guest (win) J
    SYSTEM_DRIVE           System drive           Guest (win) C:\
    APP_DRIVE              App drive              Guest (win) D:\
    FIRST_CD_DRIVE         First CD drive         Guest (win) E:\
    SECOND_CD_DRIVE        Second CD drive        Guest (win) F:\
    THIRD_CD_DRIVE         Third CD drive         Guest (win) G:\
    APP_DIR                App dir                Guest (win) D:\APP

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
