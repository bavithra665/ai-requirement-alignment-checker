from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.system_service import get_system_health
from app.services.demo_service import seed_demo_workspace

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(deps.get_db)):
    """
    Get system health status for Database, ChromaDB, Groq, Jira, and Github.
    """
    health_status = await get_system_health(db)
    return health_status


@router.post("/demo/seed")
async def demo_seed(db: AsyncSession = Depends(deps.get_db)):
    """
    Seed the database with a demonstration workspace (E-Commerce Customer Portal).
    """
    try:
        result = await seed_demo_workspace(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
