import stat
from pathlib import Path

from lib.utils import (
    copy,
    template,
)

CURRENT_DIR = Path(__file__).resolve().parent


class ScummVm:
    def __init__(self, root_dir, game: str, lang: str = "en", app_dir: Path = None) -> None:
        if not app_dir:
            app_dir = root_dir / "app"
        assert app_dir.exists()
        self.root_dir = root_dir
        self.app_dir = app_dir
        self.game = game
        self.lang = lang
        copy(CURRENT_DIR / "files" / "scummvm.ini", root_dir)

    def gen_run_script(self) -> Path:
        tmpl_params = {
            "config": (self.root_dir / "scummvm.ini").relative_to(self.root_dir),
            "game": self.game,
            "path": "./" + str((self.app_dir).relative_to(self.root_dir)),
            "save_path": "./" + str((self.app_dir).relative_to(self.root_dir)),
            "lang": self.lang,
        }
        output_path = self.root_dir / "run.sh"
        template(CURRENT_DIR / "templates" / "run.sh.tmpl", output_path, params=tmpl_params)
        output_path.chmod(output_path.stat().st_mode | stat.S_IEXEC)
        return output_path
