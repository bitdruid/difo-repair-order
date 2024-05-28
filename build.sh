#!bin/bash

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pip install python-magic==0.4.25

pyinstaller --onefile --add-data="assets:assets" --icon="assets/icon.ico" --name="DifoRepairOrder" diforepairorder.py

echo ""
echo "Executable should be in dist/diforepairorder"
echo ""
