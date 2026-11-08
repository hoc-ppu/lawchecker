from pathlib import Path

import pytest

from lawchecker import compare_amendment_documents as compare
from lawchecker.compare_amendment_documents import ChangedNames
from paper_builder import make_amendment, make_paper

# built from this file's location so the tests work from any directory
EXAMPLES = Path(__file__).resolve().parent.parent / 'example_files' / 'amendments'


@pytest.fixture(scope='module')
def energy_report() -> compare.Report:
    """Report comparing two real Energy Bill papers. Made once for this file."""

    return compare.Report(
        EXAMPLES / 'energy_rm_rep_0904.xml',
        EXAMPLES / 'energy_day_rep_0905.xml',
    )


def table_rows(table) -> list[list[str]]:
    """The text of each cell in an HTML table, row by row, header row first."""

    return [[cell.text_content() for cell in row] for row in table.iter('tr')]


# ------------------------------ Intro ----------------------------------- #


def test_render_intro(energy_report):
    """The intro table shows each paper's metadata side by side"""

    table = energy_report.render_intro().find('.//table')

    assert table_rows(table) == [
        ['', 'energy_rm_rep_0904.xml', 'energy_day_rep_0905.xml'],
        [
            'File path',
            str(EXAMPLES / 'energy_rm_rep_0904.xml'),
            str(EXAMPLES / 'energy_day_rep_0905.xml'),
        ],
        ['Bill Title', 'Energy Bill [HL]', 'Energy Bill [HL]'],
        ['Published date', 'Monday 04 September 2023', 'Tuesday 05 September 2023'],
        ['List Type', '(Amendment Paper)', '(Amendment Paper)'],
    ]


# ------------------------------ Names ----------------------------------- #


def test_added_and_removed_names_table(energy_report):
    """One row per amendment whose names changed"""

    assert len(energy_report.name_changes) == 87
    assert energy_report.name_changes[0] == ChangedNames(
        'NC7', ['Wendy Chamberlain'], []
    )

    rows = table_rows(energy_report.added_and_removed_names_table())
    rows_by_num = {row[0]: row for row in rows[1:]}

    assert rows[0] == ['Ref', 'Names added', 'Names removed', 'Totals']
    assert len(rows) == 1 + 87
    assert rows_by_num['NC7'] == ['NC7', 'Wendy Chamberlain', '', 'Added: 1']
    assert rows_by_num['NC53'] == [
        'NC53',
        'Olivia Blake [R]',
        'Olivia Blake',
        'Added: 1, Removed: 1',
    ]


def test_diff_names_in_context():
    """A changed name is reported, and shown in context in a diff table"""

    # NC53 from the real Energy papers: Olivia Blake becomes Olivia Blake [R]
    old = make_paper(
        make_amendment(
            'NC53',
            proposer='Edward Miliband',
            supporters=('Dr Alan Whitehead', 'Kerry McCarthy', 'Olivia Blake'),
        )
    )
    new = make_paper(
        make_amendment(
            'NC53',
            proposer='Edward Miliband',
            supporters=('Dr Alan Whitehead', 'Kerry McCarthy', 'Olivia Blake [R]'),
        )
    )

    report = compare.Report(old, new)

    assert report.name_changes == [
        ChangedNames('NC53', added=['Olivia Blake [R]'], removed=['Olivia Blake'])
    ]
    assert [item.num for item in report.name_changes_in_context] == ['NC53']

    in_context = report.render_added_and_removed_names().find(
        './/div[@id="name-changes-in-context"]'
    )
    # difflib uses non-breaking spaces
    text = in_context.text_content().replace('\xa0', ' ')
    assert 'NC53:' in text
    assert 'Olivia Blake [R]' in text
    assert in_context.find('.//table[@class="diff"]') is not None


def test_diff_names_in_context_warning(caplog):
    """Test that warning is generated when there is a problem finding sponsors"""

    compare.Report(
        make_paper(make_amendment('NC52', proposer=None)),
        make_paper(make_amendment('NC52', proposer=None)),
    )

    assert 'NC52: no sponsors found' in caplog.text


# ---------------------------- Star check -------------------------------- #

