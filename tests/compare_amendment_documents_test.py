from pathlib import Path

import pytest
from paper_builder import make_amendment, make_heading, make_paper

from lawchecker import compare_amendment_documents as compare
from lawchecker.amendment_document import Heading, SupDocument
from lawchecker.compare_amendment_documents import ChangedNames, check_papers_match
from lawchecker.marshalling import Group, Row, RowKind, Run

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
        ['House', 'House of Commons', 'House of Commons'],
        ['Stage', 'Report Stage', 'Report Stage'],
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
    """NC52 is in both papers. Is its star in the newer paper right?"""

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
    """NC52 is only in the newer paper, so it should have a black star"""

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


# ----------------- Papers from different stages or bills ---------------- #

COMMONS_REPORT_STAGE = {
    'bill_title': 'Health Bill',
    'house': 'House of Commons',
    'stage': 'Report Stage',
}


def test_same_stage_and_bill_no_warning():
    """Papers from the same stage of the same bill: no warning and no card"""

    report = compare.Report(
        make_paper(make_amendment('1'), **COMMONS_REPORT_STAGE),
        # differences in case and spacing are ignored
        make_paper(
            make_amendment('1'),
            bill_title='health  bill',
            house='House of Commons',
            stage='Report stage',
        ),
    )

    assert report.paper_warnings == []

    rendered = report.render_paper_warnings()
    assert rendered.tag == 'div'
    assert len(rendered) == 0


@pytest.mark.parametrize(
    'changed, summary',
    [
        pytest.param(
            {'stage': 'Committee Stage'},
            'These papers are from different stages.',
            id='stage',
        ),
        pytest.param(
            {'house': 'House of Lords'},
            'These papers are from different stages.',
            id='house',
        ),
        pytest.param(
            {'bill_title': 'Energy Bill [HL]'},
            'These papers are for different bills.',
            id='bill',
        ),
        pytest.param(
            {'stage': None},
            'Could not check that these papers are from the same stage.',
            id='no-stage',
        ),
        pytest.param(
            {'stage': ''},
            'Could not check that these papers are from the same stage.',
            id='empty-stage',
        ),
        pytest.param(
            {'house': None},
            'Could not check that these papers are from the same stage.',
            id='no-house',
        ),
        pytest.param(
            {'bill_title': None},
            'Could not check that these papers are for the same bill.',
            id='no-bill-title',
        ),
    ],
)
def test_paper_warnings(changed, summary, caplog):
    """
    The newer paper's metadata differs from the older paper's (or is
    missing). There is one warning, in the report and in the log, and the
    rest of the report is still made.
    """

    report = compare.Report(
        make_paper(make_amendment('1'), **COMMONS_REPORT_STAGE),
        make_paper(make_amendment('1'), **(COMMONS_REPORT_STAGE | changed)),
    )

    assert [warning.summary for warning in report.paper_warnings] == [summary]
    assert summary in report.render_paper_warnings().text_content()
    assert summary in caplog.text

    assert report.no_name_changes == ['1']


def test_papers_from_different_stages_real():
    """A Committee Stage paper and a Report Stage paper of the same bill"""

    report = compare.Report(
        EXAMPLES / 'english_dev_rm_pbc_1010.xml',
        EXAMPLES / 'english_dev_rm_rep_1118.xml',
    )

    [warning] = report.paper_warnings
    assert warning.summary == 'These papers are from different stages.'
    assert warning.detail.startswith(
        'english_dev_rm_pbc_1010.xml is from the Committee Stage'
        ' (House of Commons) and english_dev_rm_rep_1118.xml is from the'
        ' Report Stage (House of Commons).'
    )

    # the card is in the report, straight after the intro
    intro = report.html_root.find('.//section[@id="intro"]').getparent()
    assert 'Are these the right papers?' in intro.getnext().text_content()


