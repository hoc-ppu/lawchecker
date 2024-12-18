pyinstaller --onefile ^
--distpath . ^
--log-level WARN ^
--icon .\icon\icon.ico ^
--noconfirm ^
--add-data=.\icon\icon.ico;. ^
--add-data=.\.env;. ^
--add-data=.\ui_bundle\index.html;ui\ ^
--add-data=.\pyproject.toml;. ^
--runtime-hook=.\additional_runtime_hooks_lawchecker\hook-lawchecker.py ^
--name LawChecker ^
.\src\lawchecker\main.py
