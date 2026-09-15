import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from crm.contacts import service as contacts_service
from crm.contacts.models import Contact
from crm.contacts.schemas import ContactCreate
from crm.opportunities import service
from crm.opportunities.models import OpportunityStage, OpportunityStatus
from crm.opportunities.schemas import OpportunityCreate, OpportunityUpdate


async def _make_contact(session: AsyncSession, name: str = "Ada Lovelace") -> Contact:
    return await contacts_service.create_contact(session, ContactCreate(name=name))


async def test_create_opportunity_persists_the_given_fields(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    opportunity = await service.create_opportunity(
        session,
        OpportunityCreate(contact_id=contact.id, title="itela support contract", owner="Sam"),
    )

    assert opportunity.id is not None
    assert opportunity.contact_id == contact.id
    assert opportunity.title == "itela support contract"
    assert opportunity.owner == "Sam"


async def test_create_opportunity_rejects_an_invalid_contact_id(session: AsyncSession) -> None:
    with pytest.raises(service.OpportunityValidationError):
        await service.create_opportunity(
            session, OpportunityCreate(contact_id=999999, title="Ghost deal", owner="Sam")
        )


async def test_get_opportunity_returns_the_matching_opportunity(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    created = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    fetched = await service.get_opportunity(session, created.id)

    assert fetched.id == created.id


async def test_get_opportunity_raises_for_a_missing_id(session: AsyncSession) -> None:
    with pytest.raises(service.OpportunityNotFoundError):
        await service.get_opportunity(session, 999999)


async def test_list_open_by_stage_always_returns_all_five_stage_keys(
    session: AsyncSession,
) -> None:
    board = await service.list_open_by_stage(session)

    assert set(board.keys()) == set(OpportunityStage)
    assert board[OpportunityStage.POC] == []


async def test_list_open_by_stage_excludes_closed_opportunities(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    open_deal = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Open deal", owner="Sam")
    )
    lost_deal = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Lost deal", owner="Sam")
    )
    await service.update_opportunity(
        session, lost_deal.id, OpportunityUpdate(status=OpportunityStatus.LOST)
    )

    board = await service.list_open_by_stage(session)

    ids_on_board = {opp.id for opps in board.values() for opp in opps}
    assert ids_on_board == {open_deal.id}


async def test_list_for_contact_returns_all_statuses(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    open_deal = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Open deal", owner="Sam")
    )
    closed_deal = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Closed deal", owner="Sam")
    )
    await service.update_opportunity(
        session, closed_deal.id, OpportunityUpdate(status=OpportunityStatus.WON)
    )

    opportunities = await service.list_for_contact(session, contact.id)

    ids = {opp.id for opp in opportunities}
    assert ids == {open_deal.id, closed_deal.id}


async def test_update_opportunity_sets_closed_at_and_keeps_stage_when_status_leaves_open(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session,
        OpportunityCreate(
            contact_id=contact.id,
            title="Deal",
            owner="Sam",
            stage=OpportunityStage.PROPOSAL,
        ),
    )
    assert opportunity.closed_at is None

    updated = await service.update_opportunity(
        session, opportunity.id, OpportunityUpdate(status=OpportunityStatus.WON)
    )

    assert updated.closed_at is not None
    assert updated.stage == OpportunityStage.PROPOSAL
