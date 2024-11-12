import importlib
import os
from pathlib import Path

import click
import yaml

from lib.app_desc import AppDesc
from lib.installer.parser import Parser

PORTS_ROOT_PATH = Path(os.getenv("PORTS_ROOT_PATH"))


@click.group()
def cli():
    pass


@cli.command()
@click.argument("app", required=True)
@click.option("--release", required=True)
def install(app: str, release: str):
    print(os.environ)
    category, app_slug = app.split("/")
    with open(PORTS_ROOT_PATH / "games" / app_slug / f"{release}.yaml", encoding="UTF-8") as f:
        raw_yaml = yaml.safe_load(f)
        app_descr = AppDesc.from_dict(raw_yaml["descr"], app_slug, release)
        installer: dict = raw_yaml["installer"]
    if installer:
        p = Parser()
        p.run(app_descr, installer)
    else:
        m = f"ports.{category}.{app_slug}.install"
        importlib.import_module(m).Main(app_descr)
    return 0


if __name__ == "__main__":
    cli()
