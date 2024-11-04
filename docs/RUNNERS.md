# Runners

## APP_BUNDLEs structure

## scummvm

    app
    scummvm.ini
    run.sh

## wine

    .wine - wine bottle with win and app deps if any. Contains drive_c folder.
    D - app folder mounted as D:
        - usually contains only a single 'app' folder
    E - CD1 folder mounted as E: (optional)
    F - CD2 folder mounted as F: (optional)
    run.sh

## dosbox-x

### win98

#### System tuning:

    System properties:
        Performance -> File System -> Read-ahead optimization: None
        Search for new floppy drive: uncheck

    Screen:
        Display properties -> Appearance -> Color: black
        Resolution: 640x480
        Color bits: 16

    Control panel:
        Sounds -> Schemes: No sounds
        Power management -> Turn Off Hard Disks: Never
        Display settings -> 16 bit
        Mouse -> Set slowest motion speed

    Folder options:
        Classic style
        Show all files
        Hide file extensions: No
        View as webpage: No

Copy [RUNEXIT.EXE](https://github.com/yag-im/runexit) into C:\WINDOWS;

Copy LCOPY.EXE into C:\UTILS.

Make "En" a default input language (in non-En versions).

From DOS:

Update C:\MSDOS.SYS:

    ...
    [options]
    AutoScan=0
    Logo=0
    ...

Delete:

    C:\WINDOWS\LOGOW.SYS - removes "Please wait while Windows is shutting down" message
    C:\WINDOWS\LOGOS.SYS - removes "It is now safe to turn off your computer" message

#### Structure:

    C - system drive image (with installed OS and app deps if any)
    D - app drive image mounted as D: (var size, depends on the app)
        - 'app' folder with app data
    E - CD1 image mounted as E: (optional)
    F - CD2 image mounted as F: (optional)
    X - aux gate folder (to copy files inside dosbox)
    dosbox.conf:
        - autoexec section:
            - mounts all drives
            - copies X:\SYSTEM.INI with updated Shell to C:\WINDOWS
            - boots from C drive
    run.sh:
        - runs dosbox-x -conf dosbox.conf

### win311 (and pure dos)

    C - system folder (with installed OS and app deps if any)
    D - app folder mounted as D:
        - 'app' folder with app data
    E - CD1 image mounted as E: (optional)
    F - CD2 image mounted as F: (optional)
    dosbox.conf
        - autoexec section:
            - mounts all drives
            - runs: win RUNEXEC app.exe
    run.sh:
        - runs dosbox-x -conf dosbox.conf

#### Post install

Manual steps

windows 3x dosbox guides:

https://www.vogons.org/viewtopic.php?t=9405

https://dosbox-x.com/wiki/#Guide:Installing-Windows-3.1x

# dosbox-x + win311 base bundle (en version with minimal drivers)

win311 is tied with dosbox-x by a doxbox-x mouse drivers

    LANG=ru
    RUNNERS_BASE_DIR=$DATA_DIR/runners
    RUNNERS_SRC_DIR=$RUNNERS_BASE_DIR/src
    WIN311_SRC_DIR=$RUNNERS_SRC_DIR/win311
    RUNNERS_BUNDLE_DIR=$RUNNERS_BASE_DIR/bundles
    DOSBOX_X_WIN311_BUNDLE_DIR=$RUNNERS_BUNDLE_DIR/dosbox-x/win311-$LANG
    mkdir -p $DOSBOX_X_WIN311_BUNDLE_DIR
    DOSBOX_X_CONF_PATH=/workspaces/ports/lib/dosbox/files/win311/dosbox.conf

    dosbox-x \
        -c "CHCP 866" \
        -c "MOUNT C $DOSBOX_X_WIN311_BUNDLE_DIR" \
        -c "IMGMOUNT D \"$WIN311_SRC_DIR/win3.11-$LANG.iso\" -t iso" \
        -c "D:" \
        -c "SETUP.EXE" \
        -conf $DOSBOX_X_CONF_PATH \
        -noconsole

    Choose: Custom Install option
    Full Name: gamer
    Product Number: 1337-W33D-420

Deselect all optional components (wallpapers, sounds etc)

### Drivers install

    dosbox-x \
        -c "CHCP 866" \
        -c "MOUNT C $DOSBOX_X_WIN311_BUNDLE_DIR" \
        -c "MOUNT D $WIN311_SRC_DIR" \
        -conf $DOSBOX_X_CONF_PATH \
        -noconsole

Install audio (SoundBlaster) from DOS

http://www.sierrahelp.com/Utilities/Emulators/DOSBox/3x_InstallSB.html

    D:
    cd D:\DRIVERS\SOUNDB~1\SB16W3X
    INSTALL.EXE

Select "Custom", deselect everything, answer "no" for "Load drivers (for DOS)" and proceed.

Make sure C:\WINDOWS is properly set as a WIN3.11 path on the config screen.

Change IRQ (Interrupt Setting) to 7 for dosbox-x.

    C:
    CD C:\WINDOWS
    WIN

Now set volume levels in the mixer app to "max" for everything except the microphone

#### Install video (S3) drivers

    Windows Setup -> Options -> Change system settings -> Display -> Other -> D:\DRIVERS\S3\S3DRIV~1
        -> S3 Trio 64V 640x480 256 (the very first entry)

#### Installing video driver in russian win 3.11

When asked, answer NO for replacing existing font files.
Then installation will fail at the end showing the old driver in the list, this is expected.
Exit to DOS, run setup from C:/WINDOWS and replace video driver there, answering "Keep existing driver" on the final page.

Update C:\WINDOWS\WIN.INI:

    ; set black backgroud color
        [colors]
        Background=0 0 0

    ; skip long and boring video performance optimization test
        [WinG]
        GDIOnly=1

Update C:\WINDOWS\SYSTEM.INI:

    ; skip midi check for certain games (e.g. The Adventures of Pinoccio)
        [mciseq.drv]
        disablewarning=true

Misc

Startup -> Remove Keyboard switch indicator
Sound -> Disable system sounds


#### Install mouse drivers

    Windows Setup -> Options -> Change system settings -> Mouse -> Other -> D:\DRIVERS\MOUSE
        -> DOSBox-X Mouse Pointer Integration

#### Install "QuickTime"

    File Manager -> D:\MULTIM~1\QUICKT~1\qteasy16.exe (unpacks files)
                    D:\MULTIM~1\QUICKT~1\qtinstall.exe

Skip qt search on the first stage as it crashes.

#### Install "Video for windows" (for AVI files)

    File Manager -> D:\MULTIM~1\VFW122\SETUP.EXE

#### Runexit

Copy [RUNEXIT.EXE](https://github.com/yag-im/runexit) into `C:\WINDOWS`.

## dosbox

see win311 section in dosbox-x


# FAQ

Q: dosbox win9x installer closes immediately
A: use runexit=False
