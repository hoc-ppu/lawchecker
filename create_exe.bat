pyinstaller --onefile ^
--log-level WARN ^
--icon .\icon\icon.ico ^
--noconfirm ^
--add-data=.\icon\icon.ico;. ^
--name LawChecker ^
.\src\lawchecker\gui.py
