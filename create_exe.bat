pyinstaller --onefile ^
--distpath . ^
--log-level WARN ^
--icon .\icon\icon.ico ^
--noconfirm ^
--add-data=.\icon\icon.ico;. ^
--add-data=.\.env;. ^
--runtime-hook=.\additional_runtime_hooks_lawchecker\hook-lawchecker.py ^
--name LawChecker ^
.\src\lawchecker\gui.py
