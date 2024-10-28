import tempfile
from pathlib import Path

from lib.unpack.disc_image import unpack

CURRENT_DIR = Path(__file__).resolve().parent
ISO_IMAGE_PATH = CURRENT_DIR / "data" / "fdbootcd.iso"
ISO_IMAGE_FILES = ["[BOOT]", "boot.catalog", "fdos2040.img"]
BIN_IMAGE_PATH = CURRENT_DIR / "data" / "fdbootcd.bin"
BIN_IMAGE_FILES = ISO_IMAGE_FILES


def test_extract_iso_all_files():
    assert ISO_IMAGE_PATH.exists()
    with tempfile.TemporaryDirectory() as dest:
        dest_path = Path(dest)
        unpack(ISO_IMAGE_PATH, dest_path)
        for f in ISO_IMAGE_FILES:
            assert (dest_path / f).exists()
    with tempfile.TemporaryDirectory() as dest:
        dest_path = Path(dest)
        unpack(ISO_IMAGE_PATH, dest_path, extract_files=ISO_IMAGE_FILES)
        for f in ISO_IMAGE_FILES:
            assert (dest_path / f).exists()


def test_extract_iso_custom_files():
    assert ISO_IMAGE_PATH.exists()
    with tempfile.TemporaryDirectory() as dest:
        dest_path = Path(dest)
        unpack(ISO_IMAGE_PATH, dest_path, extract_files=ISO_IMAGE_FILES[:2])
        assert (dest_path / ISO_IMAGE_FILES[0]).exists()
        assert (dest_path / ISO_IMAGE_FILES[1]).exists()
        assert not (dest_path / ISO_IMAGE_FILES[2]).exists()


def test_extract_bin_image():
    assert BIN_IMAGE_PATH.exists()
    with tempfile.TemporaryDirectory() as dest:
        dest_path = Path(dest)
        unpack(BIN_IMAGE_PATH, dest_path)
        for f in BIN_IMAGE_FILES:
            assert (dest_path / f).exists()

    with tempfile.TemporaryDirectory() as dest:
        dest_path = Path(dest)
        unpack(BIN_IMAGE_PATH, dest_path, extract_files=BIN_IMAGE_FILES)
        for f in BIN_IMAGE_FILES:
            assert (dest_path / f).exists()
