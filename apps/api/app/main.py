from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, projects, upload, requirements, jira, github, alignment, reports, system, notifications, client

tags_metadata = [
    {"name": "system", "description": "System health and demo workspace seeding endpoints."},
    {"name": "auth", "description": "Authentication and user management."},
    {"name": "projects", "description": "Manage workspaces and projects."},
    {"name": "upload", "description": "Document parsing and upload for requirements."},
    {"name": "requirements", "description": "Requirement baselining and tracking."},
    {"name": "jira", "description": "Sync and manage Jira stories."},
    {"name": "github", "description": "Sync and manage GitHub pull requests and code artifacts."},
    {"name": "alignment", "description": "Run AI-powered alignment across artifacts."},
    {"name": "reports", "description": "Retrieve mismatch reports and alignment summaries."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Requirement-to-Implementation platform. Connects Requirements, Jira, and GitHub.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    openapi_tags=tags_metadata
)

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["projects"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/projects", tags=["upload"])
app.include_router(requirements.router, prefix=f"{settings.API_V1_STR}/requirements", tags=["requirements"])
app.include_router(jira.router, prefix=f"{settings.API_V1_STR}/jira", tags=["jira"])
app.include_router(github.router, prefix=f"{settings.API_V1_STR}/github", tags=["github"])
app.include_router(alignment.router, prefix=f"{settings.API_V1_STR}/alignment", tags=["alignment"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["reports"])
app.include_router(system.router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(client.router, prefix=f"{settings.API_V1_STR}/client", tags=["client"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
