import subprocess
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

params = {
    "dosbox_prefix": "./C",
    "img_drive_letter": "D",
    "runexit_exec": "C:\\UTILS\\RUNEXEC.EXE",
    "app_image": "./1_en.iso",
    "app_exec": "C:\\NINE\\NINE_31.EXE",
    "dosbox_conf": "./C/dosbox.conf",
}

# template(CURRENT_DIR / "lib" / "dosbox" / "templates" / "run_win3x.sh.tmpl", Path("./run.sh"), params=params)
subprocess.run(
    "cp --reflink=auto -r /ara/incoming/aaa/SYSTEM/* /ara/devel/acme/yag/storage/apps/20/203b54a9236a9fe853750ac6dd890b52",
    shell=True,
)
a = 1
