import shlex
from pathlib import (
    Path,
    PureWindowsPath,
)

import pytest

from lib.installer.cmd.qemu import exec_subtask
from lib.installer.utils import subst_vars
from lib.qemu.const import (
    FIRST_CD_DRIVE_LETTER,
    SECOND_CD_DRIVE_LETTER,
)
from lib.qemu.qemu import (
    CURRENT_DIR,
    Qemu,
    QemuFlavor,
)
from lib.qemu.qemu_win9x import (
    QemuWin9x,
    QemuWin9xConf,
)
from lib.qemu.qemu_winxp import (
    QemuWinXp,
    QemuWinXpConf,
)


def _qemu(root_dir: Path, flavor: QemuFlavor = QemuFlavor.WINXPSP3) -> Qemu:
    # bypass __init__: it copies bundled system images
    if flavor == QemuFlavor.WINXPSP3:
        qemu = QemuWinXp.__new__(QemuWinXp)
        qemu.conf = QemuWinXpConf()
    else:
        qemu = QemuWin9x.__new__(QemuWin9x)
        qemu.conf = QemuWin9xConf()
    qemu.root_dir = root_dir
    qemu.mount_points = []
    qemu.templates_dir = CURRENT_DIR / "templates" / flavor.value
    return qemu


@pytest.fixture(autouse=True)
def _iso_images(monkeypatch):
    monkeypatch.setattr("lib.qemu.qemu.is_iso_image", lambda _: True)


@pytest.fixture
def cd_images(tmp_path):
    images = []
    for letter in (FIRST_CD_DRIVE_LETTER, SECOND_CD_DRIVE_LETTER):
        p = tmp_path / letter
        p.write_bytes(b"")
        images.append(p)
    return images


def test_mount_cd_images_list_as_single_swappable_drive(tmp_path, cd_images):
    qemu = _qemu(tmp_path)
    qemu.mount(image_path=cd_images, media="cdrom", letter=FIRST_CD_DRIVE_LETTER)

    assert len(qemu.mount_points) == 1
    mp = qemu.mount_points[0]
    assert mp.image_path == cd_images[0]
    assert mp.swap_images == cd_images[1:]
    assert qemu._mount_args() == [
        "-drive",
        "file=E,if=none,id=cd0,media=cdrom",
        "-device",
        "ide-cd,drive=cd0,bus=ide.1,unit=0",
        "-cdrom-swap",
        "drive=cd0,file=F",
    ]


def test_mount_single_cd_image_has_no_swap(tmp_path, cd_images):
    qemu = _qemu(tmp_path)
    qemu.mount(image_path=cd_images[0], media="cdrom", letter=FIRST_CD_DRIVE_LETTER)
    assert "-cdrom-swap" not in qemu._mount_args()


def test_mount_swap_lists_bound_to_own_drives(tmp_path):
    images = []
    for name in ("A1.iso", "A2.iso", "B1.iso", "B2.iso", "B3.iso"):
        (tmp_path / name).write_bytes(b"")
        images.append(tmp_path / name)
    qemu = _qemu(tmp_path)
    qemu.mount(image_path=images[:2], media="cdrom", letter="E")
    qemu.mount(image_path=images[2:], media="cdrom", letter="F")

    args = qemu._mount_args()
    swaps = [args[i + 1] for i, a in enumerate(args) if a == "-cdrom-swap"]
    assert swaps == ["drive=cd0,file=A2.iso", "drive=cd1,file=B2.iso", "drive=cd1,file=B3.iso"]
    # WinXP: E (cd0) on ide.1 unit 1, F (cd1) on unit 0
    assert "ide-cd,drive=cd0,bus=ide.1,unit=1" in args
    assert "ide-cd,drive=cd1,bus=ide.1,unit=0" in args


def test_mount_list_requires_cdrom(tmp_path, cd_images):
    qemu = _qemu(tmp_path)
    with pytest.raises(ValueError):
        qemu.mount(image_path=cd_images, media="disk", letter="E")


