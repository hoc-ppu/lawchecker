# Make papers index
Create the papers index for the House of Commons Journal. A python script can output XML (that can be typeset in InDesign) either from an existing input raw XML file or via querying the [papers laid API](http://services.paperslaid.parliament.uk/).


## Before you start
You will need to have [Python](https://www.python.org/downloads/) installed and working on your computer.

You should also clone this repository. [Here is a guide to cloning](https://www.youtube.com/watch?v=CKcqniGu3tA). Or if you do not have git installed you could download and extract the zip file.

## Python script installation
### *Optionally* create and activate a python virtual environment.
To create a virtual environment run the following in PowerShell on Windows or in the terminal on Unix (Mac or Linux).

<details>
<summary>On Windows</summary>

Create:
```bash
python -m venv venv
```

To activate on Windows, run:
```powershell
venv\Scripts\Activate.ps1
```

If you run into permission trouble, [this article](https://dev.to/aka_anoop/enabling-virtualenv-in-windows-powershell-ka3) may help.
</details>

<details>
<summary>On Unix</summary>

Create:
```bash
python3 -m venv venv
```

To activate on Unix, run:
```bash
source venv/bin/activate
```
</details>

### Install the package (Required)
```bash
pip install .
```

Or, if you intend to change the code, install in editable mode:
```bash
pip install -e .[dev]
```

## Usage
Once installed you can use the `compare_bills`. By default this will find XML files in the current folder, then create and save CSV file(s) with teh numbering of sections and schedule paragraphs listed. By default the CSV file(s) are saved in the current folder.

For options/further help run:
```bash
compare_bills --help
```





