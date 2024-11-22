import stat
from dataclasses import dataclass
from pathlib import Path

from lib.utils import template

CURRENT_DIR = Path(__file__).resolve().parent


@dataclass
class ScummVmConf:
    filtering: bool = True
    fullscreen: bool = True
    subtitles: bool = True


class ScummVm:
    def __init__(self, root_dir: Path, conf: ScummVmConf) -> None:
        self.root_dir = root_dir
        tmpl_params = {
            "filtering": str(conf.filtering).lower(),
            "fullscreen": str(conf.fullscreen).lower(),
            "subtitles": str(conf.subtitles).lower(),
        }
        template(CURRENT_DIR / "templates" / "scummvm.ini.tmpl", self.root_dir / "scummvm.ini", params=tmpl_params)

    def gen_run_script(self, game: str, lang: str = "en", app_dir: Path = None) -> Path:
        if not app_dir:
            app_dir = self.root_dir / "APP"
        if not app_dir.exists():
            raise ValueError(f"no app_dir found: {app_dir}")
        tmpl_params = {
            "config": (self.root_dir / "scummvm.ini").relative_to(self.root_dir),
            "game": game,
            "path": "./" + str((app_dir).relative_to(self.root_dir)),
            "save_path": "./" + str((app_dir).relative_to(self.root_dir)),
            "lang": lang,
        }
        output_path = self.root_dir / "run.sh"
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path