@pytest.mark.parametrize(
    'old, new',
    [
        ('energy_rm_rep_0904', 'energy_day_rep_0905'),
        ('datapro_rm_rep_0721', 'datapro_rm_rep_0825'),
        ('econactivity_rm_rep_0918', 'econactivity_rm_rep_0919'),
        ('victims_prisoners_rm_rep_0906', 'victims_prisoners_rm_rep_0908'),
        ('english_dev_rm_rep_1118', 'english_dev_rm_rep_1119'),
        ('health_rm_rep_0901', 'health_rm_rep_0902'),
        ('health_rm_rep_0902', 'health_rm_rep_0903'),
        ('health_rm_rep_0903', 'health_rm_rep_0904'),
        ('health_rm_rep_0904', 'health_day_rep_0907'),
        ('health_day_rep_0907', 'health_day_rep_0908'),
    ],
)
def test_real_papers_from_the_same_stage(old, new):
    """None of the same-stage example pairs gives a warning"""

    old_doc = SupDocument(EXAMPLES / f'{old}.xml')
    new_doc = SupDocument(EXAMPLES / f'{new}.xml')

    assert check_papers_match(old_doc, new_doc) == []


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


# ------------------- Amendment numbers and dnums ------------------------ #


def test_same_number_different_dnum(caplog):
    """Amendment 2 has a different dnum, so it may be a different amendment"""

    report = compare.Report(
        make_paper(make_amendment('1', dnum='HoC1'), make_amendment('2', dnum='HoC2')),
        make_paper(make_amendment('1', dnum='HoC1'), make_amendment('2', dnum='HoC9')),
    )

    [pair] = report.same_num_different_dnum
    assert (pair.old.dnum, pair.new.dnum) == ('HoC2', 'HoC9')
    assert report.same_dnum_different_num == []

    text = report.render_numbers_and_dnums().text_content()
    assert 'These numbers are in both papers with different dnums' in text
    assert '2: HoC2 in the older paper, HoC9 in the newer' in text
    assert 'Some amendment numbers are in both papers with different dnums' in (
        caplog.text
    )


def test_same_dnum_different_number(caplog):
    """HoC33 was numbered 12 and is now 14"""

    report = compare.Report(
        make_paper(make_amendment('12', dnum='HoC33')),
        make_paper(make_amendment('14', dnum='HoC33')),
    )

    [pair] = report.same_dnum_different_num
    assert (pair.old.num, pair.new.num) == ('12', '14')
    assert report.same_num_different_dnum == []

    # the rest of the report still matches by number
    assert report.removed_amdts == ['12']
    assert report.added_amdts == ['14']

    text = report.render_numbers_and_dnums().text_content()
    assert 'same dnum but a different number in each paper' in text
    assert 'HoC33: 12 in the older paper, 14 in the newer' in text
    assert 'Some amendments have the same dnum but a different number' in caplog.text


@pytest.mark.parametrize('old_dnum, new_dnum', [('', 'HoC9'), ('HoC1', ''), ('', '')])
def test_empty_dnum_not_checked(old_dnum, new_dnum):
    report = compare.Report(
        make_paper(make_amendment('1', dnum=old_dnum)),
        make_paper(make_amendment('1', dnum=new_dnum)),
    )

    assert report.same_num_different_dnum == []
    assert report.same_dnum_different_num == []

    rendered = report.render_numbers_and_dnums()
    assert rendered.tag == 'div'
    assert len(rendered) == 0


def test_duplicate_number_first_amendment_used_for_dnums():
    """The second amendment numbered 2 (HoC3) is not checked"""

    report = compare.Report(
        make_paper(make_amendment('2', dnum='HoC2')),
        make_paper(make_amendment('2', dnum='HoC2'), make_amendment('2', dnum='HoC3')),
    )

    assert report.same_num_different_dnum == []
    assert report.same_dnum_different_num == []


# ---------------------- Amendment order (marshalling) ------------------- #


def test_order_items():
    """
    The numbers and headings given to marshalling.align. Only the first
    amendment with each number is used, as in the rest of the report.
    """

    doc = SupDocument(
        make_paper(
            make_heading('FIRST DAY'),
            make_amendment('2', dnum='HoC2'),
            make_amendment('1'),
            make_amendment('2', dnum='HoC3'),
        )
    )

    assert compare.order_items(doc) == [Heading('FIRST DAY'), '2', '1']


def test_order():
    report = compare.Report(
        make_paper(make_amendment('1'), make_amendment('2'), make_amendment('3')),
        make_paper(make_amendment('2'), make_amendment('1'), make_amendment('4')),
    )

    assert report.order is not None
    assert report.order.unmoved == ['1']
    assert report.order.moved == ['2']
    assert report.order.added == ['4']
    assert report.order.removed == ['3']


