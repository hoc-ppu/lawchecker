# added-names

To install saxon first try
```shell
pip install saxonche
```
If that doesn't work try following the [instructions](https://www.saxonica.com/saxon-c/documentation12/index.html#!starting/installingpython) to install python-saxon.

TODO: Add instructions to create the .exe with the new saxonche

Below are the old instructions for saxonc 11

To create the .exe
```shell
pyinstaller --onefile --workpath .\pyinBuild --log-level WARN --add-binary '.\saxonstuff;.\saxonstuff' --dist ..  --paths '.\pythonsaxon' --noconfirm  .\run_xslts.py
```