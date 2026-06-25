# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings

Database_url = settings.DATABASE_URL

engine = create_async_engine(Database_url,  echo=False,pool_size=10, max_overflow=20)
#pool_size=10, max_overflow=20 means that the connection pool will maintain a maximum of 10 connections, and if all of those are in use, it can create up to 20 additional connections (for a total of 30) to handle bursts of traffic. Once the demand decreases, the extra connections will be closed.
AsyncSessionLocal = async_sessionmaker(bind=engine, class_ = AsyncSession, expire_on_commit=False)
# Push changes to DB buffer (Does NOT commit)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session