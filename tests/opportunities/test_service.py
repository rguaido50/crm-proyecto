from decimal import Decimal

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

    assert [opp.id for opp in opportunities] == [open_deal.id, closed_deal.id]


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


async def test_update_opportunity_clears_closed_at_when_reopened(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )
    closed = await service.update_opportunity(
        session, opportunity.id, OpportunityUpdate(status=OpportunityStatus.LOST)
    )
    assert closed.closed_at is not None

    reopened = await service.update_opportunity(
        session, opportunity.id, OpportunityUpdate(status=OpportunityStatus.OPEN)
    )

    assert reopened.closed_at is None


async def test_update_opportunity_keeps_the_original_closed_at_on_a_closed_to_closed_change(
    session: AsyncSession,
) -> None:
    # CONTEXT.md: closed_at records "the moment [the opportunity] closed" — the first
    # time it left OPEN. A later closed-to-closed change (WON<->LOST) isn't a new closing.
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )
    lost = await service.update_opportunity(
        session, opportunity.id, OpportunityUpdate(status=OpportunityStatus.LOST)
    )
    assert lost.closed_at is not None

    won = await service.update_opportunity(
        session, opportunity.id, OpportunityUpdate(status=OpportunityStatus.WON)
    )

    assert won.closed_at == lost.closed_at


async def test_create_opportunity_rejects_a_blank_title(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    with pytest.raises(service.OpportunityValidationError):
        await service.create_opportunity(
            session, OpportunityCreate(contact_id=contact.id, title="   ", owner="Sam")
        )


async def test_update_opportunity_rejects_a_blank_owner(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    with pytest.raises(service.OpportunityValidationError):
        await service.update_opportunity(session, opportunity.id, OpportunityUpdate(owner="  "))


async def test_update_opportunity_trims_the_owner_field(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    updated = await service.update_opportunity(
        session, opportunity.id, OpportunityUpdate(owner="  Alex  ")
    )

    assert updated.owner == "Alex"


async def test_create_opportunity_rejects_a_value_usd_that_overflows_the_column(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)

    with pytest.raises(service.OpportunityValidationError):
        await service.create_opportunity(
            session,
            OpportunityCreate(
                contact_id=contact.id,
                title="Deal",
                owner="Sam",
                value_usd=Decimal(99999999999999),
            ),
        )


async def test_update_opportunity_rejects_a_value_usd_that_overflows_the_column(
    session: AsyncSession,
) -> None:
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    with pytest.raises(service.OpportunityValidationError, match="^invalid opportunity data$"):
        await service.update_opportunity(
            session, opportunity.id, OpportunityUpdate(value_usd=Decimal(99999999999999))
        )


async def test_create_opportunity_rejects_a_negative_value_usd(session: AsyncSession) -> None:
    contact = await _make_contact(session)

    with pytest.raises(service.OpportunityValidationError):
        await service.create_opportunity(
            session,
            OpportunityCreate(
                contact_id=contact.id, title="Deal", owner="Sam", value_usd=Decimal(-1)
            ),
        )


async def test_update_opportunity_rejects_a_negative_value_usd(session: AsyncSession) -> None:
    contact = await _make_contact(session)
    opportunity = await service.create_opportunity(
        session, OpportunityCreate(contact_id=contact.id, title="Deal", owner="Sam")
    )

    with pytest.raises(service.OpportunityValidationError):
        await service.update_opportunity(
            session, opportunity.id, OpportunityUpdate(value_usd=Decimal(-1))
        )
