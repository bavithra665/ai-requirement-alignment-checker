import requests

BASE_URL = 'http://localhost:8001/api/v1'

res = requests.post(f'{BASE_URL}/auth/login', json={'email':'brd_tester@example.com', 'password':'TestPassword123!'})
token = res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

res = requests.post(f'{BASE_URL}/projects', json={'name': 'BRD Test Project'}, headers=headers)
proj_id = res.json()['id']
print('Created Project:', proj_id)

with open('test_brd.docx', 'rb') as f:
    res = requests.post(f'{BASE_URL}/projects/{proj_id}/upload-brd', files={'file': ('test_brd.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}, headers=headers)
print('DOCX Upload Response:', res.status_code, res.json())

with open('test_brd.pdf', 'rb') as f:
    res = requests.post(f'{BASE_URL}/projects/{proj_id}/upload-brd', files={'file': ('test_brd.pdf', f, 'application/pdf')}, headers=headers)
print('PDF Upload Response:', res.status_code, res.json())

res = requests.get(f'{BASE_URL}/requirements/project/{proj_id}', headers=headers)
versions = res.json()
print('\nExtracted Requirements Count:', len(versions))
for v in versions:
    print(f'- Version {v["version_number"]}: {v["content"][:80]}...')
    print(f'  AI Summary snippet: {v["ai_summary"][:80]}...')
