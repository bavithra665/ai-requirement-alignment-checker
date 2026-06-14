from datetime import datetime, timezone
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.chroma_service import get_chroma_client
from app.services.ai_service import ai_service
from app.services.jira_service import jira_service
from app.services.github_service import github_service

async def get_system_health(db: AsyncSession) -> dict:
    """
    Returns the health status of DB, ChromaDB, Groq, Jira, Github.
    Statuses are returned as dictionaries with state and timestamp.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    health_status = {
        "timestamp": timestamp,
        "services": {}
    }

    # 1. Check DB
    try:
        await db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {"status": "Green", "message": "Connected"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "Red", "message": str(e)}

    # 2. Check ChromaDB
    try:
        client = get_chroma_client()
        client.heartbeat() # This checks if client is alive
        health_status["services"]["chromadb"] = {"status": "Green", "message": "Connected"}
    except Exception as e:
        health_status["services"]["chromadb"] = {"status": "Red", "message": str(e)}

    # 3. Check Groq
    if ai_service.client:
        health_status["services"]["groq"] = {"status": "Green", "message": "Configured"}
    else:
        health_status["services"]["groq"] = {"status": "Amber", "message": "Not configured"}

    # 4. Check Jira
    try:
        jira_status = jira_service.get_status()
        if jira_status.get("configured", False):
            health_status["services"]["jira"] = {"status": "Green", "message": "Configured"}
        else:
            health_status["services"]["jira"] = {"status": "Amber", "message": "Not configured"}
    except Exception as e:
        health_status["services"]["jira"] = {"status": "Red", "message": str(e)}

    # 5. Check Github
    try:
        github_status = github_service.get_status()
        if github_status.get("configured", False):
            health_status["services"]["github"] = {"status": "Green", "message": "Configured"}
        else:
            health_status["services"]["github"] = {"status": "Amber", "message": "Not configured"}
    except Exception as e:
        health_status["services"]["github"] = {"status": "Red", "message": str(e)}

    return health_status
