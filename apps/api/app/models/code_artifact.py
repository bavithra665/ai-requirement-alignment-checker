from sqlalchemy import Column, String, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import BaseDomainModel


class ArtifactType(str, enum.Enum):
    FUNCTION = "Function"
    CLASS = "Class"
    API_ENDPOINT = "API Endpoint"


class CodeArtifact(Base, BaseDomainModel):
    """
    Normalized store for extracted code symbols from Pull Request file changes.
    Each row represents a single function, class, or API endpoint discovered
    in a PR's changed files via AST or Tree-sitter analysis.
    """
    __tablename__ = "code_artifacts"

    pull_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey('pull_requests.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    artifact_type = Column(
        SAEnum(ArtifactType, name='artifacttype'),
        nullable=False,
        index=True
    )
    artifact_name = Column(String, nullable=False, index=True)  # e.g. "edit_invoice", "/invoice/edit"
    file_path = Column(String, nullable=False)                   # e.g. "app/routes/invoice.py"
    artifact_metadata = Column(JSONB, nullable=True)                      # line_number, http_method, args, decorators, etc.

    # Relationships
    pull_request = relationship("PullRequest", back_populates="code_artifacts")
