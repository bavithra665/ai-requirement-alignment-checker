import asyncio
from app.core.database import SessionLocal
from app.services.project_service import project_service

async def main():
    async with SessionLocal() as db:
        print(await project_service.get_projects(db=db))

asyncio.run(main())
