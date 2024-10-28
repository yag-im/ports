import os
import typing as t
from dataclasses import dataclass
from pathlib import Path

APPS_BUNDLE_DIR = os.getenv("APPS_BUNDLE_DIR")
APPS_SRC_DIR = os.getenv("APPS_SRC_DIR")


@dataclass
class AppDesc:
    @dataclass
    class AppReqs:
        @dataclass
        class UaReqs:
            lock_pointer: bool

        color_bits: int
        midi: bool
        screen_height: int
        screen_width: int
        ua: UaReqs

    @dataclass
    class Distro:
        files: list[str]
        format: str
        patches: t.Optional[list[str]]
        url: str

    app_slug: str
    app_reqs: AppReqs
    distro: Distro
    lang: str
    platform: str
    release_uuid: str
    year_released: int

    def src_path(self):
        return Path(APPS_SRC_DIR) / self.app_slug / self.release_uuid

    def dst_path(self):
        return Path(APPS_BUNDLE_DIR) / self.app_slug / self.release_uuid

    @classmethod
    def from_dict(cls, app_descr: dict, app_slug: str, release_uuid: str):
        return cls(
            app_reqs=AppDesc.AppReqs(
                color_bits=app_descr["reqs"]["color_bits"] if "color_bits" in app_descr["reqs"] else None,
                midi=app_descr["reqs"]["midi"] if "midi" in app_descr["reqs"] else None,
                screen_height=app_descr["reqs"]["screen_height"],
                screen_width=app_descr["reqs"]["screen_width"],
                ua=AppDesc.AppReqs.UaReqs(lock_pointer=app_descr["reqs"]["ua"]["lock_pointer"]),
            ),
            app_slug=app_slug,
            distro=AppDesc.Distro(
                format=app_descr["distro"]["format"],
                url=app_descr["distro"]["url"],
                files=app_descr["distro"]["files"],
                patches=app_descr["distro"].get("patches", None),
            ),
            lang=app_descr["lang"],
            platform=app_descr["platform"],
            release_uuid=release_uuid,
            year_released=app_descr["year_released"],
        )
