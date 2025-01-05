param (
    [switch]$NoDev
)

python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

if (-not $NoDev) {
    git update-index --assume-unchanged src/test.py
    pre-commit install
}
