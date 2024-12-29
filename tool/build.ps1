# Parse command-line arguments using getopts
param (
    [string]$FileName
)
if (-not $FileName) {
    $FileName = "MessageSyncer.exe"
}

# Check if there is a tag exactly matching the current commit
$version = git describe --tags --exact-match 2>$null

# If no matching tag is found, fall back to the short commit hash
if (-not $version) {
    $version = git rev-parse --short HEAD
}

$pipMEIPASSPath = '_pip_meipath'
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))

# Update the runtimeinfo.py file with the version information
$content = @"
VERSION = '$version'
PIPMEIPASSPATH = '$pipMEIPASSPath'
BUILDTIME = $timestamp
"@
Set-Content -Path ".\src\runtimeinfo.py" -Value $content

# Compile the script into a single executable using pyinstaller
& .\.venv\Scripts\Activate.ps1
pip install pyinstaller
python tool\build.py $FileName "--add-data=.venv/Scripts/pip.exe:${pipMEIPASSPath}"
