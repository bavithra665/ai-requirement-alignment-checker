from app.repositories.base import BaseRepository
from app.models.client_approval import ClientApproval
from app.schemas.client_approval import ClientApprovalCreate, ClientApprovalUpdate

class ClientApprovalRepository(BaseRepository[ClientApproval, ClientApprovalCreate, ClientApprovalUpdate]):
    pass

client_approval_repo = ClientApprovalRepository(ClientApproval)
