import fnmatch
import re
import tempfile
from pathlib import Path

import guestfs


def rm(image_path: Path, guest_path: str):
    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive(str(image_path))
    g.launch()
    partitions = g.list_partitions()
    g.mount(partitions[0], "/")
    g.rm_rf(str(guest_path))
    g.sync()
    g.umount_all()
    g.close()


def replace_string_in_file(image_path: Path, guest_path: str, old, new):
    """
    Replace a string in a file inside a guest filesystem using libguestfs.

    :param image_path: Path to the disk image file on the host.
    :param guest_path: Path to the file inside the guest (Linux-style, e.g., "/WINDOWS/SYSTEM.INI").
    :param old: The string to be replaced.
    :param new: The replacement string.
    """

    g = guestfs.GuestFS(python_return_dict=True)
    g.add_drive(str(image_path))
    g.launch()
    partitions = g.list_partitions()
    g.mount(partitions[0], "/")
    content = g.read_file(guest_path).decode("cp1252")
    updated = re.sub(old, new, content)
    g.write(guest_path, updated.encode("cp1252"))
    g.sync()
    g.umount_all()
    g.close()


def copy(src_img_path: Path | None, src_file_path: Path, dst_img_path: Path | None, dst_file_path: Path | None = None):
    """
    Copy files between host and virtual disk images using guestfs.

    Parameters:
    - src_img_path: None if source is host, else path to guest image
    - src_file_path: path inside host or guest (supports wildcards)
    - dst_img_path: None if destination is host, else path to guest image
    - dst_file_path: optional path inside destination (guest or host)

    Preserves directory structure. Supports Windows paths in guest images.
    """

    print(f"guestfs: copying [{src_img_path}, {src_file_path}] into [{dst_img_path}, {dst_file_path}]")

    def to_guestfs_path(p: Path) -> str:
        # Convert Windows path to guestfs path (/...)
        p_str = str(p).replace("\\", "/")
        p_str = re.sub(r"^[A-Za-z]:", "", p_str)
        if not p_str.startswith("/"):
            p_str = "/" + p_str
        return p_str

    # Host -> Guest
    if src_img_path is None and dst_img_path is not None:
        g_dst = guestfs.GuestFS(python_return_dict=True)
        g_dst.add_drive(str(dst_img_path))
        g_dst.launch()
        partitions_dst = g_dst.list_partitions()
        if not partitions_dst:
            raise RuntimeError(f"No partitions found in {dst_img_path}")
        g_dst.mount(partitions_dst[0], "/")

        src_files = list(src_file_path.parent.glob(src_file_path.name))
        for f in src_files:
            rel_path = f.relative_to(src_file_path.parent)
            dst_base = Path(to_guestfs_path(dst_file_path)) if dst_file_path else Path(f.parent.name)
            dst_path = dst_base / rel_path
            if f.is_dir():
                for sub in f.rglob("*"):
                    rel_sub = sub.relative_to(f)
                    dst_sub_path = dst_base / rel_path / rel_sub
                    g_dst.mkdir_p(str(dst_sub_path.parent))
                    if sub.is_file():
                        g_dst.write(str(dst_sub_path), sub.read_bytes())
            else:
                g_dst.mkdir_p(str(dst_path.parent))
                g_dst.write(str(dst_path), f.read_bytes())
        g_dst.sync()
        g_dst.umount_all()
        g_dst.close()
        return

    # Guest -> Host
    if src_img_path is not None and dst_img_path is None:
        g_src = guestfs.GuestFS()
        g_src.add_drive_ro(str(src_img_path))
        g_src.launch()
        partitions_src = g_src.list_partitions()
        if not partitions_src:
            # check if it's an iso image
            filesystems_src = g_src.list_filesystems()
            if filesystems_src and filesystems_src[0][1] in {"iso9660", "udf"}:
                # important: even DVDs (udf) we should mount as CDs (iso) to avoid guestfs ufs driver issues,
                # e.g. for LIGHTBRINGER.ISO it hangs in infinite loop with error on ls() and find() commands
                g_src.mount_vfs("ro", "iso9660", filesystems_src[0][0], "/")
            else:
                raise RuntimeError(f"No devices/partitions found in {src_img_path}")
        else:
            g_src.mount(partitions_src[0], "/")
        # new code
        all_matches = []
        src_file_path = to_guestfs_path(src_file_path)
        if g_src.is_file(src_file_path):
            all_matches = [src_file_path]
        elif g_src.is_dir(src_file_path):
            all_matches = g_src.find(src_file_path)
            all_matches = [
                src_file_path + f for f in all_matches
            ]  # note: find returns files without "/" prefix for root path search, for the rest it comes with "/"
        else:  # glob pattern "*"
            all_files = g_src.find("/")
            all_files = ["/" + f for f in all_files]  # because find returns files without prefix for "/" search
            all_matches = [f for f in all_files if fnmatch.fnmatch(f, src_file_path)]
        for f in all_matches:
            if "*" in src_file_path:
                base = Path(src_file_path).parent
                target_file_path = dst_file_path
            elif g_src.is_file(src_file_path):
                base = Path(src_file_path).parent
                target_file_path = dst_file_path
            else:  # directory copy
                base = Path(src_file_path)
                target_file_path = dst_file_path / base.name
            rel_path = Path(f).relative_to(base)
            # destination path on host
            target = target_file_path / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if g_src.is_file(f):
                # Copy file contents
                with open(target, "wb") as out:
                    out.write(g_src.read_file(f))

        g_src.umount_all()
        g_src.close()
        return

    # Guest -> Guest
    if src_img_path is not None and dst_img_path is not None:
        # Copy to host first, then from host to dst image
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            copy(src_img_path, src_file_path, None, tmpdir_path)
            copy(None, tmpdir_path / Path(src_file_path.name), dst_img_path, dst_file_path)
        return

    raise ValueError("Invalid combination: both src_img_path and dst_img_path cannot be None")
