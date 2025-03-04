import os
import subprocess
from pathlib import Path

import yaml

PORTS_ROOT_PATH = Path(os.environ.get("PORTS_ROOT_PATH"))

BASTION_HOST = os.environ.get("BASTION_HOST", None)
BASTION_USER = os.environ.get("BASTION_USER", None)
LOCAL_TUNNEL_PORT = os.environ.get("LOCAL_TUNNEL_PORT", None)
REMOTE_TUNNEL_PORT = os.environ.get("REMOTE_TUNNEL_PORT", None)

PORTSVC_HOST = os.environ.get("PORTSVC_HOST")
PORTSVC_PORT = os.environ.get("PORTSVC_PORT")


def upsert_remote(path_yaml_file: Path) -> None:
    with open(path_yaml_file, "r") as f:
        content = yaml.safe_load(f)
        release_name = content["descr"]["igdb_slug"]
        release_uuid = content["descr"]["uuid"]

    # establish SSH tunnel
    ssh_proc = subprocess.Popen(
        [
            "ssh",
            "-D",
            str(LOCAL_TUNNEL_PORT),
            "-p",
            str(REMOTE_TUNNEL_PORT),
            "-f",
            "-N",
            f"{BASTION_USER}@{BASTION_HOST}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ssh_proc.wait()
    (stdout, stderr) = ssh_proc.communicate()
    if ssh_proc.returncode != 0:
        print(stderr)
        return

    # perform the curl request through the SSH tunnel
    curl_proc = subprocess.Popen(
        [
            "curl",
            "-v",
            "--request",
            "POST",
            "--socks5-hostname",
            f"0:{LOCAL_TUNNEL_PORT}",
            f"http://{PORTSVC_HOST}:{PORTSVC_PORT}/ports/apps/{release_name}/releases/{release_uuid}",
            "--header",
            "content-type: application/x-yaml",
            "--data-binary",
            f"@{path_yaml_file}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    curl_proc.wait()
    (stdout, stderr) = curl_proc.communicate()
    if curl_proc.returncode != 0:
        print(stderr)
    else:
        print(stdout)

    # close the SSH tunnel
    ssh_close_proc = subprocess.Popen(
        [
            "ssh",
            "-O",
            "exit",
            f"{BASTION_USER}@{BASTION_HOST}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ssh_close_proc.wait()
    (stdout, stderr) = ssh_close_proc.communicate()
    if ssh_close_proc.returncode != 0:
        print(stderr)


def upsert_local(path_yaml_file: Path) -> None:
    with open(path_yaml_file, "r") as f:
        content = yaml.safe_load(f)
        release_name = content["descr"]["igdb_slug"]
        release_uuid = content["descr"]["uuid"]

    proc = subprocess.Popen(
        [
            "curl",
            "--request",
            "POST",
            "--url",
            f"http://{PORTSVC_HOST}:{PORTSVC_PORT}/ports/apps/{release_name}/releases/{release_uuid}",
            "--header",
            "content-type: application/x-yaml",
            "--data-binary",
            f"@{path_yaml_file}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    proc.wait()
    (stdout, stderr) = proc.communicate()
    if proc.returncode != 0:
        print(stderr)
    else:
        print(stdout)


def upsert_release(path_yaml_file: Path) -> None:
    if BASTION_HOST:
        upsert_remote(path_yaml_file)
    else:
        upsert_local(path_yaml_file)


def upsert_releases(ports_dir: Path) -> list[dict]:
    target_dir = ports_dir / "games"
    for path_yaml_file in target_dir.rglob("*.yaml"):
        print(f"upserting release: {path_yaml_file}")
        upsert_release(path_yaml_file)


if __name__ == "__main__":
    upsert_releases(PORTS_ROOT_PATH)
