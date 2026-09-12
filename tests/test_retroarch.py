import pytest

from lib.retroarch.retroarch import (
    RetroArch,
    RetroArchCore,
)


def test_retroarch_mame_gen_run_script(tmp_path):
    conf = {"mame_driver": "coco2b"}
    retroarch = RetroArch(root_dir=tmp_path, conf=conf)
    run_sh = retroarch.gen_run_script(RetroArchCore.MAME, "ALICE.DSK")

    assert run_sh.exists()
    run_sh_content = run_sh.read_text()
    expected_mame_cmd = 'coco2b -flop1 "ALICE.DSK" -rp "/home/gamer/.config/retroarch/system/mame/roms" -autoboot_delay 2 -autoboot_command LOADM"ALICE":EXEC\\n'
    assert f"echo '{expected_mame_cmd}' > \"ALICE.cmd\"" in run_sh_content
    assert 'retroarch --fullscreen --libretro=mame "$PWD/ALICE.cmd"' in run_sh_content

    cmd_file = tmp_path / "ALICE.cmd"
    assert cmd_file.exists()
    assert cmd_file.read_text() == f"{expected_mame_cmd}\n"


def test_retroarch_mame_gen_run_script_custom_conf(tmp_path):
    conf = {
        "mame_driver": "coco2b",
        "mame_media": "-flop2",
        "mame_rp": "/custom/roms",
        "mame_autoboot_delay": 5,
        "mame_autoboot_command": 'RUN"{stem}"\\n',
    }
    retroarch = RetroArch(root_dir=tmp_path, conf=conf)
    run_sh = retroarch.gen_run_script(RetroArchCore.MAME, "GAME.DSK")
    assert run_sh.exists()

    expected_mame_cmd = 'coco2b -flop2 "GAME.DSK" -rp "/custom/roms" -autoboot_delay 5 -autoboot_command RUN"GAME"\\n'
    cmd_file = tmp_path / "GAME.cmd"
    assert cmd_file.read_text() == f"{expected_mame_cmd}\n"


def test_retroarch_mame_missing_driver(tmp_path):
    retroarch = RetroArch(root_dir=tmp_path, conf={})
    with pytest.raises(ValueError, match="mame_driver is required for MAME core"):
        retroarch.gen_run_script(RetroArchCore.MAME, "ALICE.DSK")


def test_retroarch_generic_gen_run_script(tmp_path):
    retroarch = RetroArch(root_dir=tmp_path)
    run_sh = retroarch.gen_run_script(RetroArchCore.FUSE, "game.tzx")

    assert run_sh.exists()
    run_sh_content = run_sh.read_text()
    assert 'retroarch --fullscreen --libretro=fuse "$PWD/game.tzx"' in run_sh_content
