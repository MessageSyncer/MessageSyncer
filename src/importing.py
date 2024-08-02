import importlib
import sys
import subprocess
import logging
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ObjectImportingDetail:
    obj: object
    module: 'importlib.ModuleType'
    path: Path

    def reload(self):
        if not self.path.is_file():
            try_install_requirements(self.path)
        export_all_from_module(importlib.reload(self.module), self.path, do_cover=True)


details: dict[str, ObjectImportingDetail] = {}


def try_install_requirements(path: Path):
    # Check if requirements.txt exists
    requirements_file = path / 'requirements.txt'
    if not requirements_file.exists():
        return

    # Use subprocess to call pip to install dependencies
    try:
        subprocess.check_call(['pip', 'install', '-r', str(requirements_file)])
    except subprocess.CalledProcessError as e:
        logging.warning(f"Installation for requirements.txt failed: {e}")


def export_all_from_module(module, module_path, do_cover=False):
    global details

    for attr in dir(module):
        if (not attr in details or do_cover) and not attr.startswith('_'):
            details[attr] = ObjectImportingDetail(getattr(module, attr), module, module_path)


def import_all(paths):
    for path in paths:
        if not path.exists():
            raise ValueError(f"The path {path} does not exist.")

        path = path.resolve()
        sys.path.append(str(path))

        for item in path.glob('*'):
            if item.is_dir() and (item / '__init__.py').exists():
                # Import everything in the package
                try:
                    try_install_requirements(item)
                    module_name = item.relative_to(path.parent).as_posix().replace('/', '.')
                    module = importlib.import_module(module_name)
                    export_all_from_module(module, item)
                except Exception as e:
                    pass
            elif item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
                # Import everything from a single Python file
                try:
                    module_name = item.relative_to(path.parent).with_suffix('').as_posix().replace('/', '.')
                    module = importlib.import_module(module_name)
                    export_all_from_module(module, item)
                except Exception as e:
                    pass