# One row per rule. None means no star (the attribute is left out of the
# XML, as in real papers). 'UNKNOWN STAR' tests a bad value in the XML.
# old star, new star, days between papers, correct stars, incorrect stars
STAR_RULES = [
    # correct
    pytest.param('★', '☆', False, ['NC52 (☆)'], [], id='black-to-white'),
    pytest.param('☆', None, False, ['NC52 (No Star)'], [], id='white-to-none'),
    pytest.param('★', None, True, ['NC52 (No Star)'], [], id='black-to-none-days'),
    pytest.param('☆', None, True, ['NC52 (No Star)'], [], id='white-to-none-days'),
    pytest.param(None, None, False, [], [], id='none-stays-none'),
    pytest.param(None, None, True, [], [], id='none-stays-none-days'),
    # incorrect
    pytest.param('★', '★', False, [], ['NC52 has ★ (☆ expected)'], id='black-to-black'),
    pytest.param(
        '★', None, False, [], ['NC52 has No Star (☆ expected)'], id='black-to-none'
    ),
    pytest.param(
        '★', '☆', True, [], ['NC52 has ☆ (No Star expected)'], id='black-to-white-days'
    ),
    pytest.param(
        '☆', '☆', False, [], ['NC52 has ☆ (No Star expected)'], id='white-to-white'
    ),
    pytest.param(
        '☆', '★', False, [], ['NC52 has ★ (No Star expected)'], id='white-to-black'
    ),
    pytest.param(
        None, '★', False, [], ['NC52 has ★ (No Star expected)'], id='none-to-black'
    ),
    pytest.param(
        None, '☆', False, [], ['NC52 has ☆ (No Star expected)'], id='none-to-white'
    ),
    pytest.param(
        None, '★', True, [], ['NC52 has ★ (No Star expected)'], id='none-to-black-days'
    ),
    pytest.param(
        None, '☆', True, [], ['NC52 has ☆ (No Star expected)'], id='none-to-white-days'
    ),
    # bad star values in the XML
    pytest.param(
        '★',
        'UNKNOWN STAR',
        False,
        [],
        ['NC52 has Error with star (☆ expected)'],
        id='unknown-in-new',
    ),
    pytest.param(
        'UNKNOWN STAR',
        '★',
        False,
        [],
        ['Error with star in Test, NC52 check manually.'],
        id='unknown-in-old',
    ),
]


@pytest.mark.parametrize(
    'old_star, new_star, days_between_papers, correct, incorrect', STAR_RULES
)
def test_star_check_standing_amendment(
    old_star, new_star, days_between_papers, correct, incorrect
):
    """NC52 is on both papers. Is its star in the newer paper right?"""

    report = compare.Report(
        make_paper(make_amendment('NC52', star=old_star)),
        make_paper(make_amendment('NC52', star=new_star)),
        days_between_papers=days_between_papers,
    )

    assert report.correct_stars == correct
    assert report.incorrect_stars == incorrect


@pytest.mark.parametrize(
    'new_star, correct, incorrect',
    [
        pytest.param('★', ['NC52 (★)'], [], id='black'),
        pytest.param('☆', [], ['NC52 has ☆ (★ expected)'], id='white'),
        pytest.param(None, [], ['NC52 has No Star (★ expected)'], id='none'),
    ],
)
def test_star_check_new_amendment(new_star, correct, incorrect):
    """NC52 is only on the newer paper, so it should have a black star"""

    report = compare.Report(
        make_paper(),
        make_paper(make_amendment('NC52', star=new_star)),
    )

    assert report.correct_stars == correct
    assert report.incorrect_stars == incorrect


# -------------------- Duplicate amendment numbers ----------------------- #


def test_duplicate_amendment_numbers_card():
    """The report warns about duplicate numbers and says which amendments"""

    report = compare.Report(
        make_paper(
            make_amendment('NC52', dnum='HoC1', proposer='Ann Example'),
            make_amendment('NC52', dnum='HoC2', proposer='Bob Example'),
        ),
        make_paper(make_amendment('NC52')),
    )

    card_text = report.render_duplicate_amdt_nums().text_content()

    assert 'Duplicate amendment numbers' in card_text
    assert 'NC52: 2 amendments (HoC1, Ann Example; HoC2, Bob Example)' in card_text


def test_no_duplicate_amendment_numbers_no_card():
    """With no duplicates, nothing is added to the report"""

    report = compare.Report(
        make_paper(make_amendment('NC52')),
        make_paper(make_amendment('NC52')),
    )

    rendered = report.render_duplicate_amdt_nums()

    assert rendered.tag == 'div'
    assert len(rendered) == 0
    assert rendered.text_content() == ''


# ---------------------------- Real papers ------------------------------- #


@pytest.mark.parametrize(
    'old, new, days_between_papers, removed, added, incorrect_stars, changed',
    [
        pytest.param(
            'energy_rm_rep_0904',
            'energy_day_rep_0905',
            False,
            ['NC55'],
            [],
            [],
            ['NC53'],
            id='energy',
        ),
        pytest.param(
            'datapro_rm_rep_0721',
            'datapro_rm_rep_0825',
            False,
            [],
            [],
            ['NC2 has No Star (☆ expected)'],
            [],
            id='datapro',
        ),
        pytest.param(
            'econactivity_rm_rep_0918',
            'econactivity_rm_rep_0919',
            False,
            [],
            [],
            [],
            ['4'],
            id='econactivity',
        ),
        pytest.param(
            'victims_prisoners_rm_rep_0906',
            'victims_prisoners_rm_rep_0908',
            True,
            [],
            [],
            [],
            [],
            id='victims',
        ),
    ],
)
def test_real_papers(
    old, new, days_between_papers, removed, added, incorrect_stars, changed
):
    """
    What the report finds for pairs of real papers, so that a change which
    alters the results gets noticed.

    The expected values are what the report found on 8 November 2026. The
    datapro star problem is the one described in example_files/examples.md.
    For econactivity, amendment 4 changed (line 5 became line 4); examples.md
    says amendment 1, which is wrong.
    """

    report = compare.Report(
        EXAMPLES / f'{old}.xml',
        EXAMPLES / f'{new}.xml',
        days_between_papers=days_between_papers,
    )

    assert sorted(report.removed_amdts) == removed
    assert sorted(report.added_amdts) == added
    assert report.incorrect_stars == incorrect_stars
    assert [item.num for item in report.changed_amdts] == changed
