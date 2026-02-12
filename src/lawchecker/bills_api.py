"""
UK Parliament Bills API Client
API documentation: https://bills-api.parliament.uk
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

import httpx

from lawchecker.lawchecker_logger import logger

BASE_URL = 'https://bills-api.parliament.uk/api/v1'


# ============================================================================
# Type Aliases and Enums
# ============================================================================

HouseType = Literal['All', 'Commons', 'Lords', 'Unassigned']
OriginatingHouseType = Literal['All', 'Commons', 'Lords']
BillSortOrder = Literal[
    'TitleAscending', 'TitleDescending', 'DateUpdatedAscending', 'DateUpdatedDescending'
]
BillTypeCategory = Literal['Public', 'Private', 'Hybrid']
AmendmentDecisionSearch = Literal[
    'All',
    'NoDecision',
    'Withdrawn',
    'Disagreed',
    'NotMoved',
    'Agreed',
    'QuestionProposed',
    'NotSelected',
    'WithdrawnBeforeDebate',
    'StoodPart',
    'NotStoodPart',
    'Preempted',
    'NotCalled',
    'NegativedOnDivision',
    'AgreedOnDivision',
]
AmendmentDecision = Literal[
    'NoDecision',
    'Withdrawn',
    'Disagreed',
    'NotMoved',
    'Agreed',
    'QuestionProposed',
    'NotSelected',
    'WithdrawnBeforeDebate',
    'StoodPart',
    'NotStoodPart',
    'Preempted',
    'NotCalled',
    'NegativedOnDivision',
    'AgreedOnDivision',
]
AmendmentType = Literal[
    'EditLongTitle',
    'EditBillBody',
    'AddClauseOrSchedule',
    'DeleteClauseOrSchedule',
]


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass(frozen=True)
class StageSummary:
    """Summary information about a bill stage."""

    id: int
    stage_id: int
    session_id: int
    description: str
    abbreviation: str | None
    house: str | None
    sort_order: int

    @property
    def description_lc(self) -> str:
        """Lowercase, stripped description for comparisons."""
        return self.description.casefold().strip()

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'StageSummary':
        return cls(
            id=data.get('id', 0),
            stage_id=data.get('stageId', 0),
            session_id=data.get('sessionId', 0),
            description=data.get('description', ''),
            abbreviation=data.get('abbreviation'),
            house=data.get('house'),
            sort_order=data.get('sortOrder', 0),
        )


@dataclass(frozen=True)
class Member:
    """Information about a member of Parliament."""

    member_id: int
    name: str | None
    party: str | None
    party_colour: str | None
    house: str | None
    member_photo: str | None
    member_page: str | None
    member_from: str | None
    sort_order: int
    is_lead: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'Member':
        return cls(
            member_id=data.get('memberId', 0),
            name=data.get('name'),
            party=data.get('party'),
            party_colour=data.get('partyColour'),
            house=data.get('house'),
            member_photo=data.get('memberPhoto'),
            member_page=data.get('memberPage'),
            member_from=data.get('memberFrom'),
            sort_order=data.get('sortOrder', 0),
            is_lead=data.get('isLead', False),
        )


@dataclass(frozen=True)
class Sponsor:
    """Bill sponsor information."""

    member: Member | None
    organisation: dict[str, Any] | None
    sort_order: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'Sponsor':
        member_data = data.get('member')
        member = Member.from_json(member_data) if member_data else None
        return cls(
            member=member,
            organisation=data.get('organisation'),
            sort_order=data.get('sortOrder', 0),
        )


@dataclass(frozen=True)
class BillAgent:
    """Agent information for private bills."""

    name: str | None
    address: str | None
    phone_no: str | None
    email: str | None
    website: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillAgent':
        return cls(
            name=data.get('name'),
            address=data.get('address'),
            phone_no=data.get('phoneNo'),
            email=data.get('email'),
            website=data.get('website'),
        )


@dataclass(frozen=True)
class BillSummary:
    """Summary information about a bill (from search results)."""

    bill_id: int
    short_title: str | None
    current_house: str | None
    last_update: datetime | None
    bill_type_id: int
    is_act: bool
    current_stage_description: str
    current_stage_id: int

    @property
    def last_update_formatted(self) -> str | None:
        # Add for convenience
        """Formatted last update date string."""
        if self.last_update:
            return self.last_update.strftime('%Y-%m-%d %H:%M')
        return None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillSummary':
        last_update_str = data.get('lastUpdate')
        last_update = None
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(
                    last_update_str.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        return cls(
            bill_id=data.get('billId', 0),
            short_title=data.get('shortTitle'),
            current_house=data.get('currentHouse'),
            last_update=last_update,
            bill_type_id=data.get('billTypeId', 0),
            is_act=data.get('isAct', False),
            current_stage_description=data.get('currentStage', {}).get(
                'description', ''
            ),
            current_stage_id=data.get('currentStage', {}).get('id', 0),
        )


@dataclass(frozen=True)
class Bill:
    """Detailed information about a bill."""

    bill_id: int
    short_title: str | None
    former_short_title: str | None
    current_house: str | None
    originating_house: str | None
    last_update: datetime | None
    bill_withdrawn: datetime | None
    is_defeated: bool
    bill_type_id: int
    introduced_session_id: int
    included_session_ids: list[int]
    is_act: bool
    current_stage: StageSummary | None
    long_title: str | None
    summary: str | None
    sponsors: list[Sponsor]
    promoters: list[dict[str, Any]]
    petitioning_period: str | None
    petition_information: str | None
    agent: BillAgent | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'Bill':
        last_update_str = data.get('lastUpdate')
        last_update = None
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(
                    last_update_str.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        bill_withdrawn_str = data.get('billWithdrawn')
        bill_withdrawn = None
        if bill_withdrawn_str:
            try:
                bill_withdrawn = datetime.fromisoformat(
                    bill_withdrawn_str.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        current_stage_data = data.get('currentStage')
        current_stage = (
            StageSummary.from_json(current_stage_data) if current_stage_data else None
        )

        sponsors_data = data.get('sponsors', [])
        sponsors = (
            [Sponsor.from_json(s) for s in sponsors_data] if sponsors_data else []
        )

        agent_data = data.get('agent')
        agent = BillAgent.from_json(agent_data) if agent_data else None

        return cls(
            bill_id=data.get('billId', 0),
            short_title=data.get('shortTitle'),
            former_short_title=data.get('formerShortTitle'),
            current_house=data.get('currentHouse'),
            originating_house=data.get('originatingHouse'),
            last_update=last_update,
            bill_withdrawn=bill_withdrawn,
            is_defeated=data.get('isDefeated', False),
            bill_type_id=data.get('billTypeId', 0),
            introduced_session_id=data.get('introducedSessionId', 0),
            included_session_ids=data.get('includedSessionIds', []),
            is_act=data.get('isAct', False),
            current_stage=current_stage,
            long_title=data.get('longTitle'),
            summary=data.get('summary'),
            sponsors=sponsors,
            promoters=data.get('promoters', []),
            petitioning_period=data.get('petitioningPeriod'),
            petition_information=data.get('petitionInformation'),
            agent=agent,
        )


@dataclass(frozen=True)
class Committee:
    """Committee information."""

    id: int
    name: str | None
    house: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'Committee':
        return cls(
            id=data.get('id', 0),
            name=data.get('name'),
            house=data.get('house'),
        )


@dataclass(frozen=True)
class BillStageSitting:
    """Information about a bill stage sitting."""

    id: int
    stage_id: int
    bill_stage_id: int
    bill_id: int
    date: datetime | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillStageSitting':
        date_str = data.get('date')
        date_val = None
        if date_str:
            try:
                date_val = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        return cls(
            id=data.get('id', 0),
            stage_id=data.get('stageId', 0),
            bill_stage_id=data.get('billStageId', 0),
            bill_id=data.get('billId', 0),
            date=date_val,
        )


@dataclass(frozen=True)
class BillStageDetails:
    """Detailed information about a bill stage."""

    id: int
    stage_id: int
    session_id: int
    description: str | None
    abbreviation: str | None
    house: str | None
    stage_sittings: list[BillStageSitting]
    sort_order: int
    committee: Committee | None
    next_stage_bill_stage_id: int | None
    previous_stage_bill_stage_id: int | None
    last_update: datetime | None
    has_motions: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillStageDetails':
        last_update_str = data.get('lastUpdate')
        last_update = None
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(
                    last_update_str.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        sittings_data = data.get('stageSittings', [])
        sittings = (
            [BillStageSitting.from_json(s) for s in sittings_data]
            if sittings_data
            else []
        )

        committee_data = data.get('committee')
        committee = Committee.from_json(committee_data) if committee_data else None

        return cls(
            id=data.get('id', 0),
            stage_id=data.get('stageId', 0),
            session_id=data.get('sessionId', 0),
            description=data.get('description'),
            abbreviation=data.get('abbreviation'),
            house=data.get('house'),
            stage_sittings=sittings,
            sort_order=data.get('sortOrder', 0),
            committee=committee,
            next_stage_bill_stage_id=data.get('nextStageBillStageId'),
            previous_stage_bill_stage_id=data.get('previousStageBillStageId'),
            last_update=last_update,
            has_motions=data.get('hasMotions', False),
        )


@dataclass(frozen=True)
class AmendmentLine:
    """A single line of amendment text."""

    text: str | None
    indentation: int
    hanging_indentation: str | None
    is_image: bool
    image_type: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'AmendmentLine':
        return cls(
            text=data.get('text'),
            indentation=data.get('indentation', 0),
            hanging_indentation=data.get('hangingIndentation'),
            is_image=data.get('isImage', False),
            image_type=data.get('imageType'),
        )


@dataclass(frozen=True)
class AmendmentMember:
    """Member information for amendment sponsors."""

    member_id: int
    name: str | None
    party: str | None
    party_colour: str | None
    house: str | None
    member_photo: str | None
    member_page: str | None
    member_from: str | None
    sort_order: int
    is_lead: bool

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'AmendmentMember':
        return cls(
            member_id=data.get('memberId', 0),
            name=data.get('name'),
            party=data.get('party'),
            party_colour=data.get('partyColour'),
            house=data.get('house'),
            member_photo=data.get('memberPhoto'),
            member_page=data.get('memberPage'),
            member_from=data.get('memberFrom'),
            sort_order=data.get('sortOrder', 0),
            is_lead=data.get('isLead', False),
        )


@dataclass(frozen=True)
class AmendmentDetail:
    """Detailed information about an amendment."""

    id: int
    bill_id: int
    bill_stage_id: int
    status_indicator: str | None
    decision: str | None
    decision_explanation: str | None
    sponsors: list[AmendmentMember]
    amendment_id: int
    amendment_type: str | None
    clause: int | None
    schedule: int | None
    page_number: str | None
    line_number: str | None
    amendment_position: str | None
    marshalled_list_text: str | None
    d_num: str | None
    amendment_lines: list[AmendmentLine]
    explanatory_text_prefix: str | None
    explanatory_text: str | None
    amendment_note: str | None
    amendment_location: str | None
    main_header: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'AmendmentDetail':
        sponsors_data = data.get('sponsors', [])
        sponsors = (
            [AmendmentMember.from_json(s) for s in sponsors_data]
            if sponsors_data
            else []
        )

        lines_data = data.get('amendmentLines', [])
        lines = (
            [AmendmentLine.from_json(line) for line in lines_data] if lines_data else []
        )

        return cls(
            id=data.get('id', 0),
            bill_id=data.get('billId', 0),
            bill_stage_id=data.get('billStageId', 0),
            status_indicator=data.get('statusIndicator'),
            decision=data.get('decision'),
            decision_explanation=data.get('decisionExplanation'),
            sponsors=sponsors,
            amendment_id=data.get('amendmentId', 0),
            amendment_type=data.get('amendmentType'),
            clause=data.get('clause'),
            schedule=data.get('schedule'),
            page_number=data.get('pageNumber'),
            line_number=data.get('lineNumber'),
            amendment_position=data.get('amendmentPosition'),
            marshalled_list_text=data.get('marshalledListText'),
            d_num=data.get('dNum'),
            amendment_lines=lines,
            explanatory_text_prefix=data.get('explanatoryTextPrefix'),
            explanatory_text=data.get('explanatoryText'),
            amendment_note=data.get('amendmentNote'),
            amendment_location=data.get('amendmentLocation'),
            main_header=data.get('mainHeader'),
        )


@dataclass(frozen=True)
class AmendmentSearchItem:
    """Summary information about an amendment (from search results)."""

    id: int
    bill_id: int
    bill_stage_id: int
    status_indicator: str | None
    decision: str | None
    decision_explanation: str | None
    sponsors: list[AmendmentMember]
    amendment_id: int
    amendment_type: str | None
    clause: int | None
    schedule: int | None
    page_number: str | None
    line_number: str | None
    amendment_position: str | None
    marshalled_list_text: str | None
    d_num: str | None
    summary_text: list[str]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'AmendmentSearchItem':
        sponsors_data = data.get('sponsors', [])
        sponsors = (
            [AmendmentMember.from_json(s) for s in sponsors_data]
            if sponsors_data
            else []
        )

        return cls(
            id=data.get('id', 0),
            bill_id=data.get('billId', 0),
            bill_stage_id=data.get('billStageId', 0),
            status_indicator=data.get('statusIndicator'),
            decision=data.get('decision'),
            decision_explanation=data.get('decisionExplanation'),
            sponsors=sponsors,
            amendment_id=data.get('amendmentId', 0),
            amendment_type=data.get('amendmentType'),
            clause=data.get('clause'),
            schedule=data.get('schedule'),
            page_number=data.get('pageNumber'),
            line_number=data.get('lineNumber'),
            amendment_position=data.get('amendmentPosition'),
            marshalled_list_text=data.get('marshalledListText'),
            d_num=data.get('dNum'),
            summary_text=data.get('summaryText', []),
        )


@dataclass(frozen=True)
class PublicationType:
    """Publication type information."""

    id: int
    name: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'PublicationType':
        return cls(
            id=data.get('id', 0),
            name=data.get('name'),
        )


@dataclass(frozen=True)
class PublicationLink:
    """Link to a publication document."""

    title: str | None
    url: str | None
    content_type: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'PublicationLink':
        return cls(
            title=data.get('title'),
            url=data.get('url'),
            content_type=data.get('contentType'),
        )


@dataclass(frozen=True)
class PublicationDocument:
    """Publication document metadata."""

    id: int
    title: str | None
    content_type: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'PublicationDocument':
        return cls(
            id=data.get('id', 0),
            title=data.get('title'),
            content_type=data.get('contentType'),
        )


@dataclass(frozen=True)
class BillPublication:
    """Information about a bill publication."""

    id: int
    title: str | None
    publication_type: PublicationType | None
    display_date: datetime | None
    links: list[PublicationLink]
    files: list[PublicationDocument]
    house: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillPublication':
        display_date_str = data.get('displayDate')
        display_date = None
        if display_date_str:
            try:
                display_date = datetime.fromisoformat(
                    display_date_str.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        pub_type_data = data.get('publicationType')
        pub_type = PublicationType.from_json(pub_type_data) if pub_type_data else None

        links_data = data.get('links', [])
        links = (
            [PublicationLink.from_json(link) for link in links_data]
            if links_data
            else []
        )

        files_data = data.get('files', [])
        files = (
            [PublicationDocument.from_json(f) for f in files_data] if files_data else []
        )

        return cls(
            id=data.get('id', 0),
            title=data.get('title'),
            publication_type=pub_type,
            display_date=display_date,
            links=links,
            files=files,
            house=data.get('house'),
        )


@dataclass(frozen=True)
class BillPublicationList:
    """List of publications for a bill."""

    bill_id: int
    publications: list[BillPublication]

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillPublicationList':
        pubs_data = data.get('publications', [])
        pubs = [BillPublication.from_json(p) for p in pubs_data] if pubs_data else []

        return cls(
            bill_id=data.get('billId', 0),
            publications=pubs,
        )


@dataclass(frozen=True)
class BillType:
    """Information about a bill type."""

    id: int
    name: str | None
    description: str | None
    category: str | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'BillType':
        return cls(
            id=data.get('id', 0),
            name=data.get('name'),
            description=data.get('description'),
            category=data.get('category'),
        )


@dataclass(frozen=True)
class StageReference:
    """Reference information about a stage."""

    id: int
    name: str | None
    house: str | None
    sort_order: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> 'StageReference':
        return cls(
            id=data.get('id', 0),
            name=data.get('name'),
            house=data.get('house'),
            sort_order=data.get('sortOrder', 0),
        )


# ============================================================================
# Async Client
# ============================================================================


class BillsApiClient:
    """Async client for the UK Parliament Bills API.

    This client uses httpx.AsyncClient for efficient concurrent requests.
    Use as an async context manager to ensure proper resource cleanup.

    Example:
        async with BillsApiClient() as client:
            bills = await client.get_bills(current_house='Commons')
    """

    def __init__(self, base_url: str = BASE_URL):
        """Initialize the Bills API client.

        Args:
            base_url: Base URL for the Bills API
        """
        self.base_url = base_url
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=5.0),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,
            ),
            http2=True,
        )

    async def close(self) -> None:
        """Close the HTTP session."""
        await self.session.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _build_params(self, **kwargs) -> dict[str, Any]:
        """Build query parameters, excluding None values."""
        params = {}
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, bool):
                    params[key] = str(value).lower()
                elif isinstance(value, list):
                    params[key] = value
                else:
                    params[key] = value
        return params

    async def _make_request(
        self, url: str, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Make an HTTP request with automatic retry on timeout/network errors.

        Retries once on timeout or network errors, then raises the exception.

        Args:
            url: The full URL to request
            params: Query parameters to include

        Returns:
            httpx.Response: The HTTP response object

        Raises:
            httpx.TimeoutException: If request times out after retries
            httpx.NetworkError: If network error occurs after retries
            httpx.HTTPStatusError: If response has error status code
        """
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                response = await self.session.get(url, params=params)
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == max_retries:
                    logger.error(
                        f'Request failed after {max_retries + 1} attempts: {url}'
                    )
                    raise
                if attempt == max_retries - 1:
                    logger.warning(
                        f'Request timeout/network error '
                        f'(attempt {attempt + 1}/{max_retries + 1}), final retry...'
                    )
        # Should never reach here due to raise in exception handler
        raise RuntimeError('Unexpected code path in _make_request')

    # ========================================================================
    # BILLS
    # ========================================================================

    async def get_bills_raw(
        self,
        search_term: str | None = None,
        session: int | None = None,
        current_house: HouseType | None = None,
        originating_house: OriginatingHouseType | None = None,
        member_id: int | None = None,
        department_id: int | None = None,
        bill_stage: list[int] | None = None,
        bill_stages_excluded: list[int] | None = None,
        is_defeated: bool | None = None,
        is_withdrawn: bool | None = None,
        bill_type: list[int] | None = None,
        sort_order: BillSortOrder | None = None,
        bill_ids: list[int] | None = None,
        is_in_amendable_stage: bool | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> httpx.Response:
        """Returns a list of Bills (raw response).

        Args:
            search_term: Search term to filter bills
            session: Session ID to filter bills
            current_house: Current house (All, Commons, Lords, Unassigned)
            originating_house: Originating house (All, Commons, Lords)
            member_id: Filter by member ID
            department_id: Filter by department ID
            bill_stage: List of bill stage IDs to include
            bill_stages_excluded: List of bill stage IDs to exclude
            is_defeated: Include defeated bills
            is_withdrawn: Include withdrawn bills
            bill_type: List of bill type IDs
            sort_order: Sort order for results
            bill_ids: List of specific bill IDs to retrieve
            is_in_amendable_stage: Filter by amendable stage
            skip: Number of results to skip (pagination)
            take: Number of results to return (pagination)

        Returns:
            httpx.Response: Raw HTTP response
        """
        params = self._build_params(
            SearchTerm=search_term,
            Session=session,
            CurrentHouse=current_house,
            OriginatingHouse=originating_house,
            MemberId=member_id,
            DepartmentId=department_id,
            BillStage=bill_stage,
            BillStagesExcluded=bill_stages_excluded,
            IsDefeated=is_defeated,
            IsWithdrawn=is_withdrawn,
            BillType=bill_type,
            SortOrder=sort_order,
            BillIds=bill_ids,
            IsInAmendableStage=is_in_amendable_stage,
            Skip=skip,
            Take=take,
        )

        return await self._make_request(f'{self.base_url}/Bills', params=params)

    async def get_bills_json(
        self,
        search_term: str | None = None,
        session: int | None = None,
        current_house: HouseType | None = None,
        originating_house: OriginatingHouseType | None = None,
        member_id: int | None = None,
        department_id: int | None = None,
        bill_stage: list[int] | None = None,
        bill_stages_excluded: list[int] | None = None,
        is_defeated: bool | None = None,
        is_withdrawn: bool | None = None,
        bill_type: list[int] | None = None,
        sort_order: BillSortOrder | None = None,
        bill_ids: list[int] | None = None,
        is_in_amendable_stage: bool | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> dict:
        """Returns a list of Bills (JSON dict).

        Args:
            Same as get_bills_raw

        Returns:
            dict: Bill summary search results
        """
        response = await self.get_bills_raw(
            search_term=search_term,
            session=session,
            current_house=current_house,
            originating_house=originating_house,
            member_id=member_id,
            department_id=department_id,
            bill_stage=bill_stage,
            bill_stages_excluded=bill_stages_excluded,
            is_defeated=is_defeated,
            is_withdrawn=is_withdrawn,
            bill_type=bill_type,
            sort_order=sort_order,
            bill_ids=bill_ids,
            is_in_amendable_stage=is_in_amendable_stage,
            skip=skip,
            take=take,
        )
        return response.json()

    async def get_bills(
        self,
        search_term: str | None = None,
        session: int | None = None,
        current_house: HouseType | None = None,
        originating_house: OriginatingHouseType | None = None,
        member_id: int | None = None,
        department_id: int | None = None,
        bill_stage: list[int] | None = None,
        bill_stages_excluded: list[int] | None = None,
        is_defeated: bool | None = None,
        is_withdrawn: bool | None = None,
        bill_type: list[int] | None = None,
        sort_order: BillSortOrder | None = None,
        bill_ids: list[int] | None = None,
        is_in_amendable_stage: bool | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> list[BillSummary]:
        """Returns a list of Bills (typed dataclasses).

        Args:
            Same as get_bills_raw

        Returns:
            list[BillSummary]: List of bill summaries
        """
        data = await self.get_bills_json(
            search_term=search_term,
            session=session,
            current_house=current_house,
            originating_house=originating_house,
            member_id=member_id,
            department_id=department_id,
            bill_stage=bill_stage,
            bill_stages_excluded=bill_stages_excluded,
            is_defeated=is_defeated,
            is_withdrawn=is_withdrawn,
            bill_type=bill_type,
            sort_order=sort_order,
            bill_ids=bill_ids,
            is_in_amendable_stage=is_in_amendable_stage,
            skip=skip,
            take=take,
        )
        items = data.get('items', [])
        return [BillSummary.from_json(item) for item in items]

    async def get_bill_raw(self, bill_id: int) -> httpx.Response:
        """Return a Bill by ID (raw response).

        Args:
            bill_id: Bill ID

        Returns:
            httpx.Response: Raw HTTP response
        """
        return await self._make_request(f'{self.base_url}/Bills/{bill_id}')

    async def get_bill_json(self, bill_id: int) -> dict:
        """Return a Bill by ID (JSON dict).

        Args:
            bill_id: Bill ID

        Returns:
            dict: Bill details
        """
        response = await self.get_bill_raw(bill_id)
        return response.json()

    async def get_bill(self, bill_id: int) -> Bill:
        """Return a Bill by ID (typed dataclass).

        Args:
            bill_id: Bill ID

        Returns:
            Bill: Bill details
        """
        data = await self.get_bill_json(bill_id)
        return Bill.from_json(data)

    async def get_bill_stages_raw(
        self,
        bill_id: int,
        skip: int | None = None,
        take: int | None = None,
    ) -> httpx.Response:
        """Returns all Bill stages (raw response).

        Args:
            bill_id: Bill ID
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            httpx.Response: Raw HTTP response
        """
        params = self._build_params(Skip=skip, Take=take)
        return await self._make_request(
            f'{self.base_url}/Bills/{bill_id}/Stages', params=params
        )

    async def get_bill_stages_json(
        self,
        bill_id: int,
        skip: int | None = None,
        take: int | None = None,
    ) -> dict:
        """Returns all Bill stages (JSON dict).

        Args:
            bill_id: Bill ID
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            dict: Stage summary search results
        """
        response = await self.get_bill_stages_raw(bill_id, skip=skip, take=take)
        return response.json()

    async def get_bill_stages(
        self,
        bill_id: int,
        skip: int | None = None,
        take: int | None = None,
    ) -> list[StageSummary]:
        """Returns all Bill stages (typed dataclasses).

        Args:
            bill_id: Bill ID
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            list[StageSummary]: List of stage summaries
        """
        data = await self.get_bill_stages_json(bill_id, skip=skip, take=take)
        items = data.get('items', [])
        return [StageSummary.from_json(item) for item in items]

    async def get_bill_stage_details_raw(
        self, bill_id: int, bill_stage_id: int
    ) -> httpx.Response:
        """Returns a Bill stage (raw response).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID

        Returns:
            httpx.Response: Raw HTTP response
        """
        return await self._make_request(
            f'{self.base_url}/Bills/{bill_id}/Stages/{bill_stage_id}'
        )

    async def get_bill_stage_details_json(
        self, bill_id: int, bill_stage_id: int
    ) -> dict:
        """Returns a Bill stage (JSON dict).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID

        Returns:
            dict: Bill stage details
        """
        response = await self.get_bill_stage_details_raw(bill_id, bill_stage_id)
        return response.json()

    async def get_bill_stage_details(
        self, bill_id: int, bill_stage_id: int
    ) -> BillStageDetails:
        """Returns a Bill stage (typed dataclass).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID

        Returns:
            BillStageDetails: Bill stage details
        """
        data = await self.get_bill_stage_details_json(bill_id, bill_stage_id)
        return BillStageDetails.from_json(data)

    # ========================================================================
    # AMENDMENTS
    # ========================================================================

    async def get_amendments_raw(
        self,
        bill_id: int,
        bill_stage_id: int,
        search_term: str | None = None,
        amendment_number: str | None = None,
        decision: AmendmentDecisionSearch | None = None,
        member_id: int | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> httpx.Response:
        """Returns a list of amendments (raw response).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID
            search_term: Search term to filter amendments
            amendment_number: Specific amendment number
            decision: Amendment decision status
            member_id: Filter by member ID
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            httpx.Response: Raw HTTP response
        """
        params = self._build_params(
            SearchTerm=search_term,
            AmendmentNumber=amendment_number,
            Decision=decision,
            MemberId=member_id,
            Skip=skip,
            Take=take,
        )

        return await self._make_request(
            f'{self.base_url}/Bills/{bill_id}/Stages/{bill_stage_id}/Amendments',
            params=params,
        )

    async def get_amendments_json(
        self,
        bill_id: int,
        bill_stage_id: int,
        search_term: str | None = None,
        amendment_number: str | None = None,
        decision: AmendmentDecisionSearch | None = None,
        member_id: int | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> dict:
        """Returns a list of amendments (JSON dict).

        Args:
            Same as get_amendments_raw

        Returns:
            dict: Amendment search results
        """
        response = await self.get_amendments_raw(
            bill_id=bill_id,
            bill_stage_id=bill_stage_id,
            search_term=search_term,
            amendment_number=amendment_number,
            decision=decision,
            member_id=member_id,
            skip=skip,
            take=take,
        )
        return response.json()

    async def get_amendments(
        self,
        bill_id: int,
        bill_stage_id: int,
        search_term: str | None = None,
        amendment_number: str | None = None,
        decision: AmendmentDecisionSearch | None = None,
        member_id: int | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> list[AmendmentSearchItem]:
        """Returns a list of amendments (typed dataclasses).

        Args:
            Same as get_amendments_raw

        Returns:
            list[AmendmentSearchItem]: List of amendment summaries
        """
        data = await self.get_amendments_json(
            bill_id=bill_id,
            bill_stage_id=bill_stage_id,
            search_term=search_term,
            amendment_number=amendment_number,
            decision=decision,
            member_id=member_id,
            skip=skip,
            take=take,
        )
        items = data.get('items', [])
        return [AmendmentSearchItem.from_json(item) for item in items]

    async def get_amendment_raw(
        self, bill_id: int, bill_stage_id: int, amendment_id: int
    ) -> httpx.Response:
        """Returns an amendment (raw response).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID
            amendment_id: Amendment ID

        Returns:
            httpx.Response: Raw HTTP response
        """
        return await self._make_request(
            f'{self.base_url}/Bills/{bill_id}/Stages/{bill_stage_id}/Amendments/{amendment_id}'
        )

    async def get_amendment_json(
        self, bill_id: int, bill_stage_id: int, amendment_id: int
    ) -> dict:
        """Returns an amendment (JSON dict).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID
            amendment_id: Amendment ID

        Returns:
            dict: Amendment details
        """
        response = await self.get_amendment_raw(bill_id, bill_stage_id, amendment_id)
        return response.json()

    async def get_amendment(
        self, bill_id: int, bill_stage_id: int, amendment_id: int
    ) -> AmendmentDetail:
        """Returns an amendment (typed dataclass).

        Args:
            bill_id: Bill ID
            bill_stage_id: Bill stage ID
            amendment_id: Amendment ID

        Returns:
            AmendmentDetail: Amendment details
        """
        data = await self.get_amendment_json(bill_id, bill_stage_id, amendment_id)
        return AmendmentDetail.from_json(data)

    # ========================================================================
    # PUBLICATIONS
    # ========================================================================

    async def get_bill_publications_raw(self, bill_id: int) -> httpx.Response:
        """Return a list of Bill publications (raw response).

        Args:
            bill_id: Bill ID

        Returns:
            httpx.Response: Raw HTTP response
        """
        return await self._make_request(f'{self.base_url}/Bills/{bill_id}/Publications')

    async def get_bill_publications_json(self, bill_id: int) -> dict:
        """Return a list of Bill publications (JSON dict).

        Args:
            bill_id: Bill ID

        Returns:
            dict: Bill publication list
        """
        response = await self.get_bill_publications_raw(bill_id)
        return response.json()

    async def get_bill_publications(self, bill_id: int) -> BillPublicationList:
        """Return a list of Bill publications (typed dataclass).

        Args:
            bill_id: Bill ID

        Returns:
            BillPublicationList: Bill publication list
        """
        data = await self.get_bill_publications_json(bill_id)
        return BillPublicationList.from_json(data)

    async def get_bill_stage_publications_raw(
        self, bill_id: int, stage_id: int
    ) -> httpx.Response:
        """Return a list of Bill stage publications (raw response).

        Args:
            bill_id: Bill ID
            stage_id: Stage ID

        Returns:
            httpx.Response: Raw HTTP response
        """
        return await self._make_request(
            f'{self.base_url}/Bills/{bill_id}/Stages/{stage_id}/Publications'
        )

    async def get_bill_stage_publications_json(
        self, bill_id: int, stage_id: int
    ) -> dict:
        """Return a list of Bill stage publications (JSON dict).

        Args:
            bill_id: Bill ID
            stage_id: Stage ID

        Returns:
            dict: Bill stage publication list
        """
        response = await self.get_bill_stage_publications_raw(bill_id, stage_id)
        return response.json()

    # ========================================================================
    # BILL TYPES
    # ========================================================================

    async def get_publication_types_raw(
        self,
        skip: int | None = None,
        take: int | None = None,
    ) -> httpx.Response:
        """Returns a list of publication types (raw response).

        Args:
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            httpx.Response: Raw HTTP response
        """
        params = self._build_params(Skip=skip, Take=take)
        return await self._make_request(
            f'{self.base_url}/PublicationTypes', params=params
        )

    async def get_publication_types_json(
        self,
        skip: int | None = None,
        take: int | None = None,
    ) -> dict:
        """Returns a list of publication types (JSON dict).

        Args:
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            dict: Publication type search results
        """
        response = await self.get_publication_types_raw(skip=skip, take=take)
        return response.json()

    async def get_publication_types(
        self,
        skip: int | None = None,
        take: int | None = None,
    ) -> list[PublicationType]:
        """Returns a list of publication types (typed dataclasses).

        Args:
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            list[PublicationType]: List of publication types
        """
        data = await self.get_publication_types_json(skip=skip, take=take)
        items = data.get('items', [])
        return [PublicationType.from_json(item) for item in items]

    async def get_bill_types_raw(
        self,
        category: BillTypeCategory | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> httpx.Response:
        """Returns a list of Bill types (raw response).

        Args:
            category: Bill type category (Public, Private, Hybrid)
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            httpx.Response: Raw HTTP response
        """
        params = self._build_params(Category=category, Skip=skip, Take=take)
        return await self._make_request(f'{self.base_url}/BillTypes', params=params)

    async def get_bill_types_json(
        self,
        category: BillTypeCategory | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> dict:
        """Returns a list of Bill types (JSON dict).

        Args:
            category: Bill type category (Public, Private, Hybrid)
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            dict: Bill type search results
        """
        response = await self.get_bill_types_raw(
            category=category, skip=skip, take=take
        )
        return response.json()

    async def get_bill_types(
        self,
        category: BillTypeCategory | None = None,
        skip: int | None = None,
        take: int | None = None,
    ) -> list[BillType]:
        """Returns a list of Bill types (typed dataclasses).

        Args:
            category: Bill type category (Public, Private, Hybrid)
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            list[BillType]: List of bill types
        """
        data = await self.get_bill_types_json(category=category, skip=skip, take=take)
        items = data.get('items', [])
        return [BillType.from_json(item) for item in items]

    # ========================================================================
    # STAGES
    # ========================================================================

    async def get_stages_raw(
        self,
        skip: int | None = None,
        take: int | None = None,
    ) -> httpx.Response:
        """Returns a list of Bill stages (raw response).

        Args:
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            httpx.Response: Raw HTTP response
        """
        params = self._build_params(Skip=skip, Take=take)
        return await self._make_request(f'{self.base_url}/Stages', params=params)

    async def get_stages_json(
        self,
        skip: int | None = None,
        take: int | None = None,
    ) -> dict:
        """Returns a list of Bill stages (JSON dict).

        Args:
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            dict: Stage reference search results
        """
        response = await self.get_stages_raw(skip=skip, take=take)
        return response.json()

    async def get_stages(
        self,
        skip: int | None = None,
        take: int | None = None,
    ) -> list[StageReference]:
        """Returns a list of Bill stages (typed dataclasses).

        Args:
            skip: Number of results to skip
            take: Number of results to return

        Returns:
            list[StageReference]: List of stage references
        """
        data = await self.get_stages_json(skip=skip, take=take)
        items = data.get('items', [])
        return [StageReference.from_json(item) for item in items]


# Helpers
async def print_stages() -> None:
    async with BillsApiClient() as client:
        response = await client.get_stages()

    for stage in response:
        print(f'House: {stage.house}   Stage name: {stage.name}')

    # As at Saturday, 24  January 2026 This print the following stages:

    # House: Commons   Stage name: Committee stage (re-committed clauses and schedules)
    # House: Commons   Stage name: Committee of the whole House
    # House: Commons   Stage name: Power of public bill committee to send for persons, papers and records
    # House: Commons   Stage name: 1st reading
    # House: Commons   Stage name: 2nd reading
    # House: Commons   Stage name: Guillotine motion
    # House: Commons   Stage name: Second House Examination
    # House: Commons   Stage name: Second reading committee
    # House: Commons   Stage name: Programme motion
    # House: Commons   Stage name: Money resolution
    # House: Commons   Stage name: Allocation of time motion
    # House: Commons   Stage name: Order of Commitment discharged
    # House: Commons   Stage name: Committee stage
    # House: Commons   Stage name: Select Committee stage
    # House: Commons   Stage name: Ways and Means resolution
    # House: Commons   Stage name: Report stage
    # House: Commons   Stage name: 3rd reading
    # House: Commons   Stage name: Legislative Grand Committee
    # House: Commons   Stage name: Reconsideration
    # House: Commons   Stage name: Consideration of Lords amendments
    # House: Commons   Stage name: Consequential consideration
    # House: Commons   Stage name: Carry-over motion
    # House: Commons   Stage name: Consideration of Lords message
    # House: Commons   Stage name: Motion to revive Bill
    # House: Commons   Stage name: Motion to suspend Bill till next session considered
    # House: Commons   Stage name: Bill reintroduced
    # House: Commons   Stage name: Motion to suspend Bill till next session approved
    # House: Commons   Stage name: Instruction
    # House: Commons   Stage name: Committal (to a Select Committee)
    # House: Lords   Stage name: Lords Special Public Bill Committee
    # House: Lords   Stage name: 1st reading
    # House: Lords   Stage name: 2nd reading
    # House: Lords   Stage name: Committee stage
    # House: Lords   Stage name: Report stage
    # House: Lords   Stage name: 3rd reading


if __name__ == '__main__':
    asyncio.run(print_stages())
