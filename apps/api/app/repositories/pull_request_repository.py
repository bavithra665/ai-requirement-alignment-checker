from app.repositories.base import BaseRepository
from app.models.pull_request import PullRequest
from app.schemas.pull_request import PullRequestCreate, PullRequestUpdate

class PullRequestRepository(BaseRepository[PullRequest, PullRequestCreate, PullRequestUpdate]):
    pass

pull_request_repo = PullRequestRepository(PullRequest)
