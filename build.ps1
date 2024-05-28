python -m venv .venv
.venv\Scripts\activate.ps1
pip install -r requirements.txt

pip install python-magic-bin==0.4.14

pyinstaller --onefile --add-data="assets:assets" --icon="assets/icon.ico" --name="DifoRepairOrder" diforepairorder.py

Write-Host ""
Write-Host "Executable should be in dist\diforepairorder.exe"
Write-Host ""