@pytest.mark.parametrize(
    'changed',
    [{'stage': 'Committee Stage'}, {'bill_title': 'Energy Bill [HL]'}],
    ids=['stage', 'bill'],
)
def test_papers_differ_no_order_or_dnum_check(changed):
    """
    On papers from different stages or bills, the same number is usually a
    different amendment, so neither is done.
    """

    report = compare.Report(
        make_paper(make_amendment('1', dnum='HoC1'), **COMMONS_REPORT_STAGE),
        make_paper(
            make_amendment('1', dnum='HoC9'), **(COMMONS_REPORT_STAGE | changed)
        ),
    )

    assert report.order is None
    assert report.same_num_different_dnum == []


@pytest.mark.parametrize(
    'changed',
    [{'stage': None}, {'bill_title': None}],
    ids=['no-stage', 'no-bill-title'],
)
def test_missing_metadata_order_still_made(changed):
    """If the papers could not be checked, warn (see above) and carry on"""

    report = compare.Report(
        make_paper(make_amendment('1', dnum='HoC1'), **COMMONS_REPORT_STAGE),
        make_paper(
            make_amendment('1', dnum='HoC9'), **(COMMONS_REPORT_STAGE | changed)
        ),
    )

    assert report.order is not None
    assert report.order.unmoved == ['1']
    assert len(report.same_num_different_dnum) == 1


def test_papers_from_different_stages_real_no_order():
    """All 195 numbers in both papers have different dnums, but no card"""

    report = compare.Report(
        EXAMPLES / 'english_dev_rm_pbc_1010.xml',
        EXAMPLES / 'english_dev_rm_rep_1118.xml',
    )

    assert report.order is None
    assert 'Amendment numbers and dnums' not in report.html_root.text_content()


@pytest.mark.parametrize(
    'old, new, counts',
    [
        # counts are moved, runs, groups, added, removed
        ('energy_rm_rep_0904', 'energy_day_rep_0905', (0, 0, 0, 0, 1)),
        ('datapro_rm_rep_0721', 'datapro_rm_rep_0825', (0, 0, 0, 0, 0)),
        ('econactivity_rm_rep_0918', 'econactivity_rm_rep_0919', (0, 0, 0, 0, 0)),
        (
            'victims_prisoners_rm_rep_0906',
            'victims_prisoners_rm_rep_0908',
            (1, 1, 1, 0, 0),
        ),
        ('english_dev_rm_rep_1118', 'english_dev_rm_rep_1119', (44, 10, 1, 38, 3)),
        ('health_rm_rep_0901', 'health_rm_rep_0902', (52, 27, 1, 33, 1)),
        ('health_rm_rep_0902', 'health_rm_rep_0903', (7, 6, 5, 52, 0)),
        ('health_rm_rep_0903', 'health_rm_rep_0904', (1, 1, 1, 1, 0)),
        ('health_rm_rep_0904', 'health_day_rep_0907', (0, 0, 0, 0, 0)),
        ('health_day_rep_0907', 'health_day_rep_0908', (0, 0, 0, 0, 166)),
    ],
)
def test_order_real_papers(old, new, counts):
    """
    How the order changed on pairs of real papers, so that a change which
    alters the results gets noticed. The expected values are what the
    report found on 10 November 2026.
    """

    report = compare.Report(EXAMPLES / f'{old}.xml', EXAMPLES / f'{new}.xml')
    order = report.order

    assert order is not None
    assert (
        len(order.moved),
        len(order.runs),
        len(order.groups),
        len(order.added),
        len(order.removed),
    ) == counts

    # the same as the Added and removed amendments card
    assert sorted(order.added) == sorted(report.added_amdts)
    assert sorted(order.removed) == sorted(report.removed_amdts)

    # the numbers and dnums agree on all of these
    assert report.same_num_different_dnum == []
    assert report.same_dnum_different_num == []


