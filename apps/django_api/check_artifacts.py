import os
import sys
import django

# Set up django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from integrations.models import CodeArtifact

artifacts = CodeArtifact.objects.all()
print(f"Total CodeArtifacts: {artifacts.count()}")

types = {}
for a in artifacts:
    types[a.artifact_type] = types.get(a.artifact_type, 0) + 1

print("Artifact Types:")
for t, count in types.items():
    print(f"  {t}: {count}")

# Print first 20 artifacts details
for a in artifacts[:20]:
    print(f"  ID: {a.id}, Type: {a.artifact_type}, Name: {a.artifact_name}, File: {a.file_path}")
