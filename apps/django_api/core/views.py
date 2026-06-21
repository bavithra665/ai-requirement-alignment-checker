from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import connection
import os
from django.utils import timezone

class SystemHealthView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        services = {}
        
        # 1. Check Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            services['database'] = {
                "status": "Green",
                "message": "Connected and responsive"
            }
        except Exception as e:
            services['database'] = {
                "status": "Red",
                "message": f"Connection failed: {str(e)}"
            }
            
        # 2. Check ChromaDB
        try:
            from alignment.services import get_chroma_client
            client = get_chroma_client()
            client.heartbeat()
            services['chromadb'] = {
                "status": "Green",
                "message": "Connected and responsive"
            }
        except Exception as e:
            services['chromadb'] = {
                "status": "Red",
                "message": f"Connection failed: {str(e)}"
            }
            
        # 3. Check Groq
        if os.getenv('GROQ_API_KEY'):
            services['groq'] = {
                "status": "Green",
                "message": "API key configured"
            }
        else:
            services['groq'] = {
                "status": "Amber",
                "message": "API key missing (AI features disabled)"
            }
            
        # 4. Check Github
        if os.getenv('GITHUB_TOKEN'):
            services['github'] = {
                "status": "Green",
                "message": "Integration configured"
            }
        else:
            services['github'] = {
                "status": "Amber",
                "message": "Global token missing (using per-project configs)"
            }
            
        # 5. Check Jira
        if os.getenv('JIRA_API_TOKEN') and os.getenv('JIRA_BASE_URL'):
            services['jira'] = {
                "status": "Green",
                "message": "Integration configured"
            }
        else:
            services['jira'] = {
                "status": "Amber",
                "message": "Global credentials missing (using per-project configs)"
            }
            
        return Response({
            "timestamp": timezone.now().isoformat(),
            "services": services
        }, status=status.HTTP_200_OK)
