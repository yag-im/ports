import stat
import subprocess
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

    @staticmethod
    def rip_cd_audio(bin_file_path, cue_file_path, output_dir, track="track"):
        """
        Extracts CD audio tracks from BIN/CUE files using bchunk and converts them to FLAC.

        Args:
            bin_file_path (Path): Absolute path to the .bin file
            cue_file_path (Path): Absolute path to the .cue file
            output_dir (Path): Output directory
        """

        # Run bchunk to extract WAV tracks
        bchunk_cmd = ["bchunk", "-w", str(bin_file_path), str(cue_file_path), track]
        subprocess.run(bchunk_cmd, cwd=str(output_dir), check=True)

        # Convert all track*.wav files to FLAC
        wav_files = output_dir.glob(f"{track}*.wav")
        for wav_file in wav_files:
            flac_cmd = ["flac", "-f", str(wav_file)]
            subprocess.run(flac_cmd, check=True)
            wav_file.unlink()

        for f in sorted(output_dir.glob(f"{track}*.flac")):
            n = int(f.stem[len(track) :]) - 1
            f.rename(f.with_name(f"{track}{n:02}.flac"))

        # cleanup: remove iso track
        for iso_file in output_dir.glob(f"{track}*.iso"):
            iso_file.unlink()
