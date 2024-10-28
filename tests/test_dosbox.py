from lib.dosbox.misc import DosCmdExec


def test_misc_dos_cmd():
    assert next(DosCmdExec("XCOPY", ["X:\\SYSTEM.INI", "C:\\WINDOWS"]).iter()) == "XCOPY X:\\SYSTEM.INI C:\\WINDOWS"
    assert next(DosCmdExec("BOOT", ["C:"]).iter()) == "BOOT C:"
    assert next(DosCmdExec("D:\\").iter()) == "D:\\"

    iter = DosCmdExec("D:\APP\GAME.EXE", ["arg1", "arg2"]).iter()
    assert next(iter) == "D:"
    assert next(iter) == "CD D:\\APP"
    assert next(iter) == "GAME.EXE arg1 arg2"
