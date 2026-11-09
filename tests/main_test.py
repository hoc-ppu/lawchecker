"""
Tests for the GUI's report buttons (lawchecker.main.Api) without a GUI.

The progress dialog and the web browser are replaced with fakes, so these
tests only check what happens in Python: that the dialog is open while the
report is built, that a report file is written, and that errors become a
message for the user rather than an exception.
"""

import shutil
from pathlib import Path

import pytest
from lxml import etree, html

from lawchecker import main

EXAMPLES = Path(__file__).resolve().parent.parent / 'example_files' / 'amendments'


class FakeProgressModal:
    """Stands in for ui_feedback.ProgressModal and records what happens."""

    def __init__(self):
        self.is_open = False
        self.messages: list[str] = []

    def __enter__(self):
        self.is_open = True
        return self

    def __exit__(self, *exc_info):
        self.is_open = False

    def update(self, text, log=False, log_level='INFO'):
        self.messages.append(text)


@pytest.fixture
def modal(monkeypatch) -> FakeProgressModal:
    """Replace the progress dialog with a fake, and stop browsers opening."""

    fake = FakeProgressModal()
    monkeypatch.setattr(main, 'ProgressModal', lambda: fake)
    # webbrowser.open returns True when a browser opened
    monkeypatch.setattr(main.webbrowser, 'open', lambda uri: True)
    return fake


@pytest.fixture
def papers(tmp_path) -> tuple[Path, Path]:
    """Copies of two small real papers, so reports are written to tmp_path."""

    old = shutil.copy(EXAMPLES / 'victims_prisoners_rm_rep_0906.xml', tmp_path)
    new = shutil.copy(EXAMPLES / 'victims_prisoners_rm_rep_0908.xml', tmp_path)
    return Path(old), Path(new)


def record_when_built(monkeypatch, name: str, modal: FakeProgressModal) -> list:
    """Wrap main.<name> (a report class) to record if the dialog was open."""

    real_report = getattr(main, name)
    dialog_open_when_built = []

    def wrapped(*args, **kwargs):
        dialog_open_when_built.append(modal.is_open)
        return real_report(*args, **kwargs)

    monkeypatch.setattr(main, name, wrapped)
    return dialog_open_when_built


# ------------------------- errors_shown_to_user ------------------------- #


def test_errors_shown_to_user_no_error(caplog):
    with main.errors_shown_to_user('create the report'):
        result = 'the report'

    assert result == 'the report'
    assert caplog.text == ''


def test_errors_shown_to_user_invalid_xml(tmp_path, caplog):
    bad = tmp_path / 'not_valid.xml'
    bad.write_text('<amendmentList><oops></amendmentList>')
    reached_end_of_block = False

    with main.errors_shown_to_user('create the report'):
        main.Report(bad, bad)
        reached_end_of_block = True

    # the error stopped the with block, but was not raised
    assert not reached_end_of_block
    assert (
        'Could not create the report. not_valid.xml is not a valid XML file.'
        in caplog.text
    )


def test_errors_shown_to_user_missing_file(tmp_path, caplog):
    missing = tmp_path / 'missing.xml'

    with main.errors_shown_to_user('create the report'):
        main.Report(missing, missing)

    assert 'Could not create the report.' in caplog.text
    assert 'missing.xml' in caplog.text


def test_errors_shown_to_user_other_error(caplog):
    with main.errors_shown_to_user('create the report'):
        # a bug, as an example. (A bare `raise` here would make Pyright think
        # the asserts below can never run.)
        int('not a number')

    assert 'Could not create the report. [ValueError("invalid literal' in caplog.text
    # the traceback goes to the log too
    assert caplog.records[-1].exc_info is not None


# ---------------------------- save_and_open ----------------------------- #


def a_report() -> etree._ElementTree:
    """A tiny HTML report"""

    return html.fromstring('<html><body>report</body></html>').getroottree()


def test_save_and_open(tmp_path, modal):
    out = tmp_path / 'report.html'

    main.save_and_open(a_report(), out, modal)

    assert out.read_text(encoding='utf-8').startswith('<!DOCTYPE html>')
    assert modal.messages[0] == f'HTML report created: {out}'


def test_save_failure_names_the_file(tmp_path, modal, caplog):
    # a missing folder, rather than a read-only one, because read-only
    # folders do not stop files being written on Windows
    out = tmp_path / 'no_such_folder' / 'report.html'

    with main.errors_shown_to_user('create the report'):
        main.save_and_open(a_report(), out, modal)

    assert 'Could not create the report.' in caplog.text
    assert 'no_such_folder' in caplog.text
    assert modal.messages == []  # nothing claimed to be created


def test_browser_does_not_open(tmp_path, modal, monkeypatch, caplog):
    monkeypatch.setattr(main.webbrowser, 'open', lambda uri: False)
    out = tmp_path / 'report.html'

    main.save_and_open(a_report(), out, modal)

    assert out.exists()
    assert 'Could not open the report in a browser.' in caplog.text


# ------------------------ Check Amendment Papers ------------------------ #


def test_compare_report_built_while_dialog_open(monkeypatch, modal, papers):
    dialog_open_when_built = record_when_built(monkeypatch, 'Report', modal)
    api = main.Api()
    api.com_amend_old_xml, api.com_amend_new_xml = papers

    api.amend_create_html_compare(days_between_papers=True)

    assert dialog_open_when_built == [True]
    assert len(list(papers[0].parent.glob('Comp_Amdts_*.html'))) == 1
    assert any(message.startswith('HTML report created') for message in modal.messages)


def test_compare_report_invalid_xml(modal, papers, caplog):
    old, new = papers
    old.write_text('<amendmentList><oops></amendmentList>')
    api = main.Api()
    api.com_amend_old_xml, api.com_amend_new_xml = old, new

    api.amend_create_html_compare()  # must not raise

    assert f'{old.name} is not a valid XML file.' in caplog.text
    assert list(old.parent.glob('*.html')) == []


# ------------------------- Duplicate Amendments ------------------------- #


def test_duplicates_report_built_while_dialog_open(monkeypatch, modal, papers):
    dialog_open_when_built = record_when_built(monkeypatch, 'DupReport', modal)
    api = main.Api()
    api.dup_amend_xml = papers[1]

    api.dup_amend_html_report()

    assert dialog_open_when_built == [True]
    assert len(list(papers[1].parent.glob('Dup_Amdts_*.html'))) == 1
