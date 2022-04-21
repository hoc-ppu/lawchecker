# added-names

Follow the [instructions](https://www.saxonica.com/saxon-c/documentation11/index.html#!starting/installingpython) to install python-saxon.

To create the .exe
```shell
pyinstaller --onefile --workpath .\pyinBuild --log-level WARN --add-binary '.\saxonstuff;.\saxonstuff' --dist ..  --paths '.\pythonsaxon' --noconfirm  .\run_xslts.py
```