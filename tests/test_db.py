from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def test_session_executes_a_query_against_real_postgres(session: AsyncSession) -> None:
    result = await session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1
