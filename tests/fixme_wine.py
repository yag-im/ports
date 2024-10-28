from pathlib import Path

from lib.wine.wine import (
    VirtualDesktopResolution,
    Wine,
)


def test_init(tmp_path: Path):
    w = Wine()
    w.init(tmp_path, virtual_desktop=VirtualDesktopResolution.RES_640x480)
    assert w.prefix.exists()
    assert w.virtual_desktop == VirtualDesktopResolution.RES_640x480


def test_get_overrides_env():
    w = Wine()
    assert w.get_overrides_env() == ""

    dll_overrides = {}
    dll_overrides["mshtml"] = "d"
    dll_overrides["mscoree"] = "d"
    assert w.get_overrides_env(dll_overrides) == "mscoree,mshtml=d"


def test_gen_run_script(tmp_path: Path):
    w = Wine()
    w.init(tmp_path)
    assert w.prefix.exists()
    w.gen_run_script("myapp.exe")
    with open(tmp_path / "run.sh", "r") as f:
        lines = f.readlines()
        assert "wine myapp.exe\n" in lines

    w = Wine()
    w.init(tmp_path, virtual_desktop=VirtualDesktopResolution.RES_640x480)
    w.gen_run_script("myapp.exe")
    with open(tmp_path / "run.sh", "r") as f:
        lines = f.readlines()
        assert "wine explorer /desktop=mydesktop,640x480 myapp.exe\n" in lines