def test_order_real_papers_swap():
    """Amendments 2 and 1 swapped places. 1 is reported as moved."""

    report = compare.Report(
        EXAMPLES / 'victims_prisoners_rm_rep_0906.xml',
        EXAMPLES / 'victims_prisoners_rm_rep_0908.xml',
    )

    assert report.order is not None
    assert report.order.groups == [
        Group(
            runs=[Run(['1'], was_after='2', was_before='3')],
            now_after='NC3',
            now_before='2',
        )
    ]


def test_order_real_papers_removed():
    report = compare.Report(
        EXAMPLES / 'english_dev_rm_rep_1118.xml',
        EXAMPLES / 'english_dev_rm_rep_1119.xml',
    )

    assert report.order is not None
    assert report.order.removed == ['NC3', '67', '68']


def test_order_real_papers_moved_back():
    """NC63 moved back to where it was on the 0902 paper"""

    report = compare.Report(
        EXAMPLES / 'health_rm_rep_0903.xml',
        EXAMPLES / 'health_rm_rep_0904.xml',
    )

    assert report.order is not None
    assert report.order.moved == ['NC63']


def test_order_real_papers_first_day_removed():
    """
    Day One's business has gone. Its headings stay in the older paper only,
    and Day Two's headings are in both papers, so they share rows.
    """

    report = compare.Report(
        EXAMPLES / 'health_day_rep_0907.xml',
        EXAMPLES / 'health_day_rep_0908.xml',
    )

    first_day, clauses_1_to_61, second_day, clauses_62_to_81 = [
        item for item in report.old_doc.sequence if isinstance(item, Heading)
    ]
    assert first_day == Heading('FIRST DAY')
    assert second_day == Heading('SECOND DAY')

    assert report.order is not None
    assert [
        (row.old, row.new) for row in report.order.rows if row.kind == 'heading'
    ] == [
        (first_day, None),
        (clauses_1_to_61, None),
        (second_day, second_day),
        (clauses_62_to_81, clauses_62_to_81),
    ]


# ------------------------- Moved amendments card ------------------------ #


def card_lines(card) -> list[str]:
    """
    The text of a card, one line per paragraph, list item or <summary>.
    List items start with '- ', indented by two spaces for each level.
    """

    lines = []
    content = card.find('.//div[@class="secondary-info"]')

    for element in content.iter('p', 'li', 'summary'):
        if element.tag == 'li':
            # the item's own text, without any list inside it
            text = ''.join(element.xpath('text() | *[not(self::ul)]//text()'))
            depth = len(list(element.iterancestors('ul')))
            lines.append('  ' * (depth - 1) + '- ' + ' '.join(text.split()))
        else:
            lines.append(' '.join(element.text_content().split()))

    return lines


EXPLANATION = (
    'These amendments are in a different place, compared with the amendments'
    ' around them, from where they were in the older paper.'
)


@pytest.mark.parametrize(
    'nums, expected',
    [
        ([], ''),
        (['1'], '1'),
        (['1', '2'], '1 and 2'),
        (['1', '2', '3'], '1, 2 and 3'),
    ],
)
def test_join_nums(nums, expected):
    assert compare.join_nums(nums) == expected


@pytest.mark.parametrize(
    'after, before, expected',
    [
        ('2', '3', 'between 2 and 3'),
        ('2', None, 'after 2'),
        (None, '3', 'before 3'),
    ],
)
def test_describe_place(after, before, expected):
    assert compare.describe_place(after, before) == expected


def test_describe_place_no_unmoved_amendment():
    with pytest.raises(ValueError):
        compare.describe_place(None, None)


def test_first_heading():
    assert compare.first_heading(()) == ''
    assert (
        compare.first_heading((Heading('FIRST DAY'), Heading('NEW CLAUSES')))
        == 'FIRST DAY'
    )


def moved_card(old: list[str], new: list[str]) -> list[str]:
    """
    The Moved amendments card's lines for two made-up papers. Items starting
    with 'NC' are amendments, anything else is a heading.
    """

    def paper(items: list[str]):
        return make_paper(
            *(
                make_amendment(item) if item.startswith('NC') else make_heading(item)
                for item in items
            )
        )

    report = compare.Report(paper(old), paper(new))
    return card_lines(report.render_moved_amdts())


