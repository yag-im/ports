import os
import subprocess
from pathlib import Path

import yaml

PORTS_ROOT_PATH = Path(os.environ.get("PORTS_ROOT_PATH"))


def post_releases(ports_dir: Path) -> list[dict]:
    target_dir = ports_dir / "games"
    for path_yaml_file in target_dir.rglob("*.yaml"):
        print(f"posting: {path_yaml_file}")
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
                f"http://portsvc.yag.dc:8087/ports/apps/{release_name}/releases/{release_uuid}",
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


post_releases(PORTS_ROOT_PATH)
