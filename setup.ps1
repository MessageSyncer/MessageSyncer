git update-index --assume-unchanged src/test.py
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
Set-Location src
pip install -r requirements.txt