def test_moved_card_swap():
    """NC2 is now before NC1, at the start of the paper"""

    lines = moved_card(['NC1', 'NC2', 'NC3'], ['NC2', 'NC1', 'NC3'])

    assert lines[0].startswith(EXPLANATION)
    assert lines[1:] == [
        'Of the 3 amendments in both papers, 1 has moved.',
        '- 1 amendment is now before NC1',
        '  - NC2 was between NC1 and NC3',
    ]


def test_moved_card_to_the_end():
    lines = moved_card(['NC1', 'NC2', 'NC3'], ['NC2', 'NC3', 'NC1'])

    assert lines[1:] == [
        'Of the 3 amendments in both papers, 1 has moved.',
        '- 1 amendment is now after NC3',
        '  - NC1 was before NC2',
    ]


def test_moved_card_two_runs_to_one_place():
    """NC2 and NC5 were in different places, and are now together"""

    lines = moved_card(
        ['NC1', 'NC2', 'NC3', 'NC4', 'NC5', 'NC6', 'NC7'],
        ['NC1', 'NC3', 'NC4', 'NC6', 'NC7', 'NC2', 'NC5'],
    )

    assert lines[1:] == [
        'Of the 7 amendments in both papers, 2 have moved.',
        '- 2 amendments are now after NC7',
        '  - NC2 was between NC1 and NC3',
        '  - NC5 was between NC4 and NC6',
    ]


def test_moved_card_to_another_day():
    """The heading they were under is shown, because it has changed"""

    lines = moved_card(
        ['FIRST DAY', 'NC1', 'NC2', 'NC3', 'NC4', 'SECOND DAY', 'NC5', 'NC6', 'NC7'],
        ['FIRST DAY', 'NC1', 'NC4', 'SECOND DAY', 'NC5', 'NC6', 'NC2', 'NC3', 'NC7'],
    )

    assert lines[1:] == [
        'Of the 7 amendments in both papers, 2 have moved.',
        '- 2 amendments are now between NC6 and NC7, under SECOND DAY',
        '  - NC2 and NC3 were between NC1 and NC4, under FIRST DAY',
    ]


def test_moved_card_within_a_day():
    """The heading is the same, so it is only given once"""

    lines = moved_card(
        ['FIRST DAY', 'NC1', 'NC2', 'NC3', 'NC4', 'NC5'],
        ['FIRST DAY', 'NC1', 'NC3', 'NC4', 'NC2', 'NC5'],
    )

    assert lines[1:] == [
        'Of the 5 amendments in both papers, 1 has moved.',
        '- 1 amendment is now between NC4 and NC5, under FIRST DAY',
        '  - NC2 was between NC1 and NC3',
    ]


@pytest.mark.parametrize(
    'old, new, expected',
    [
        pytest.param(
            ['NC1', 'NC2'],
            ['NC1', 'NC2', 'NC3'],
            [
                'No amendments have moved. The 2 amendments in both papers are'
                ' in the same order.',
            ],
            id='no-moves',
        ),
        pytest.param(
            ['NC1'],
            ['NC1'],
            ['No amendments have moved.'],
            id='one-amendment',
        ),
        pytest.param(
            ['NC1', 'NC3'],
            ['NC2'],
            [
                'No amendments are in both papers.',
            ],
            id='none-in-both',
        ),
    ],
)
def test_moved_card_nothing_moved(old, new, expected):
    assert moved_card(old, new) == expected


def test_moved_card_papers_differ():
    report = compare.Report(
        make_paper(make_amendment('1'), **COMMONS_REPORT_STAGE),
        make_paper(
            make_amendment('1'),
            **(COMMONS_REPORT_STAGE | {'stage': 'Committee Stage'}),
        ),
    )

    assert card_lines(report.render_moved_amdts()) == [
        'Not checked, because these papers are from different stages or for'
        ' different bills (see above).'
    ]


def test_moved_card_real_papers_swap():
    report = compare.Report(
        EXAMPLES / 'victims_prisoners_rm_rep_0906.xml',
        EXAMPLES / 'victims_prisoners_rm_rep_0908.xml',
    )

    assert card_lines(report.render_moved_amdts())[1:] == [
        'Of the 6 amendments in both papers, 1 has moved.',
        '- 1 amendment is now between NC3 and 2',
        '  - 1 was between 2 and 3',
    ]

    # the card is straight after the Added and removed amendments card
    labels = [
        h2.get('data-heading-label')
        for h2 in report.html_root.iter('h2')
        if h2.get('data-heading-label')
    ]
    assert labels.index('Moved amendments') == (
        labels.index('Added and removed amendments') + 1
    )


