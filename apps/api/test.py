import asyncio
from app.core.database import SessionLocal
from app.services.project_service import project_service

async def main():
    async with SessionLocal() as db:
        projects = await project_service.get_projects(db)
        print("Projects:", len(projects))
        if projects:
            print("Status:", projects[0].status)
            print("Reason:", projects[0].status_reason)

if __name__ == "__main__":
    asyncio.run(main())
