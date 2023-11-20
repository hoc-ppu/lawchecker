# Compare bill numbering
A python script that compares the numbering of sections and schedule paragraphs in two or more versions of a bill. The output is CSV file(s) which indicate when sections or schedule paragraphs are insearted or removed. You can can also process several different bills at once, e.g. bill A (with 3 versions) and bill B (with 2 versions).


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

If you run into **permission trouble**, [this article](https://dev.to/aka_anoop/enabling-virtualenv-in-windows-powershell-ka3) may help.
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
Once installed you can use the `compare_bills` command line tool. By default this will find XML files in the current folder, then create and save CSV file(s) with the numbering of sections and schedule paragraphs listed. By default the CSV file(s) are saved in the current folder.

For options/further help run:
```bash
compare_bills --help
```

### Example

First check that you have cloned the repo and have the `example_files` populated, with two `Data Protection...xml` files and four `Social Housing...xml` files. Then run the following command.

```bash
compare_bills --input-folder example_files
```

You should see two CSV files have been created: `data_protection_and_digital_information_no_2.csv` & `social_housing_regulation.csv`.
You should notice that items are added and removed and that items are renumbered as a result. For example, in the `social_housing_regulation.csv` file you should see (amongst other changes) that the section (a.k.a. clause) '*Standards relating to energy demand*' [guid: _6b3c4b1c-9203-4a45-bdfa-c31570fc8636] was added in the Lords report stage and removed again at the commons committee stage.


