import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pkg_resources

import image
import log
import runtime

dep_path = Path("data") / "dep"
dep_path.mkdir(parents=True, exist_ok=True)
sys.path.append(str(dep_path.absolute()))
pkg_resources.working_set.add_entry(str(dep_path.absolute()))


def try_install_requirementstxt(requirements_file: Path):
    if not requirements_file.exists():
        # log.warning(f'Failed to install {requirements_file}: file not exists')
        return

    for requirement_str in requirements_file.read_text("utf-8").split("\n"):
        requirement_str = requirement_str.strip()

        try:
            version = importlib.metadata.version(requirement_str)
            installed = True
            log.debug(f"Check requirement: {requirement_str}: exists, {version}")
        except Exception as e:
            log.debug(f"Check requirement: {requirement_str}: {e}")
            installed = False

        if not installed:
            try:
                log.debug(f"Trying to install {requirement_str}")
                subprocess.check_call(
                    [
                        runtime.pip,
                        "install",
                        requirement_str,
                        "--target",
                        str(dep_path.absolute()),
                    ]
                )
                log.debug(f"Successfully installed {requirement_str}")
            except Exception as e:
                log.warning(f"Failed to install {requirement_str}: {e}")


def from_package_import_attr(pkg: str, path: Path, attr: str, force_reload=False):
    if str(path.parent.absolute()) not in sys.path:
        sys.path.append(str(path.parent.absolute()))

    if force_reload:
        try:
            sys.modules.pop(pkg)
        except:
            pass

    if not (path / "__init__.py").exists():
        raise Exception(f"Failed to import package {pkg}: not a vaild package")
    if pkg not in sys.modules:
        try_install_requirementstxt(path / "requirements.txt")

    attr_obj = getattr(importlib.import_module(pkg), attr)
    try:
        setattr(attr_obj, "_import_path", path)
        setattr(attr_obj, "_import_pkg", pkg)
    except:
        pass

    return attr_obj
