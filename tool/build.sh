# Parse command-line arguments using getopts
filename="MessageSyncer"
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --filename)
            filename="$2"
            shift 2
            ;;
        *)
    esac
done

# Check if there is a tag exactly matching the current commit
version=$(git describe --tags --exact-match 2>/dev/null)

# If no matching tag is found, fall back to the short commit hash
if [ -z "$version" ]; then
    version=$(git rev-parse --short HEAD)
fi

pip_MEIPASS_Path='_pip_meipath'
timestamp=$(date +%s)

# Update the runtimeinfo.py file with the version information
echo "VERSION = '$version'
PIPMEIPASSPATH = '$pip_MEIPASS_Path'
BUILDTIME = $timestamp
" > ./src/runtimeinfo.py

# Compile the script into a single executable using pyinstaller
source .venv/bin/activate
pip install pyinstaller
python tool/build.py $filename "--add-data=.venv/bin/pip:$pip_MEIPASS_Path"
