from app.repositories.base import BaseRepository
from app.models.alignment_result import AlignmentResult
from app.schemas.alignment_result import AlignmentResultCreate, AlignmentResultUpdate

class AlignmentResultRepository(BaseRepository[AlignmentResult, AlignmentResultCreate, AlignmentResultUpdate]):
    pass

alignment_result_repo = AlignmentResultRepository(AlignmentResult)
