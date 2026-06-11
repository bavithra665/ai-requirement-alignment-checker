from app.repositories.base import BaseRepository
from app.models.jira_story import JiraStory
from app.schemas.jira_story import JiraStoryCreate, JiraStoryUpdate

class JiraStoryRepository(BaseRepository[JiraStory, JiraStoryCreate, JiraStoryUpdate]):
    pass

jira_story_repo = JiraStoryRepository(JiraStory)
