"""
Work out how the order of amendments changed between two amendment papers.

Used by the Check Amendment Papers report to show amendments that have moved
(been re-marshalled) between the older and the newer paper. This module only
deals with order: it knows nothing about XML or HTML.

Each paper is given as a list of items in paper order. An item is either an
amendment's key (a string that identifies the same amendment in both papers,
such as its number) or a Heading (from amendment_document.py, which has
only the heading's text).

- Unmoved: the amendments in both papers that kept their order. They are
  found with the longest increasing subsequence of their old positions,
  taken in new-paper order, which leaves as many amendments unmoved as
  possible. So when a block of amendments moves, the block is reported as
  moving, not everything around it. When there is more than one equally
  good answer (e.g. two amendments swapped places), one is picked, and it
  is always the same one for the same papers.
- Moved: every other amendment that is in both papers.
- Run: moved amendments that are next to each other, in the same order, on
  both papers. Added and removed amendments in between are ignored.
- Group: moved amendments that are now in the same place, i.e. between the
  same two unmoved amendments in the newer paper. A group has one or more
  runs.
- Headings are not matched or counted as moves. A heading belongs with the
  amendment after it, and headings before the same unmoved amendment on
  both papers share rows.
"""

from bisect import bisect_left
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from itertools import zip_longest
from typing import Literal

from lawchecker.amendment_document import Heading

Item = str | Heading

RowKind = Literal['unmoved', 'moved', 'added', 'removed', 'heading']


@dataclass(frozen=True)
class Row:
    """
    One row of the side-by-side view.

    old and new are what is on each side of the row: an amendment's key, a
    Heading, or None for an empty cell. A moved amendment has two rows: one
    with only old (where it was) and one with only new (where it is now).
    """

    kind: RowKind
    old: Item | None
    new: Item | None


@dataclass
class Run:
    """Moved amendments that are next to each other in both papers"""

    keys: list[str]
    # the nearest unmoved amendments either side of the run in the older
    # paper. None means the start (or end) of the paper.
    was_after: str | None
    was_before: str | None
    # the headings above the run in the older paper
    was_under: tuple[Heading, ...] = ()


@dataclass
class Group:
    """Moved amendments that are now between the same unmoved amendments"""

    runs: list[Run]
    # the unmoved amendments either side of the group in the newer paper.
    # None means the start (or end) of the paper.
    now_after: str | None
    now_before: str | None
    # the headings above the group in the newer paper
    now_under: tuple[Heading, ...] = ()

    @property
    def keys(self) -> list[str]:
        return [key for run in self.runs for key in run.keys]


@dataclass
class Alignment:
    """How the order changed. Lists of keys are in paper order."""

    unmoved: list[str]
    moved: list[str]  # in new-paper order
    added: list[str]
    removed: list[str]
    groups: list[Group]  # in new-paper order
    rows: list[Row]

    @property
    def runs(self) -> list[Run]:
        return [run for group in self.groups for run in group.runs]


def align(old: Sequence[Item], new: Sequence[Item]) -> Alignment:
    """
    Compare the order of the older paper's items with the newer paper's.

    Each key must only appear once in each paper (raises ValueError), so
    leave out any duplicated amendment numbers before calling this.
    """

    old_keys = _keys(old, 'older')
    new_keys = _keys(new, 'newer')
    old_set, new_set = set(old_keys), set(new_keys)

    # the amendments in both papers, in each paper's order
    common_old = [key for key in old_keys if key in new_set]
    common_new = [key for key in new_keys if key in old_set]
    old_position = {key: i for i, key in enumerate(common_old)}

    unmoved = [
        common_old[position]
        for position in _longest_increasing([old_position[k] for k in common_new])
    ]
    unmoved_set = set(unmoved)

    return Alignment(
        unmoved=unmoved,
        moved=[key for key in common_new if key not in unmoved_set],
        added=[key for key in new_keys if key not in old_set],
        removed=[key for key in old_keys if key not in new_set],
        groups=_groups(old, new, unmoved_set, old_position),
        rows=_rows(old, new, unmoved_set, old_set, new_set),
    )


def _keys(items: Sequence[Item], paper: str) -> list[str]:
    keys = [item for item in items if not isinstance(item, Heading)]

    # This line creates a list of values that appear more than once in keys
    duplicates = [key for key, count in Counter(keys).items() if count > 1]

    if duplicates:
        raise ValueError(
            f'The {paper} paper has these keys more than once:'
            f' {", ".join(duplicates)}. Each key must only appear once.'
        )
    return keys


def _longest_increasing(values: list[int]) -> list[int]:
    """
    One longest strictly increasing subsequence of values, in order.

    Patience sorting, which takes O(n log n) time.
    """

    # tails[n] is the smallest value that ends an increasing subsequence of
    # length n + 1 so far, and tail_index[n] is where that value is
    tails: list[int] = []
    tail_index: list[int] = []
    # previous[i] is where the value before values[i] is, in the subsequence
    # ending at values[i]
    previous = [-1] * len(values)

    for i, value in enumerate(values):
        length = bisect_left(tails, value)
        if length == len(tails):
            tails.append(value)
            tail_index.append(i)
        else:
            tails[length] = value
            tail_index[length] = i
        previous[i] = tail_index[length - 1] if length else -1

    result = []
    i = tail_index[-1] if tail_index else -1
    while i != -1:
        result.append(values[i])
        i = previous[i]

    return result[::-1]


