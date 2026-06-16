import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.requirement_version import RequirementVersion
from app.models.jira_story import JiraStory
from app.models.pull_request import PullRequest
from app.models.code_artifact import CodeArtifact, ArtifactType
from app.models.alignment_result import AlignmentResult
from app.models.mismatch_report import MismatchReport

async def seed_demo_workspace(db: AsyncSession):
    # Get or create demo user
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="demo@example.com",
            full_name="Demo User",
            hashed_password="mock",
            role="admin"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Delete existing demo project if it exists (for idempotency)
    result = await db.execute(select(Project).where(Project.name == "E-Commerce Customer Portal"))
    existing_project = result.scalar_one_or_none()
    if existing_project:
        await db.delete(existing_project)
        await db.commit()

    # Create project
    project = Project(
        id=uuid.uuid4(),
        name="E-Commerce Customer Portal",
        client_name="Demo Client",
        description="Demo workspace for E-Commerce platform",
        status="Active",
        owner_id=user.id
    )
    db.add(project)
    await db.flush()

    # Requirements
    req1 = Requirement(id=uuid.uuid4(), project_id=project.id, title="REQ-001 (Login)", description="User Login")
    req2 = Requirement(id=uuid.uuid4(), project_id=project.id, title="REQ-002 (View Orders)", description="View Orders")
    req3 = Requirement(id=uuid.uuid4(), project_id=project.id, title="REQ-003 (Download Invoices)", description="Download Invoices")
    db.add_all([req1, req2, req3])
    await db.flush()

    # Requirement Versions
    req_v1 = RequirementVersion(id=uuid.uuid4(), requirement_id=req1.id, version_number=1, content="User Login feature", is_baseline=True)
    req_v2 = RequirementVersion(id=uuid.uuid4(), requirement_id=req2.id, version_number=1, content="View Order History", is_baseline=True)
    req_v3 = RequirementVersion(id=uuid.uuid4(), requirement_id=req3.id, version_number=1, content="Download Invoices", is_baseline=True)
    db.add_all([req_v1, req_v2, req_v3])
    await db.flush()

    # Jira Stories
    jira1 = JiraStory(id=uuid.uuid4(), project_id=project.id, jira_issue_key="JIRA-101", title="User Login", status="Done")
    jira2 = JiraStory(id=uuid.uuid4(), project_id=project.id, jira_issue_key="JIRA-102", title="Order History", status="Done")
    jira3 = JiraStory(id=uuid.uuid4(), project_id=project.id, jira_issue_key="JIRA-103", title="Invoice Download", status="Done")
    db.add_all([jira1, jira2, jira3])
    await db.flush()

    # Pull Requests
    pr1 = PullRequest(id=uuid.uuid4(), project_id=project.id, pr_number=201, repository_url="https://github.com/demo/repo", title="Add Login", status="merged")
    pr2 = PullRequest(id=uuid.uuid4(), project_id=project.id, pr_number=202, repository_url="https://github.com/demo/repo", title="Add Order History", status="merged")
    pr3 = PullRequest(id=uuid.uuid4(), project_id=project.id, pr_number=203, repository_url="https://github.com/demo/repo", title="Add Invoice Editing", status="merged")
    db.add_all([pr1, pr2, pr3])
    await db.flush()

    # Code Artifacts
    ca1 = CodeArtifact(id=uuid.uuid4(), pull_request_id=pr1.id, artifact_type=ArtifactType.FUNCTION, artifact_name="login_user()", file_path="auth.py")
    ca2 = CodeArtifact(id=uuid.uuid4(), pull_request_id=pr1.id, artifact_type=ArtifactType.API_ENDPOINT, artifact_name="/auth/login", file_path="auth.py")
    ca3 = CodeArtifact(id=uuid.uuid4(), pull_request_id=pr2.id, artifact_type=ArtifactType.FUNCTION, artifact_name="get_orders()", file_path="orders.py")
    ca4 = CodeArtifact(id=uuid.uuid4(), pull_request_id=pr2.id, artifact_type=ArtifactType.API_ENDPOINT, artifact_name="/orders", file_path="orders.py")
    ca5 = CodeArtifact(id=uuid.uuid4(), pull_request_id=pr3.id, artifact_type=ArtifactType.FUNCTION, artifact_name="edit_invoice()", file_path="invoice.py")
    ca6 = CodeArtifact(id=uuid.uuid4(), pull_request_id=pr3.id, artifact_type=ArtifactType.API_ENDPOINT, artifact_name="/invoice/edit", file_path="invoice.py")
    db.add_all([ca1, ca2, ca3, ca4, ca5, ca6])
    await db.flush()

    # Alignment Results
    # Aligned 1
    ar1 = AlignmentResult(
        id=uuid.uuid4(),
        project_id=project.id,
        requirement_version_id=req_v1.id,
        jira_story_id=jira1.id,
        pull_request_id=pr1.id,
        code_artifact_id=ca1.id,
        requirement_jira_score=100,
        jira_pr_score=100,
        pr_artifact_score=100,
        overall_alignment_score=100,
        score=100,
        alignment_status="Aligned",
        confidence=100,
        explanation="Implementation aligns with requirements.",
        summary="Implementation aligns with requirements."
    )
    
    # Aligned 2
    ar2 = AlignmentResult(
        id=uuid.uuid4(),
        project_id=project.id,
        requirement_version_id=req_v2.id,
        jira_story_id=jira2.id,
        pull_request_id=pr2.id,
        code_artifact_id=ca3.id,
        requirement_jira_score=100,
        jira_pr_score=100,
        pr_artifact_score=100,
        overall_alignment_score=100,
        score=100,
        alignment_status="Aligned",
        confidence=100,
        explanation="Implementation aligns with requirements.",
        summary="Implementation aligns with requirements."
    )
    
    # Drift
    ar3 = AlignmentResult(
        id=uuid.uuid4(),
        project_id=project.id,
        requirement_version_id=req_v3.id,
        jira_story_id=jira3.id,
        pull_request_id=pr3.id,
        code_artifact_id=ca5.id,
        requirement_jira_score=90,
        jira_pr_score=80,
        pr_artifact_score=50,
        overall_alignment_score=50,
        score=50,
        alignment_status="Potential Drift",
        confidence=90,
        explanation="Implementation is Edit Invoice instead of Download Invoice.",
        summary="Implementation is Edit Invoice instead of Download Invoice."
    )
    db.add_all([ar1, ar2, ar3])
    await db.flush()

    # Mismatch Report
    mr = MismatchReport(
        id=uuid.uuid4(),
        project_id=project.id,
        alignment_result_id=ar3.id,
        mismatch_type="logic_error",
        description="Implementation is Edit Invoice instead of Download Invoice.",
        status="Open",
        severity="High"
    )
    db.add(mr)

    await db.commit()

    return {"message": "Demo workspace seeded successfully", "project_id": str(project.id)}