def test_mount_escapes_commas(tmp_path):
    images = [tmp_path / "Disc 1, Intro.iso", tmp_path / "Disc 2, Game.iso"]
    for p in images:
        p.write_bytes(b"")
    qemu = _qemu(tmp_path)
    qemu.mount(image_path=images, media="cdrom", letter="E")
    args = qemu._mount_args()
    assert "file=Disc 1,, Intro.iso,if=none,id=cd0,media=cdrom" in args
    assert "drive=cd0,file=Disc 2,, Game.iso" in args


def test_umount_removes_all_images(tmp_path, cd_images):
    qemu = _qemu(tmp_path)
    qemu.mount(image_path=cd_images, media="cdrom", letter=FIRST_CD_DRIVE_LETTER)
    qemu.umount(FIRST_CD_DRIVE_LETTER)
    assert not qemu.mount_points
    assert not any(p.exists() for p in cd_images)


@pytest.mark.parametrize("flavor", [QemuFlavor.WINXPSP3, QemuFlavor.WIN98SE])
def test_gen_run_script_contains_swap_images(tmp_path, flavor):
    images = [tmp_path / "CD 1.iso", tmp_path / "CD 2.iso"]
    for p in images:
        p.write_bytes(b"")
    qemu = _qemu(tmp_path, flavor)
    qemu.mount(image_path=images, media="cdrom", letter="E")

    run_sh = Qemu.gen_run_script(qemu, PureWindowsPath("D:\\APP\\GAME.EXE"))
    qemu_line = next(line for line in run_sh.read_text().splitlines() if line.startswith("qemu-system-x86_64"))
    qemu_args = shlex.split(qemu_line)
    mount_args = [
        "-drive",
        "file=CD 1.iso,if=none,id=cd0,media=cdrom",
        "-device",
        "ide-cd,drive=cd0,bus=ide.1,unit=0",
        "-cdrom-swap",
        "drive=cd0,file=CD 2.iso",
    ]
    start = qemu_args.index("-drive")
    assert qemu_args[start : start + len(mount_args)] == mount_args


def test_installer_mount_task_with_src_list(tmp_path, cd_images):
    task = {
        "mount": {
            "letter": "{FIRST_CD_DRIVE_LETTER}",
            "src": ["{DEST_DIR}/{FIRST_CD_DRIVE_LETTER}", "{DEST_DIR}/{SECOND_CD_DRIVE_LETTER}"],
        }
    }
    variables = {
        "DEST_DIR": str(tmp_path),
        "FIRST_CD_DRIVE_LETTER": FIRST_CD_DRIVE_LETTER,
        "SECOND_CD_DRIVE_LETTER": SECOND_CD_DRIVE_LETTER,
    }
    qemu = _qemu(tmp_path)
    exec_subtask(subst_vars(task, variables), qemu)

    assert len(qemu.mount_points) == 1
    mp = qemu.mount_points[0]
    assert mp.letter == FIRST_CD_DRIVE_LETTER
    assert mp.media == "cdrom"
    assert mp.image_path == cd_images[0]
    assert mp.swap_images == cd_images[1:]


def test_installer_mount_task_with_src_str(tmp_path, cd_images):
    qemu = _qemu(tmp_path)
    exec_subtask({"mount": {"letter": "E", "src": str(cd_images[0])}}, qemu)
    assert qemu.mount_points[0].image_path == cd_images[0]
    assert qemu.mount_points[0].swap_images == []


def test_run_qemu_passes_cdrom_swap(tmp_path, cd_images, monkeypatch):
    calls = []
    monkeypatch.setattr("lib.qemu.qemu.run_cmd", lambda cmd, **_: calls.append(cmd))
    qemu = _qemu(tmp_path)
    qemu.mount(image_path=cd_images, media="cdrom", letter=FIRST_CD_DRIVE_LETTER)
    qemu._run_qemu()

    (cmd,) = calls
    assert "file=E,if=none,id=cd0,media=cdrom" in cmd
    assert cmd[cmd.index("-cdrom-swap") + 1] == "drive=cd0,file=F"
