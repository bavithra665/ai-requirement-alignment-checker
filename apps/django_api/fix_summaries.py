import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import RequirementVersion
from projects.services import ai_service

# Find all requirement versions that have the disabled message
bad_versions = RequirementVersion.objects.filter(ai_summary__startswith="Failed to generate executive summary")
print(f"Found {bad_versions.count()} requirement versions with disabled AI summary.")

if bad_versions.exists():
    # Group by project to avoid regenerating the summary for every single requirement unnecessarily
    # (Although since we modified the frontend to only show one summary per project, 
    # we still need to update them all so the frontend .find() finds a valid one)
    
    # Let's get all requirements from the project of the first bad version
    project = bad_versions.first().requirement.project
    all_project_reqs = [r.content for r in RequirementVersion.objects.filter(requirement__project=project)]
    full_text = "\n\n".join(all_project_reqs)
    
    print("Generating new AI Executive Summary for the project...")
    new_summary = ai_service.generate_executive_summary(full_text)
    
    if new_summary.startswith("AI Summary is disabled"):
        print("FAILED: API Key is still not working!")
    else:
        print("Successfully generated new summary. Updating database...")
        bad_versions.update(ai_summary=new_summary)
        print("Done!")
