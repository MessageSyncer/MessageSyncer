import subprocess
import sys
import re
import pkgutil
import hashlib
import os
import sysconfig


def read_requirements(file_path):
    with open(file_path, "r") as file:
        requirements = []
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                package_name = re.split(r"[<>=]", line)[0].strip()
                requirements.append(package_name)
    return requirements


def generate_sha256_checksum(file_path, output_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    with open(output_path, "w") as f:
        f.write(f"{sha256_hash.hexdigest()}")


def build_executable(filename, args):
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
        + args
        + hidden_imports_cmd
    )
    print(command)

    subprocess.run(command, check=True)

    executable_path = os.path.join("dist", filename)
    if os.path.exists(executable_path):
        sha256_file_path = f"{executable_path}.sha256"
        generate_sha256_checksum(executable_path, sha256_file_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename> <args to pyinstaller>")
        sys.exit(1)

    filename = sys.argv[1]
    args = sys.argv[2:]
    build_executable(filename, args)
