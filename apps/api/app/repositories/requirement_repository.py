from app.repositories.base import BaseRepository
from app.models.requirement import Requirement
from app.schemas.requirement import RequirementCreate, RequirementUpdate

class RequirementRepository(BaseRepository[Requirement, RequirementCreate, RequirementUpdate]):
    pass

requirement_repo = RequirementRepository(Requirement)
