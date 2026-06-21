import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
User = get_user_model()

client_email = "testclient_api@example.com"
client_user, _ = User.objects.get_or_create(email=client_email, defaults={'username': 'testclient_api', 'role': 'client', 'password': 'password123'})
if client_user.role != 'client':
    client_user.role = 'client'
    client_user.save()

owner_email = "dev_api@example.com"
owner_user, _ = User.objects.get_or_create(email=owner_email, defaults={'username': 'dev_api', 'role': 'developer', 'password': 'password123'})

client = APIClient()
client.force_authenticate(user=owner_user)

data = {
    "name": "API Test Project",
    "client_email": client_email,
    "description": "Testing the API response code",
    "client_name": "API Test Client"
}

response = client.post('/api/v1/projects', data, format='json')
print(f"POST /api/v1/projects Status Code: {response.status_code}")
if response.status_code == 201:
    print("Project successfully created via API.")
    project_id = response.data.get('id')
    from projects.models import Project
    Project.objects.get(id=project_id).delete()
    print("Test project cleaned up.")
else:
    print(f"Response Error: {response.data}")
