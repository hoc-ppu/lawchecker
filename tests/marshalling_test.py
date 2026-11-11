"""
Tests for marshalling.py, using made-up papers.

Each paper is a list of keys (amendment numbers) and Headings. Letters are
used for amendments that should stay unmoved, and x, y, z for the ones that
should move, to make the expected answers easier to follow. The tests on
real papers are with the report, in compare_amendment_documents_test.py.
"""

import random

import pytest

from lawchecker.amendment_document import Heading
from lawchecker.marshalling import Alignment, Group, Run, align


def cells(alignment: Alignment) -> list[tuple[str, str, str]]:
    """The rows as (kind, old, new), with '' for an empty cell"""

    def text(item) -> str:
        if item is None:
            return ''
        return item.text if isinstance(item, Heading) else item

    return [(row.kind, text(row.old), text(row.new)) for row in alignment.rows]


# --------------------------- No moves ---------------------------------- #


def test_no_change():
    alignment = align(['1', '2', '3'], ['1', '2', '3'])

    assert alignment.unmoved == ['1', '2', '3']
    assert alignment.moved == alignment.added == alignment.removed == []
    assert alignment.groups == []
    assert cells(alignment) == [
        ('unmoved', '1', '1'),
        ('unmoved', '2', '2'),
        ('unmoved', '3', '3'),
    ]


@pytest.mark.parametrize(
    'old, new, added, removed',
    [
        pytest.param([], [], [], [], id='both-empty'),
        pytest.param([], ['1', '2'], ['1', '2'], [], id='old-empty'),
        pytest.param(['1', '2'], [], [], ['1', '2'], id='new-empty'),
    ],
)
def test_empty_paper(old, new, added, removed):
    alignment = align(old, new)

    assert alignment.unmoved == alignment.moved == []
    assert alignment.added == added
    assert alignment.removed == removed
    assert len(alignment.rows) == len(old) + len(new)


def test_added_and_removed():
    """New and removed amendments are not moves"""

    alignment = align(['1', '2', '3'], ['N', '1', '3'])

    assert alignment.added == ['N']
    assert alignment.removed == ['2']
    assert alignment.moved == []
    assert cells(alignment) == [
        ('added', '', 'N'),
        ('unmoved', '1', '1'),
        ('removed', '2', ''),
        ('unmoved', '3', '3'),
    ]


# ----------------------------- Moves ------------------------------------ #


def test_swap():
    """
    Two amendments swapped places. Either could be the one that moved; the
    one now higher up the paper is chosen (as in the Victims example, where
    1 moved to before 2).
    """

    alignment = align(['1', '2', '3'], ['2', '1', '3'])

    assert alignment.unmoved == ['1', '3']
    assert alignment.moved == ['2']
    assert alignment.groups == [
        Group(
            runs=[Run(['2'], was_after='1', was_before='3')],
            now_after=None,
            now_before='1',
        )
    ]
    assert cells(alignment) == [
        ('moved', '', '2'),
        ('unmoved', '1', '1'),
        ('moved', '2', ''),
        ('unmoved', '3', '3'),
    ]


def test_block_moved():
    """A block that moves together is one run"""

    alignment = align(['A', 'B', 'C', 'D', 'x', 'y'], ['A', 'x', 'y', 'B', 'C', 'D'])

    assert alignment.unmoved == ['A', 'B', 'C', 'D']
    assert alignment.moved == ['x', 'y']
    assert alignment.groups == [
        Group(
            runs=[Run(['x', 'y'], was_after='D', was_before=None)],
            now_after='A',
            now_before='B',
        )
    ]
    assert cells(alignment) == [
        ('unmoved', 'A', 'A'),
        ('moved', '', 'x'),
        ('moved', '', 'y'),
        ('unmoved', 'B', 'B'),
        ('unmoved', 'C', 'C'),
        ('unmoved', 'D', 'D'),
        ('moved', 'x', ''),
        ('moved', 'y', ''),
    ]


def test_gathered_into_one_place():
    """Amendments from different places, now together: one group, three runs"""

    alignment = align(
        ['A', 'x', 'B', 'C', 'y', 'D', 'E', 'z', 'F', 'G'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'x', 'y', 'z'],
    )

    assert alignment.moved == ['x', 'y', 'z']
    assert alignment.groups == [
        Group(
            runs=[
                Run(['x'], was_after='A', was_before='B'),
                Run(['y'], was_after='C', was_before='D'),
                Run(['z'], was_after='E', was_before='F'),
            ],
            now_after='G',
            now_before=None,
        )
    ]


def test_gathered_at_the_end_tie():
    """
    As above, but z was next to F, so "z moved after F" and "F moved before
    x" leave the same number unmoved. The current rule picks F, though a
    clerk would say z. This records what happens; see TODO.md.
    """

    alignment = align(
        ['A', 'x', 'B', 'C', 'y', 'D', 'E', 'z', 'F'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'x', 'y', 'z'],
    )

    assert alignment.moved == ['F', 'x', 'y']


