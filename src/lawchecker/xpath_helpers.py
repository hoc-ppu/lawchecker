from collections.abc import Mapping
from typing import Any, Generic, TypeVar, cast

from lxml import etree
from lxml.etree import _Element

from .settings import NSMAP

T = TypeVar("T")


class XPath(etree.XPath, Generic[T]):
    # fix etree.XPath for typing purposes
    def __init__(
        self,
        path: str,
        expected_type: type[T],
        *,
        namespaces: Mapping[str, str] | None = NSMAP,
        **kwargs: Any,
    ):
        super().__init__(
            path,
            namespaces=namespaces,
            **kwargs,
        )
        self.typ = expected_type

    def __call__(self, _etree_or_element, **_variables) -> T:
        typ = self.typ
        return cast(typ, super().__call__(_etree_or_element, **_variables))


get_amendments = XPath(
    "//xmlns:component[xmlns:amendment]",
    expected_type=list[_Element],
)

# here sections will include clauses and schedule paragraphs
get_sections = XPath(
    "//xmlns:section[not(ancestor::xmlns:mod)]",
    expected_type=list[_Element],
)

get_schedules = XPath(
    "//xmlns:hcontainer[@name='schedule'][not(ancestor::xmlns:mod)]",
    expected_type=list[_Element],
)

get_sched_paras = XPath(
    ".//xmlns:paragraph[not(ancestor::xmlns:mod)]",
    expected_type=list[_Element],
)

text_content = XPath("string()", expected_type=type(str()))

# get MP name elements. These are proposer and supporters elements
get_name_elements = XPath(
    (
        "xmlns:amendmentHeading/xmlns:block[@name='proposer' or"
        " @name='supporters']/*[@refersTo]"
    ),
    expected_type=list[_Element],
)

get_amdt_heading = XPath(
    "xmlns:amendmentHeading[1]",
    expected_type=list[_Element],
)

get_amdt_content = XPath(
    "xmlns:amendmentContent[1]",
    expected_type=list[_Element],
)
