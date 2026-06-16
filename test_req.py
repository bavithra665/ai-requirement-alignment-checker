import requests
try:
    res = requests.post("http://localhost:8000/api/v1/auth/register", json={
        "email": "test@test.com",
        "password": "password123",
        "full_name": "Test User",
        "company_name": "Test Inc",
        "role": "developer"
    })
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
