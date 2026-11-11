# Lawchecker Change Log

## 2.5.0 (unreleased)

### Added
- Duplicate Amendments: a new report (in the GUI) on a single amendment paper. It lists amendments with the same text, amendments that make the same change at different places, and amendments with very similar text
- Check Amendment Papers: "Moved amendments" card, listing the amendments that have moved since the older paper (been re-marshalled), grouped by where they are now, with where each run of them was before
- Check Amendment Papers: "Side-by-side order" card, showing the order of both papers side by side, with a short description of each amendment. Long stretches of unmoved amendments fold away. Hovering over or clicking a moved amendment shows an arrow from where it was to where it is now
- Check Amendment Papers: "Are these the right papers?" warning (in the report and the GUI dialog) when the papers are from different stages or different bills, or when that information is missing from a paper. The introduction table now shows each paper's house and stage
- Check Amendment Papers: "Amendment numbers and dnums" warning when a number is in both papers with different dnums, or a dnum is in both papers with different numbers
- Check Amendment Papers: "Duplicate amendment numbers" warning when a paper uses the same amendment number more than once. The first amendment with that number is the one compared
- Example amendment papers for the English Devolution and Community Empowerment Bill and the Health Bill, with notes in `example_files/examples.md`

### Fixed
- Star check: standing amendments with no star in the older paper but a star in the newer one were not checked
- Errors while creating the Compare Bills, Check Amendment Papers and Duplicate Amendments reports from the GUI are now shown in the feedback dialog
- Clicking the "Days between papers" label in the GUI now ticks the box
- A JavaScript error in the amendment reports, from a button that is only in the Compare Bills report
- Web amendments: requests to the Bills API are now retried after any HTTP error, not only timeouts and network errors

### Changed
- The GUI (pywebview) is now an optional extra. Install with `pip install ".[gui]"` or `uv sync --extra gui`. Reinstalling with pip or pipx without `[gui]` installs only the command line tools
- Check Amendment Papers: the "Added and removed names" card starts closed
- Amendment paper classes (`SupDocument`, `Amendment`) moved to `amendment_document.py`, shared by the Check Amendment Papers and Duplicate Amendments reports
- Tests rebuilt around small papers made in code (`tests/paper_builder.py`), with checks against the example papers
- Removed `pp_xml_lxml.py`

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
