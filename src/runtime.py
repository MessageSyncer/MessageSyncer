import sys
from pathlib import Path

run_in_frozen_mode: bool
version: str
build_time: int
pip: str


def is_frozen():
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


run_in_frozen_mode = is_frozen()
if run_in_frozen_mode:
    import runtimeinfo

    version = runtimeinfo.VERSION
    build_time = runtimeinfo.BUILDTIME

    pip_alias = ["pip", "pip.exe"]
    for pip_name in pip_alias:
        _pip_path = Path(sys._MEIPASS) / runtimeinfo.PIPMEIPASSPATH / pip_name
        if _pip_path.exists():
            pip = str(_pip_path)
else:
    version = ""
    build_time = 0
    pip = "pip"
