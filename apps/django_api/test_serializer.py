import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from django.contrib.auth import get_user_model
from projects.serializers import ProjectSerializer

User = get_user_model()

# Create or get a client user
client_email = "testclient@example.com"
client_user, _ = User.objects.get_or_create(email=client_email, defaults={'role': 'client', 'password': 'password123'})
if client_user.role != 'client':
    client_user.role = 'client'
    client_user.save()

# Create or get an owner (developer)
owner_email = "dev@example.com"
owner_user, _ = User.objects.get_or_create(email=owner_email, defaults={'role': 'developer', 'password': 'password123'})

# Setup request object needed by serializer for saving owner if needed, though we can pass owner explicitly
factory = APIRequestFactory()
request = factory.post('/api/v1/projects')
request.user = owner_user
drf_request = Request(request)

# Data for project creation
data = {
    "name": "Serializer Test Project",
    "client_email": client_email,
    "description": "Testing the serializer fix",
    "client_name": "Test Client Corp"
}

print(f"Testing serializer with client_email={client_email}")

# Initialize serializer
serializer = ProjectSerializer(data=data, context={'request': drf_request})

# Validate
is_valid = serializer.is_valid()
print(f"Serializer valid: {is_valid}")
if not is_valid:
    print(f"Errors: {serializer.errors}")
else:
    # Save project (we need to pass owner since it's read-only and typically saved in ViewSet perform_create)
    project = serializer.save(owner=owner_user)
    print(f"Successfully created project ID: {project.id}")
    print(f"Linked Client User ID: {project.client_user_id}")
    
    # Cleanup
    project.delete()
    print("Test project cleaned up.")
