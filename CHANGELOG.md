# Lawchecker Change Log

## 2.4.0 (2026-02-24)

### Added
- `ReportMetadata` context model for web amendments reporting flow
- XML decision-state property in web amendments processing

### Improved
- API querying architecture with synchronous wrappers around async internals
- Newline normalization in generated table cell content to reduce false positives in XML/Web amendment diffing
- Filename handling for generated reports
- User feedback showing where reports are saved

### Fixed
- Newline handling around semicolon-delimited content
- Unnecessary amendment JSON save step in web amendments pipeline

### Changed
- Migrated HTTP layer from `requests` to `httpx` with async support
- Refactored logging usage across Python report/checking modules

## 2.3.0 (2025-11-10)

### Added
- JSON summary output for web amendments checking
- Template files now properly included in Python package for distribution via pipx

### Improved
- Sponsor matching and reporting accuracy in web amendments
- Web amendments CLI with better error handling and user feedback
- Template path resolution for various installation methods

### Fixed
- False positive with quote character normalization
- Template files not accessible when installing via pipx

### Changed
- Updated pywebview dependency for better stability
- Improved error messages and validation
- Relocated templates to be inside the Python package structure

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