def test_moved_card_real_papers_days():
    report = compare.Report(
        EXAMPLES / 'health_rm_rep_0902.xml',
        EXAMPLES / 'health_rm_rep_0903.xml',
    )

    lines = card_lines(report.render_moved_amdts())

    # lines[0] is the explanation, and nothing comes after the list
    assert lines[1:] == [
        'Of the 210 amendments in both papers, 7 have moved.',
        '- 1 amendment is now between NC55 and NC57, under FIRST DAY',
        '  - NC56 was between NC52 and NC58, under SECOND DAY',
        '- 1 amendment is now between NC62 and NC64, under FIRST DAY',
        '  - NC63 was between NC60 and NC68, under SECOND DAY',
        '- 2 amendments are now between NC108 and NC118, under FIRST DAY',
        '  - NC109 was between NC107 and NC110, under SECOND DAY',
        '  - NC115 was between NC114 and NC116, under SECOND DAY',
        '- 2 amendments are now between NC83 and NC88, under SECOND DAY',
        '  - NC86 and NC87 were between NC85 and NC90, under FIRST DAY',
        '- 1 amendment is now between NC126 and NC128, under SECOND DAY',
        '  - NC127 was between NC122 and NC129, under FIRST DAY',
    ]


# ------------------------ Side-by-side order card ----------------------- #


def side_by_side_cell(cell) -> str:
    """An amendment's number and label, e.g. 'NC2 (moved ↑)', or the text"""

    num = cell.find('span[@class="om-num"]')
    if num is None:
        # a heading, or an empty cell
        return cell.text_content()

    label = cell.find('span[@class="om-label"]')
    return num.text + (f' ({label.text})' if label is not None else '')


def side_by_side_row(row) -> str:
    """e.g. 'moved |  | NC2 (moved ↑)'"""

    kind = row.get('class').split()[1].removeprefix('om-')
    old, _gap, new = row
    return f'{kind} | {side_by_side_cell(old)} | {side_by_side_cell(new)}'


def side_by_side(report: compare.Report) -> list[str]:
    """
    The rows of the Side-by-side order card as text, one line per row (see
    side_by_side_row). A fold is shown as 'fold: ' and its summary, and the
    rows inside it are indented.
    """

    lines = []
    order_map = report.render_side_by_side().find('.//div[@class="order-map"]')
    assert order_map is not None

    for element in order_map:
        if element.tag == 'details':
            lines.append(f'fold: {element.findtext("summary", default="")}')
            lines += [f'  {side_by_side_row(row)}' for row in element.findall('div')]
        elif 'om-head' not in element.get('class', '').split():
            lines.append(side_by_side_row(element))

    return lines


def paper_of(*nums: str):
    return make_paper(*(make_amendment(num) for num in nums))


def test_side_by_side():
    """NC2 moved up, NC3 was removed and NC4 was added"""

    report = compare.Report(
        paper_of('NC1', 'NC2', 'NC3'), paper_of('NC2', 'NC1', 'NC4')
    )

    assert side_by_side(report) == [
        'moved |  | NC2 (moved ↑)',
        'unmoved | NC1 | NC1',
        'moved | NC2 (moved ↑) | ',
        'removed | NC3 (removed) | ',
        'added |  | NC4 (added)',
    ]


def test_side_by_side_links():
    """→ and ← link a moved amendment's two rows"""

    report = compare.Report(paper_of('NC1', 'NC2'), paper_of('NC2', 'NC1'))
    root = report.html_root

    old_row = root.get_element_by_id('order-old-NC2')
    new_row = root.get_element_by_id('order-new-NC2')
    assert (old_row.get('data-key'), old_row.get('data-side')) == ('NC2', 'old')
    assert (new_row.get('data-key'), new_row.get('data-side')) == ('NC2', 'new')

    [old_link] = old_row.find_class('om-jump')
    [new_link] = new_row.find_class('om-jump')
    assert (old_link.text, old_link.get('href')) == ('→', '#order-new-NC2')
    assert (new_link.text, new_link.get('href')) == ('←', '#order-old-NC2')