def test_block_split_up():
    """A run that is split up is in two groups"""

    alignment = align(
        ['A', 'x', 'y', 'B', 'C', 'D', 'E'],
        ['A', 'B', 'C', 'x', 'D', 'E', 'y'],
    )

    assert alignment.unmoved == ['A', 'B', 'C', 'D', 'E']
    assert alignment.groups == [
        Group(
            runs=[Run(['x'], was_after='A', was_before='B')],
            now_after='C',
            now_before='D',
        ),
        Group(
            runs=[Run(['y'], was_after='A', was_before='B')],
            now_after='E',
            now_before=None,
        ),
    ]


def test_reversed():
    """Amendments in the opposite order are separate runs, not one"""

    alignment = align(['1', '2', '3', '4'], ['4', '3', '2', '1'])

    assert alignment.unmoved == ['1']
    assert alignment.moved == ['4', '3', '2']
    assert alignment.groups == [
        Group(
            runs=[
                Run(['4'], was_after='1', was_before=None),
                Run(['3'], was_after='1', was_before=None),
                Run(['2'], was_after='1', was_before=None),
            ],
            now_after=None,
            now_before='1',
        )
    ]


def test_moved_with_added_and_removed():
    alignment = align(
        ['A', 'R', 'x', 'B', 'C', 'D'],
        ['A', 'B', 'C', 'N', 'x', 'D'],
    )

    assert alignment.unmoved == ['A', 'B', 'C', 'D']
    assert alignment.moved == ['x']
    assert alignment.added == ['N']
    assert alignment.removed == ['R']
    assert alignment.groups == [
        Group(
            runs=[Run(['x'], was_after='A', was_before='B')],
            now_after='C',
            now_before='D',
        )
    ]
    assert cells(alignment) == [
        ('unmoved', 'A', 'A'),
        ('removed', 'R', ''),
        ('moved', 'x', ''),
        ('unmoved', 'B', 'B'),
        ('unmoved', 'C', 'C'),
        ('added', '', 'N'),
        ('moved', '', 'x'),
        ('unmoved', 'D', 'D'),
    ]


def test_run_ignores_added_amendment_in_between():
    """x and y are still one run, although N has been added between them"""

    alignment = align(
        ['A', 'x', 'y', 'B', 'C', 'D'],
        ['A', 'B', 'C', 'D', 'x', 'N', 'y'],
    )

    assert alignment.groups == [
        Group(
            runs=[Run(['x', 'y'], was_after='A', was_before='B')],
            now_after='D',
            now_before=None,
        )
    ]


def test_duplicate_keys():
    with pytest.raises(ValueError, match='older paper has these keys more than'):
        align(['1', '1'], ['1'])


# ---------------------------- Headings ---------------------------------- #

FIRST_DAY = Heading('FIRST DAY')
SECOND_DAY = Heading('SECOND DAY')
NEW_CLAUSES = Heading('NEW CLAUSES')


def test_same_headings_share_rows():
    alignment = align(
        [FIRST_DAY, '1', SECOND_DAY, '2'],
        [FIRST_DAY, '1', SECOND_DAY, '2'],
    )

    assert alignment.moved == []
    assert cells(alignment) == [
        ('heading', 'FIRST DAY', 'FIRST DAY'),
        ('unmoved', '1', '1'),
        ('heading', 'SECOND DAY', 'SECOND DAY'),
        ('unmoved', '2', '2'),
    ]


def test_heading_on_newer_paper_only():
    alignment = align(['1', '2'], [FIRST_DAY, '1', '2'])

    assert cells(alignment) == [
        ('heading', '', 'FIRST DAY'),
        ('unmoved', '1', '1'),
        ('unmoved', '2', '2'),
    ]


def test_different_headings_at_the_same_place():
    alignment = align([FIRST_DAY, '1'], [SECOND_DAY, '1'])

    assert cells(alignment) == [
        ('heading', 'FIRST DAY', 'SECOND DAY'),
        ('unmoved', '1', '1'),
    ]


def test_heading_added_to_a_block():
    """The headings that match are lined up"""

    alignment = align([NEW_CLAUSES, '1'], [FIRST_DAY, NEW_CLAUSES, '1'])

    assert cells(alignment) == [
        ('heading', '', 'FIRST DAY'),
        ('heading', 'NEW CLAUSES', 'NEW CLAUSES'),
        ('unmoved', '1', '1'),
    ]


def test_first_day_business_removed():
    """
    As in health_day_rep_0907 to 0908. The FIRST DAY headings stay with the
    removed amendments, and the SECOND DAY headings line up.
    """

    alignment = align(
        [FIRST_DAY, NEW_CLAUSES, '1', '2', SECOND_DAY, NEW_CLAUSES, '3'],
        [SECOND_DAY, NEW_CLAUSES, '3'],
    )

    assert cells(alignment) == [
        ('heading', 'FIRST DAY', ''),
        ('heading', 'NEW CLAUSES', ''),
        ('removed', '1', ''),
        ('removed', '2', ''),
        ('heading', 'SECOND DAY', 'SECOND DAY'),
        ('heading', 'NEW CLAUSES', 'NEW CLAUSES'),
        ('unmoved', '3', '3'),
    ]


