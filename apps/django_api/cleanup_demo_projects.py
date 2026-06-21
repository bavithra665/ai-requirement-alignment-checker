import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from projects.models import Project

DEMO_KEYWORDS = [
    'django migration',
    'acme project',
    'acme corp',
    'acme',
    'brd test',
    'integration test',
    'invoice test',
    'fully aligned',
    'partially aligned',
    'misaligned project',
    'seed demo',
    'demo workspace',
    'test project',
    'local test',
    'demo project',
]

kept = []
deleted = []

for project in Project.objects.all():
    name_lower = project.name.lower()
    # Never delete MSME Command Center
    if 'msme' in name_lower or 'command center' in name_lower:
        kept.append(project.name)
        continue
    is_demo = any(kw in name_lower for kw in DEMO_KEYWORDS)
    if is_demo:
        deleted.append(project.name)
        project.delete()
    else:
        kept.append(project.name)

print(f"\n=== Demo Project Cleanup ===")
print(f"Deleted ({len(deleted)}):")
for n in deleted:
    print(f"  - {n}")
print(f"\nKept ({len(kept)}):")
for n in kept:
    print(f"  + {n}")
print(f"\nTotal deleted: {len(deleted)}")