def test_side_by_side_cell_details():
    """The star is shown, and the description, proposer and dnum on hover"""

    report = compare.Report(
        make_paper(
            make_amendment(
                'NC1',
                star='★',
                dnum='HoC1',
                proposer='Ann Example',
                instruction='Clause 1, page 1, line 1, leave out “a”',
            ),
            make_amendment('NC2'),
        ),
        paper_of('NC1', 'NC2'),
    )
    order_map = report.render_side_by_side().find('.//div[@class="order-map"]')
    assert order_map is not None
    first_row, second_row = order_map.find_class('om-unmoved')
    old_cell = first_row[0]

    assert old_cell.find_class('om-star')[0].text == '★'
    assert old_cell.find_class('om-desc')[0].text == (
        'Clause 1, page 1, line 1, leave out “a”'
    )
    assert old_cell.get('title') == (
        'Clause 1, page 1, line 1, leave out “a”\nAnn Example\nHoC1'
    )

    # no star (and no dnum)
    assert second_row[0].find_class('om-star')[0].text is None
    assert second_row[0].get('title') == (
        'Clause 1, page 1, line 1, leave out “example”\nAnn Example'
    )


@pytest.mark.parametrize(
    'kinds, context, expected',
    [
        ('uuuuuu', 2, []),
        ('uuuuuuu', 2, [(2, 4)]),
        # a heading ends a stretch
        ('uuuuhuuuu', 2, []),
        ('muuuuuuuua', 2, [(3, 6)]),
        ('uuuuuuuhuuuuuuu', 2, [(2, 4), (10, 12)]),
        ('uuuuu', 1, [(1, 3)]),
    ],
)
def test_fold_ranges(kinds, context, expected):
    """kinds has a letter for each row: u for unmoved, h for a heading..."""

    kind_names: dict[str, RowKind] = {
        'u': 'unmoved',
        'h': 'heading',
        'm': 'moved',
        'a': 'added',
    }
    rows = [Row(kind_names[kind], 'NC1', 'NC1') for kind in kinds]

    assert compare.fold_ranges(rows, context) == expected


def test_side_by_side_no_fold():
    """Six unmoved amendments in a row are all shown"""

    nums = [f'NC{n}' for n in range(1, 7)]
    report = compare.Report(paper_of(*nums), paper_of(*nums))

    assert side_by_side(report) == [f'unmoved | {num} | {num}' for num in nums]


def test_side_by_side_fold():
    """Seven are folded, leaving two showing at each end"""

    nums = [f'NC{n}' for n in range(1, 8)]
    report = compare.Report(paper_of(*nums), paper_of(*nums))

    assert side_by_side(report) == [
        'unmoved | NC1 | NC1',
        'unmoved | NC2 | NC2',
        'fold: 3 amendments have not moved: NC3 to NC5',
        '  unmoved | NC3 | NC3',
        '  unmoved | NC4 | NC4',
        '  unmoved | NC5 | NC5',
        'unmoved | NC6 | NC6',
        'unmoved | NC7 | NC7',
    ]


def test_side_by_side_papers_differ():
    report = compare.Report(
        make_paper(make_amendment('1'), **COMMONS_REPORT_STAGE),
        make_paper(
            make_amendment('1'),
            **(COMMONS_REPORT_STAGE | {'stage': 'Committee Stage'}),
        ),
    )

    rendered = report.render_side_by_side()
    assert rendered.tag == 'div'
    assert len(rendered) == 0


def test_side_by_side_real_papers_swap():
    report = compare.Report(
        EXAMPLES / 'victims_prisoners_rm_rep_0906.xml',
        EXAMPLES / 'victims_prisoners_rm_rep_0908.xml',
    )

    assert side_by_side(report) == [
        'unmoved | NC1 | NC1',
        'unmoved | NC2 | NC2',
        'unmoved | NC3 | NC3',
        'moved |  | 1 (moved ↑)',
        'unmoved | 2 | 2',
        'moved | 1 (moved ↑) | ',
        'unmoved | 3 | 3',
    ]

    # the card is straight after the Moved amendments card
    labels = [
        h2.get('data-heading-label')
        for h2 in report.html_root.iter('h2')
        if h2.get('data-heading-label')
    ]
    assert labels.index('Side-by-side order') == labels.index('Moved amendments') + 1


