from app.repositories.base import BaseRepository
from app.models.mismatch_report import MismatchReport
from app.schemas.mismatch_report import MismatchReportCreate, MismatchReportUpdate

class MismatchReportRepository(BaseRepository[MismatchReport, MismatchReportCreate, MismatchReportUpdate]):
    pass

mismatch_report_repo = MismatchReportRepository(MismatchReport)