def test_moved_under_new_headings():
    """The headings above a moved amendment stay with it"""

    alignment = align(
        ['A', 'x', 'B', 'C'],
        ['A', 'B', 'C', SECOND_DAY, NEW_CLAUSES, 'x'],
    )

    assert alignment.groups == [
        Group(
            runs=[Run(['x'], was_after='A', was_before='B')],
            now_after='C',
            now_before=None,
            now_under=(SECOND_DAY, NEW_CLAUSES),
        )
    ]
    assert cells(alignment) == [
        ('unmoved', 'A', 'A'),
        ('moved', 'x', ''),
        ('unmoved', 'B', 'B'),
        ('unmoved', 'C', 'C'),
        ('heading', '', 'SECOND DAY'),
        ('heading', '', 'NEW CLAUSES'),
        ('moved', '', 'x'),
    ]


def test_moved_from_one_day_to_another():
    """The headings a run was under, and the headings a group is now under"""

    alignment = align(
        [FIRST_DAY, 'A', 'x', 'B', SECOND_DAY, 'C', 'D'],
        [FIRST_DAY, 'A', 'B', SECOND_DAY, 'C', 'x', 'D'],
    )

    assert alignment.groups == [
        Group(
            runs=[Run(['x'], was_after='A', was_before='B', was_under=(FIRST_DAY,))],
            now_after='C',
            now_before='D',
            now_under=(SECOND_DAY,),
        )
    ]
    assert cells(alignment) == [
        ('heading', 'FIRST DAY', 'FIRST DAY'),
        ('unmoved', 'A', 'A'),
        ('moved', 'x', ''),
        ('unmoved', 'B', 'B'),
        ('heading', 'SECOND DAY', 'SECOND DAY'),
        ('unmoved', 'C', 'C'),
        ('moved', '', 'x'),
        ('unmoved', 'D', 'D'),
    ]


# ------------------------ Random papers --------------------------------- #


def random_papers(rng: random.Random) -> tuple[list, list]:
    """
    A made-up older paper, and a newer paper with some amendments removed,
    moved and added. Both have a few headings in random places.
    """

    old = [str(n) for n in range(rng.randint(0, 30))]

    new = [key for key in old if rng.random() > 0.1]
    for _ in range(rng.randint(0, 5)):
        if new:
            moving = new.pop(rng.randrange(len(new)))
            new.insert(rng.randrange(len(new) + 1), moving)
    for n in range(rng.randint(0, 5)):
        new.insert(rng.randrange(len(new) + 1), f'N{n}')

    def add_headings(items: list) -> list:
        for _ in range(rng.randint(0, 3)):
            heading = rng.choice([FIRST_DAY, SECOND_DAY, NEW_CLAUSES])
            items.insert(rng.randrange(len(items) + 1), heading)
        return items

    return add_headings(old), add_headings(new)


def longest_increasing_length(values: list[int]) -> int:
    """The slow but simple way, to check the fast way in marshalling.py"""

    lengths: list[int] = []
    for i, value in enumerate(values):
        shorter = [lengths[j] for j in range(i) if values[j] < value]
        lengths.append(1 + max(shorter, default=0))
    return max(lengths, default=0)


@pytest.mark.parametrize('seed', range(200))
def test_random_papers(seed):
    """Things that should be true of any two papers"""

    old, new = random_papers(random.Random(seed))
    alignment = align(old, new)
    rows = alignment.rows

    # every item in each paper is in the rows once, in paper order
    assert [row.old for row in rows if row.old is not None] == old
    assert [row.new for row in rows if row.new is not None] == new

    # unmoved amendments share a row, and are in the same order in both papers
    for row in rows:
        if row.kind == 'unmoved':
            assert row.old == row.new
    old_keys = [item for item in old if not isinstance(item, Heading)]
    new_keys = [item for item in new if not isinstance(item, Heading)]
    unmoved = set(alignment.unmoved)
    assert [key for key in old_keys if key in unmoved] == alignment.unmoved
    assert [key for key in new_keys if key in unmoved] == alignment.unmoved

    # as many amendments as possible are unmoved
    common_old = [key for key in old_keys if key in new_keys]
    positions = [common_old.index(key) for key in new_keys if key in common_old]
    assert len(alignment.unmoved) == longest_increasing_length(positions)

    # each moved amendment has two rows, and is in one run
    moved_rows = [row for row in rows if row.kind == 'moved']
    assert len(moved_rows) == 2 * len(alignment.moved)
    assert [key for group in alignment.groups for key in group.keys] == (
        alignment.moved
    )

    # the amendments in a run were next to each other in the older paper
    for run in alignment.runs:
        start = common_old.index(run.keys[0])
        assert common_old[start : start + len(run.keys)] == run.keys