@pytest.mark.parametrize(
    'old, new',
    [
        ('english_dev_rm_rep_1118', 'english_dev_rm_rep_1119'),
        ('health_rm_rep_0902', 'health_rm_rep_0903'),
    ],
)
def test_side_by_side_real_papers_links(old, new):
    """Every → and ← goes to a row, and no id is used twice in the report"""

    report = compare.Report(EXAMPLES / f'{old}.xml', EXAMPLES / f'{new}.xml')
    assert report.order is not None

    ids = report.html_root.xpath('//@id')
    assert len(ids) == len(set(ids))

    links = report.html_root.find_class('om-jump')
    assert len(links) == 2 * len(report.order.moved)
    for link in links:
        assert link.get('href', '').removeprefix('#') in ids


def test_side_by_side_real_papers_headings():
    """Day One's business has gone, along with its headings"""

    report = compare.Report(
        EXAMPLES / 'health_day_rep_0907.xml',
        EXAMPLES / 'health_day_rep_0908.xml',
    )
    lines = side_by_side(report)

    assert lines[0] == 'heading | FIRST DAY | '
    assert lines[1].startswith('heading | NEW CLAUSES AND NEW SCHEDULES RELATING TO')
    assert lines[1].endswith('THE WORKFORCE OF THE NHS | ')

    # everything between FIRST DAY and SECOND DAY was removed. Removed rows
    # are never folded.
    second_day = lines.index('heading | SECOND DAY | SECOND DAY')
    assert all(line.startswith('removed |') for line in lines[2:second_day])
    assert sum(line.startswith('removed |') for line in lines) == 166


# --------------- Run ids, for the JavaScript in the template ------------ #


def test_run_ids_link_the_two_cards():
    """
    The Moved amendments card's lines and the side-by-side rows have the
    same run ids (data-run), so the Highlight buttons can find the rows
    """

    report = compare.Report(
        paper_of('NC1', 'NC2', 'NC3', 'NC4', 'NC5', 'NC6', 'NC7'),
        paper_of('NC1', 'NC3', 'NC4', 'NC6', 'NC7', 'NC2', 'NC5'),
    )

    summary = report.render_moved_amdts()
    [summary_list] = summary.find_class('om-summary')
    [group] = summary_list.xpath('li[@data-group]')
    assert group.get('data-group') == 'g0'
    assert [line.get('data-run') for line in group.xpath('.//li')] == ['r0', 'r1']

    rows = report.render_side_by_side().xpath('.//div[@data-run]')
    assert [
        (row.get('data-key'), row.get('data-side'), row.get('data-run')) for row in rows
    ] == [
        ('NC2', 'old', 'r0'),
        ('NC5', 'old', 'r1'),
        ('NC2', 'new', 'r0'),
        ('NC5', 'new', 'r1'),
    ]


@pytest.mark.parametrize(
    'old, new',
    [
        ('english_dev_rm_rep_1118', 'english_dev_rm_rep_1119'),
        ('health_rm_rep_0902', 'health_rm_rep_0903'),
    ],
)
def test_run_ids_real_papers(old, new):
    report = compare.Report(EXAMPLES / f'{old}.xml', EXAMPLES / f'{new}.xml')
    assert report.order is not None
    expected = {f'r{i}': run.keys for i, run in enumerate(report.order.runs)}

    # one line in the summary for each run
    lines = report.render_moved_amdts().xpath('.//li[@data-run]')
    assert [line.get('data-run') for line in lines] == list(expected)

    # every moved row has its run's id
    rows = report.render_side_by_side().find_class('om-moved')
    keys_by_run: dict[str, list[str]] = {}
    for row in rows:
        if row.get('data-side') == 'new':
            keys_by_run.setdefault(row.get('data-run', ''), []).append(
                row.get('data-key', '')
            )
    assert keys_by_run == expected
    assert len(rows) == 2 * len(report.order.moved)
