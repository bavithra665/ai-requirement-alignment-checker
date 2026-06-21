import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connection

cursor = connection.cursor()

# Create missing M2M tables for PermissionsMixin
tables_to_create = [
    """
    CREATE TABLE IF NOT EXISTS users_groups (
        id BIGSERIAL PRIMARY KEY,
        customuser_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        group_id INTEGER NOT NULL REFERENCES auth_group(id) ON DELETE CASCADE,
        UNIQUE (customuser_id, group_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users_user_permissions (
        id BIGSERIAL PRIMARY KEY,
        customuser_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        permission_id INTEGER NOT NULL REFERENCES auth_permission(id) ON DELETE CASCADE,
        UNIQUE (customuser_id, permission_id)
    )
    """,
]

for sql in tables_to_create:
    cursor.execute(sql)
    print(f'Executed: {sql.strip().split(chr(10))[1].strip()}')

# Delete test user directly via SQL to avoid M2M cascade issue
cursor.execute("DELETE FROM users WHERE email = 'testdjango@example.com'")
print('Test user deleted')

print('All M2M tables created successfully')
