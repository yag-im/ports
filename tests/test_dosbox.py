from lib.dosbox.helpers import to_short_path
from lib.dosbox.misc import DosCmdExec


def test_misc_dos_cmd():
    assert next(DosCmdExec("XCOPY", ["X:\\SYSTEM.INI", "C:\\WINDOWS"]).iter()) == "XCOPY X:\\SYSTEM.INI C:\\WINDOWS"
    assert next(DosCmdExec("BOOT", ["C:"]).iter()) == "BOOT C:"
    assert next(DosCmdExec("D:\\").iter()) == "D:\\"

    iter = DosCmdExec("D:\APP\GAME.EXE", ["arg1", "arg2"]).iter()
    assert next(iter) == "D:"
    assert next(iter) == "CD D:\\APP"
    assert next(iter) == "GAME.EXE arg1 arg2"


def test_to_short_path():
    # Path with a space in the filename gets shortened
    assert to_short_path("D:\\APP\\TKKG 8.EXE") == "D:\\APP\\TKKG8~1.EXE"
    # Path without spaces is unchanged
    assert to_short_path("D:\\APP\\GAME.EXE") == "D:\\APP\\GAME.EXE"
    # Space in a directory component
    assert to_short_path("C:\\PROGRAM FILES\\GAME\\GAME.EXE") == "C:\\PROGRA~1\\GAME\\GAME.EXE"
    # Space in filename without extension
    assert to_short_path("D:\\APP\\MY GAME") == "D:\\APP\\MYGAME~1"
