import asyncio
from sqlalchemy import text
from app.db.session import engine

async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))
        tables = [row[0] for row in result]
        for table in tables:
            print(table)

asyncio.run(check_tables())
