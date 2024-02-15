pyinstaller --onefile ^
--log-level WARN ^
--icon .\icon\icon.ico ^
--noconfirm ^
--add-data=.\icon\icon.ico;. ^
--name Lawchecker ^
.\src\supcheck\supcheck_gui.py