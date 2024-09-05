git update-index --assume-unchanged src/test.py
python -m venv .venv
source .venv/bin/activate
cd src
pip install -r requirements.txt
