import hashlib
import os
import pkgutil
import re
import subprocess
import sys
import sysconfig
from datetime import datetime

import git


def read_requirements(file_path):
    """Read the requirements.txt file and return a list of package names."""
    with open(file_path, "r") as file:
        requirements = []
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                package_name = re.split(r"[<>=]", line)[0].strip()
                requirements.append(package_name)
    return requirements


def generate_sha256_checksum(file_path, output_path):
    """Generate a SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    with open(output_path, "w") as f:
        f.write(f"{sha256_hash.hexdigest()}")


def build_executable(filename, extra_args):
    """Build the executable using PyInstaller."""
    std_imports = [
        module.name for module in pkgutil.iter_modules([sysconfig.get_path("stdlib")])
    ]
    req_imports = read_requirements("requirements.txt")
    hidden_imports_cmd = [f"--hidden-import={pkg}" for pkg in std_imports + req_imports]
    hidden_imports_cmd += [f"--copy-metadata={pkg}" for pkg in req_imports]

    command = (
        [
            "pyinstaller",
            "--onefile",
            f"--name={filename}",
            "./src/MessageSyncer.py",
        ]
        + extra_args
        + hidden_imports_cmd
    )
    print("Running command:", " ".join(command))
    subprocess.run(command, check=True)

    executable_path = os.path.join("dist", filename)
    if os.path.exists(executable_path):
        sha256_file_path = f"{executable_path}.sha256"
        generate_sha256_checksum(executable_path, sha256_file_path)


def get_version():
    """Get the version from Git tags or commit hash."""
    repo = git.Repo(search_parent_directories=True)
    try:
        version = repo.git.describe(tags=True, exact_match=True)
    except git.GitCommandError:
        version = repo.git.rev_parse("--short", "HEAD")
    return version


def create_runtime_info(version, pip_meipass_path, timestamp):
    """Generate the runtimeinfo.py file."""
    content = f"""
VERSION = '{version}'
PIPMEIPASSPATH = '{pip_meipass_path}'
BUILDTIME = {timestamp}
"""
    with open("./src/runtimeinfo.py", "w") as f:
        f.write(content)


def main():
    # Parse arguments
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        if os.name == "nt":
            filename = "MessageSyncer.exe"
        else:
            filename = "MessageSyncer"

    pip_meipass_path = "_pip_meipath"
    timestamp = int(datetime.now().timestamp())
    if os.name == "nt":
        extra_args = [f"--add-data=.venv/Scripts/pip.exe:{pip_meipass_path}"]
    else:
        extra_args = [f"--add-data=.venv/bin/pip:{pip_meipass_path}"]

    # Get version from Git
    version = get_version()

    # Create runtimeinfo.py
    create_runtime_info(version, pip_meipass_path, timestamp)

    # Build the executable
    build_executable(filename, extra_args)


if __name__ == "__main__":
    main()
