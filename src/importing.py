import importlib
import sys
import subprocess
import logging
import pkg_resources
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ObjectImportingDetail:
    attr_name: str
    obj: object
    module: 'importlib.ModuleType'
    module_name: str
    path: Path

    def reload(self) -> bool:
        global details

        if self.path.exists():
            if not self.path.is_file():
                try_install_requirements(self.path)
            export_all_from_module(importlib.reload(self.module), self.module_name, self.path)
            return True
        else:
            details.pop(self.attr_name)
            return False


details: dict[str, ObjectImportingDetail] = {}


def install_package(package_name):
    try:
        logging.debug(f'Installing {package_name}')
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        logging.debug(f'Installing {package_name} succeed')
    except subprocess.CalledProcessError as e:
        logging.debug(f'Installing {package_name} failed: {e}')


def try_install_requirements(path: Path):
    requirements_file = path / 'requirements.txt'

    if not requirements_file.exists():
        return

    with open(requirements_file, 'r') as file:
        requirements = file.readlines()

    logger = logging.getLogger('requirements_checker')

    for requirement in requirements:
        requirement = requirement.strip()
        try:
            pkg_resources.require(requirement)
            logger.debug(f"{requirement} already satisfied")
        except pkg_resources.DistributionNotFound:
            logger.debug(f"{requirement} is not installed")
            install_package(requirement)
        except pkg_resources.VersionConflict as e:
            logger.debug(f"{requirement} has a version conflict: {e.report()}")
            install_package(requirement)


def export_all_from_module(module, module_name, module_path):
    global details
    do_cover = True
    for attr in dir(module):
        if (not attr in details or do_cover) and not attr.startswith('_'):
            details[attr] = ObjectImportingDetail(attr, getattr(module, attr), module, module_name, module_path)
    logging.debug(f'{module_name} loaded from {module_path}')

def import_all(paths):
    for path in paths:
        if not path.exists():
            raise ValueError(f"The path {path} does not exist.")

        path = path.resolve()
        sys.path.append(str(path))

        for item in path.glob('*'):
            if not [i for i in details.values() if i.path == item]:
                if item.is_dir() and (item / '__init__.py').exists():
                    # Import everything in the package
                    try:
                        try_install_requirements(item)
                        module_name = item.relative_to(path.parent).as_posix().replace('/', '.')
                        module = importlib.import_module(module_name)
                        export_all_from_module(module, module_name, item)
                    except Exception as e:
                        pass
                elif item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
                    # Import everything from a single Python file
                    try:
                        module_name = item.relative_to(path.parent).with_suffix('').as_posix().replace('/', '.')
                        module = importlib.import_module(module_name)
                        export_all_from_module(module, module_name, item)
                    except Exception as e:
                        pass
