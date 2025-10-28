# Lawchecker Change Log

## 2.2.0 (2025-10-28)

- New: Enhances web amendment checking by adding dnum support and improving error handling
- Updates dependencies and build scripts
- Fixes UI bugs and improves user feedback in the GUI
- Adds web amendments examples to examples.md
- Removes the defunct `create_exe.bat` file.
- Updates the README file to include instructions for building the application into standalone executables (.exe or .app files) using `npm run build`.
- The templates are added to the python package

## 2.1.0 (2025-03-19)

- New: Added the ability to check the web amendments on bills.parliament.uk against amendments in an amendment paper or a proceedings paper. This works by downloading all the web amendments from the bills API.
- Fix: Issue with the bill numbering table being out of order
- Fix: bug with fedback dialogue spinner disappearing when a warning or error message is shown.
