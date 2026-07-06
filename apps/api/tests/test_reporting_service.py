import uuid
from types import SimpleNamespace

import pytest

from app.services import reporting_service
from app.services.reporting_service import ReportingService


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)


class FakeDB:
    def __init__(self, results):
        self._results = list(results)
        self.added = []

    async def execute(self, stmt):
        if not self._results:
            return FakeResult([])
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        return None


class FakeMismatchReportRepo:
    def __init__(self):
        self.created = []

    async def create(self, db, obj_in, created_by_id=None):
        report = SimpleNamespace(
            id=uuid.uuid4(),
            project_id=obj_in.project_id,
            alignment_result_id=obj_in.alignment_result_id,
            is_deleted=False,
            status="Open",
            severity=obj_in.severity,
            mismatch_type=obj_in.mismatch_type,
            description=obj_in.description,
            suggested_fix=obj_in.suggested_fix,
        )
        self.created.append(report)
        return report

    async def update(self, db, db_obj, obj_in, updated_by_id=None):
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        return db_obj


@pytest.mark.asyncio
async def test_generate_mismatch_reports_soft_deletes_stale_reports(monkeypatch):
    service = ReportingService()
    project_id = uuid.uuid4()
    current_user_id = uuid.uuid4()

    aligned_result = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=project_id,
        alignment_status="Aligned",
        overall_alignment_score=100,
        requirement_jira_score=100,
        jira_pr_score=100,
        pr_artifact_score=100,
    )
    misaligned_result = SimpleNamespace(
        id=uuid.uuid4(),
        project_id=project_id,
        alignment_status="Misaligned",
        overall_alignment_score=25,
        requirement_jira_score=20,
        jira_pr_score=10,
        pr_artifact_score=0,
    )
    stale_report = SimpleNamespace(
        id=uuid.uuid4(),
        alignment_result_id=aligned_result.id,
        project_id=project_id,
        is_deleted=False,
        status="Open",
        severity="Low",
        mismatch_type="old_type",
    )

    fake_repo = FakeMismatchReportRepo()
    monkeypatch.setattr(reporting_service, "mismatch_report_repo", fake_repo)

    db = FakeDB([
        FakeResult([misaligned_result, aligned_result]),
        FakeResult([stale_report]),
    ])

    await service.generate_mismatch_reports(db, project_id, current_user_id)

    assert stale_report.is_deleted is True
    assert len(fake_repo.created) == 1