def _with_headings(items: Sequence[Item]) -> Iterator[tuple[str, tuple[Heading, ...]]]:
    """
    Each amendment key, with the headings it comes under: the most recent
    block of headings (one heading or several in a row) above it.
    """

    under: tuple[Heading, ...] = ()
    after_heading = False

    for item in items:
        if isinstance(item, Heading):
            under = (*under, item) if after_heading else (item,)
            after_heading = True
        else:
            after_heading = False
            yield item, under


def _groups(
    old: Sequence[Item],
    new: Sequence[Item],
    unmoved: set[str],
    old_position: dict[str, int],
) -> list[Group]:
    # where each amendment was in the older paper
    was_after: dict[str, str | None] = {}
    was_under: dict[str, tuple[Heading, ...]] = {}
    last_unmoved = None
    for key, under in _with_headings(old):
        was_after[key] = last_unmoved
        was_under[key] = under
        if key in unmoved:
            last_unmoved = key

    was_before: dict[str, str | None] = {}
    next_unmoved = None
    for key in reversed(list(was_after)):
        was_before[key] = next_unmoved
        if key in unmoved:
            next_unmoved = key

    # walk the newer paper, collecting moved amendments between unmoved ones
    groups: list[Group] = []
    group: Group | None = None
    last_unmoved = None

    for key, under in _with_headings(new):
        if key in unmoved:
            if group:
                group.now_before = key
                groups.append(group)
                group = None
            last_unmoved = key

        elif key in old_position:  # in both papers, so it has moved
            if group is None:
                group = Group(
                    runs=[], now_after=last_unmoved, now_before=None, now_under=under
                )

            run = group.runs[-1] if group.runs else None
            if run and old_position[key] == old_position[run.keys[-1]] + 1:
                # next to the previous one in the older paper too
                run.keys.append(key)
                run.was_before = was_before[key]
            else:
                group.runs.append(
                    Run([key], was_after[key], was_before[key], was_under[key])
                )

        # otherwise it is a new amendment, which does not affect the groups

    if group:
        groups.append(group)

    return groups


def _next_amendment(items: Sequence[Item], start: int) -> int:
    """The index of the first amendment at or after start (len(items) if none)"""

    for i in range(start, len(items)):
        if not isinstance(items[i], Heading):
            return i
    return len(items)


def _rows(
    old: Sequence[Item],
    new: Sequence[Item],
    unmoved: set[str],
    old_set: set[str],
    new_set: set[str],
) -> list[Row]:
    """
    The rows of the side-by-side view, found by walking both papers at once.

    Amendments that moved, were added or were removed get a row on their
    own side. Unmoved amendments share a row. Headings go with the amendment
    after them.
    """

    rows: list[Row] = []
    i = j = 0

    while i < len(old) or j < len(new):
        i_next = _next_amendment(old, i)
        j_next = _next_amendment(new, j)
        old_key = old[i_next] if i_next < len(old) else None
        new_key = new[j_next] if j_next < len(new) else None

        if old_key is not None and old_key not in unmoved:
            # moved from here, or removed
            rows += [Row('heading', heading, None) for heading in old[i:i_next]]
            kind = 'moved' if old_key in new_set else 'removed'
            rows.append(Row(kind, old_key, None))
            i = i_next + 1

        elif new_key is not None and new_key not in unmoved:
            # moved to here, or added
            rows += [Row('heading', None, heading) for heading in new[j:j_next]]
            kind = 'moved' if new_key in old_set else 'added'
            rows.append(Row(kind, None, new_key))
            j = j_next + 1

        else:
            # Unmoved amendments are in the same order in both papers, and
            # everything before them has been dealt with, so both papers are
            # at the same unmoved amendment (or both are at the end).
            assert old_key == new_key, (old_key, new_key)
            rows += _heading_rows(old[i:i_next], new[j:j_next])
            if old_key is not None:
                rows.append(Row('unmoved', old_key, new_key))
            i, j = i_next + 1, j_next + 1

    return rows


def _heading_rows(old: Sequence[Item], new: Sequence[Item]) -> list[Row]:
    """
    Rows for the headings just before the same place in both papers.

    Headings with the same text share a row. Others at the same point in
    the list are paired up (e.g. FIRST DAY became SECOND DAY), and any left
    over go on their own side.
    """

    rows: list[Row] = []
    matcher = SequenceMatcher(a=old, b=new, autojunk=False)

    for _, i1, i2, j1, j2 in matcher.get_opcodes():
        for old_heading, new_heading in zip_longest(old[i1:i2], new[j1:j2]):
            rows.append(Row('heading', old_heading, new_heading))

    return rows
