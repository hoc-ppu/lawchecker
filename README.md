# SupCheck

Automated test for House of Commons amendment paper. AKA, Supplement, Sup.

You can create:
- an HTML added names report
- an HTML report which compared two Amendment paper XML files

## Python script installation
Clone the repository if you have not already done so. [Here is a guide to cloning](https://www.youtube.com/watch?v=CKcqniGu3tA).
This project uses submodules so when cloning use, `--recurse-submodules`. Alternatively run `submodule update --init`.
If you do not have git installed you could download and extract the zip file. You may also need to download the submodule.
Install a recent version of [Python](https://www.python.org/downloads/) if you have not got one.

### *Optionally* create and activate a python virtual environment.
To create a virtual environment run the following in PowerShell on Windows or in the terminal on Unix (Mac or Linux).

<details>
<summary>On Windows</summary>

Create:
```bash
python -m venv sdenv
```

To activate on Windows, run:
```powershell
sdenv\Scripts\Activate.ps1
```

If you run into permission trouble, [this article](https://dev.to/aka_anoop/enabling-virtualenv-in-windows-powershell-ka3) may help.
</details>

<details>
<summary>On Unix</summary>

Create:
```bash
python3 -m venv sdenv
```

To activate on Unix, run:
```bash
source sdenv/bin/activate
```
</details>

### Install the package (Required)
```bash
pip install .
```

Or if you intend to change the code
```bash
pip install -e .[dev]
```

If that doesn't work because of saxon try following the [instructions](https://www.saxonica.com/saxon-c/documentation12/index.html#!starting/installingpython) to install python-saxon.

## Usage
There are three entry points.
 - `an_report` creates an added names report. Type `an_report --help` in your terminal or comand prompt for help on how to use this.
 - `compare` creates a report detailing the differences between two Amendment paper XML files. Type `compare --help` in your terminal or comand prompt for help on how to use this.
 - `startgui` will start a graphical user interface with lets you create both of the above reports.



## Tests
To run tests `pytest tests/`

TODO: Add instructions to create the .exe with the new saxonche

Below are the old instructions for saxonc 11

To create the .exe
```shell
pyinstaller --onefile --workpath .\pyinBuild --log-level WARN --add-binary '.\saxonstuff;.\saxonstuff' --dist ..  --paths '.\pythonsaxon' --noconfirm  .\run_xslts.py
```
