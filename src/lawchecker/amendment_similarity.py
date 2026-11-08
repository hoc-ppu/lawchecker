#!/usr/bin/env python3

"""
Pure algorithmic helpers for finding exact-duplicate and similar amendments
within a single LawMaker XML official list document.

No HTML/report concerns live here - see duplicate_amendments.py for that.
"""

import re
from collections.abc import Iterable, Sequence
from copy import deepcopy
from difflib import SequenceMatcher
from typing import NamedTuple

from lxml.etree import _Element

from lawchecker import xpath_helpers as xp
from lawchecker.amendment_document import Amendment
from lawchecker.lawchecker_logger import logger
from lawchecker.settings import NSMAP, SIMILARITY_THRESHOLD


class TextBucket(NamedTuple):
    """All amendments sharing identical (whitespace-normalized) content text."""

    normalized_text: str
    content_xml: _Element  # cleaned, num-stripped content of one member, for diffing
    members: list[Amendment]


class SimilarPair(NamedTuple):
    """Two distinct buckets whose text similarity meets the threshold."""

    bucket_a: TextBucket
    bucket_b: TextBucket
    ratio: float


class LocationGroup(NamedTuple):
    """Buckets whose text is identical once the location prefix is removed."""

    bucket: TextBucket  # normalized_text is the location-stripped text
    variant_count: int  # number of distinct raw texts (i.e. distinct locations)


_LOCATION_PREFIX = re.compile(
    r'^\s*(?:(?:new\s+)?(?:clause|schedule|section|part)\s+\S+,\s*)?'
    r'page\s+\d+(?:,\s*line\s+\d+)?,?\s*',
    re.IGNORECASE,
)


def strip_location(text: str) -> str:
    """Remove a leading 'Clause N, page N, line N,' style reference."""

    return _LOCATION_PREFIX.sub('', text, count=1)


def group_by_location(buckets: Iterable[TextBucket]) -> list[LocationGroup]:
    """Merge buckets whose text differs only in the location prefix."""

    merged: dict[str, TextBucket] = {}
    counts: dict[str, int] = {}

    for bucket in buckets:
        key = strip_location(bucket.normalized_text)
        counts[key] = counts.get(key, 0) + 1
        if key in merged:
            merged[key].members.extend(bucket.members)
        else:
            merged[key] = TextBucket(key, bucket.content_xml, list(bucket.members))

    return [LocationGroup(merged[key], counts[key]) for key in merged]


def normalize_amdt_content(amdt: Amendment) -> tuple[str, _Element] | None:
    """
    Extract an amendment's content, strip the amendment number (which
    routinely differs between otherwise identical amendments), and return
    (whitespace-collapsed text, cleaned content element).

    Returns None if the amendment has no content.
    """

    amdt_content = xp.get_amdt_content(amdt.xml)

    if len(amdt_content) == 0:
        logger.warning(f'{amdt.num}: has no content')
        return None

    content_xml = deepcopy(amdt_content[0])

    amendment_num = content_xml.find('.//xmlns:num[@ukl:dnum]', namespaces=NSMAP)
    if amendment_num is not None:
        parent = amendment_num.getparent()
        if parent is not None:
            parent.remove(amendment_num)

    text = xp.text_content(content_xml)
    normalized_text = re.sub(r'\n+', '\n', text)
    normalized_text = re.sub(r'[^\S\n]+', ' ', normalized_text)
    normalized_text = re.sub(r'(\n )+', '\n', normalized_text)

    return normalized_text, content_xml


def build_text_buckets(amendments: Iterable[Amendment]) -> list[TextBucket]:
    """
    Group amendments by identical normalized text.

    Amendments with no content are skipped (and logged by
    normalize_amdt_content).
    """

    buckets: dict[str, TextBucket] = {}

    for amdt in amendments:
        result = normalize_amdt_content(amdt)
        if result is None:
            continue

        normalized_text, content_xml = result

        if normalized_text in buckets:
            buckets[normalized_text].members.append(amdt)
        else:
            buckets[normalized_text] = TextBucket(
                normalized_text=normalized_text,
                content_xml=content_xml,
                members=[amdt],
            )

    return list(buckets.values())


def exact_duplicate_buckets(buckets: Iterable[TextBucket]) -> list[TextBucket]:
    """Return only the buckets with more than one member."""

    return [bucket for bucket in buckets if len(bucket.members) > 1]


def find_similar_pairs(
    buckets: Sequence[TextBucket],
    threshold: float = SIMILARITY_THRESHOLD,
    min_length: int = 0,
) -> list[SimilarPair]:
    """
    Compare every distinct pair of bucket representatives (a bucket is never
    compared against itself) and return those whose SequenceMatcher.ratio()
    is >= threshold.

    Buckets whose normalized text is shorter than min_length are excluded
    entirely (a placeholder for future short-amendment handling).

    Two optimisations avoid a full O(n^2) comparison:
    * Buckets are sorted by length, and for each bucket we only consider
      longer buckets up to the point where the length ratio alone rules out
      reaching `threshold` (derived from the same bound used by
      SequenceMatcher.real_quick_ratio()). This is exact, not an
      approximation - once a candidate is too long, so is everything after it.
    * For remaining candidates, we use SequenceMatcher's quick_ratio() (a
      cheap upper bound on ratio()) to skip pairs before paying for the full
      ratio() alignment.
    """

    candidates = sorted(
        (bucket for bucket in buckets if len(bucket.normalized_text) >= min_length),
        key=lambda bucket: len(bucket.normalized_text),
    )

    # For two strings to reach `threshold`, the shorter length must be at
    # least this fraction of the longer length (from the real_quick_ratio
    # upper bound: 2*min(len_a, len_b) / (len_a + len_b) >= threshold).
    min_length_ratio = threshold / (2 - threshold)

    similar_pairs: list[SimilarPair] = []

    for i, bucket_a in enumerate(candidates):
        len_a = len(bucket_a.normalized_text)
        if len_a == 0:
            continue

        matcher = SequenceMatcher(None, bucket_a.normalized_text)

        for bucket_b in candidates[i + 1 :]:
            len_b = len(bucket_b.normalized_text)

            # candidates are sorted by length, so once bucket_b is too much
            # longer than bucket_a, every subsequent candidate will be too
            if len_a / len_b < min_length_ratio:
                break

            matcher.set_seq2(bucket_b.normalized_text)

            if matcher.quick_ratio() < threshold:
                continue

            ratio = matcher.ratio()
            if ratio >= threshold:
                similar_pairs.append(SimilarPair(bucket_a, bucket_b, ratio))

    return similar_pairs
