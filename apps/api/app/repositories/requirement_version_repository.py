from app.repositories.base import BaseRepository
from app.models.requirement_version import RequirementVersion
from app.schemas.requirement_version import RequirementVersionCreate, RequirementVersionUpdate

class RequirementVersionRepository(BaseRepository[RequirementVersion, RequirementVersionCreate, RequirementVersionUpdate]):
    pass

requirement_version_repo = RequirementVersionRepository(RequirementVersion)
