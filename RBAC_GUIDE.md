# RBAC (Role-Based Access Control) Guide

## Overview

The ZK Attendance Pro system includes a complete RBAC implementation using SQLite, providing secure authentication and fine-grained authorization without requiring Supabase.

## Features

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based permissions
- ✅ User management
- ✅ Audit logging
- ✅ Independent of Supabase (SQLite only)

---

## Default Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **admin** | Full system access | `*` (all permissions) |
| **hr_manager** | HR and employee management | `employees:*`, `attendance:read`, `reports:*` |
| **department_manager** | Department-level access | `employees:read`, `attendance:read`, `reports:read` |
| **employee** | View own attendance | `attendance:read_own` |
| **viewer** | Read-only access | `attendance:read`, `reports:read` |

---

## Default Admin Account

On first startup, a default admin account is created:

```
Username: admin
Password: admin123
```

**⚠️ IMPORTANT:** Change this password immediately after first login!

---

## Authentication Endpoints

### 1. Login

**POST** `/api/auth/login`

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Get Current User

**GET** `/api/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "System Administrator",
  "is_active": true,
  "is_superuser": true,
  "roles": ["admin"],
  "permissions": ["*"]
}
```

### 3. Change Password

**POST** `/api/auth/change-password`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "old_password": "admin123",
  "new_password": "NewSecurePassword123!"
}
```

### 4. Register New User

**POST** `/api/auth/register`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Requires:** `users:write` permission

**Body:**
```json
{
  "username": "jdoe",
  "email": "jdoe@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "department": "Engineering",
  "employee_pin": "1001"
}
```

---

## User Management Endpoints

### Get All Users

**GET** `/api/users`

**Requires:** `users:read` permission

### Get Specific User

**GET** `/api/users/{user_id}`

**Requires:** `users:read` permission

### Update User

**PUT** `/api/users/{user_id}`

**Requires:** `users:write` permission

**Body:**
```json
{
  "full_name": "John Smith",
  "department": "HR",
  "is_active": true
}
```

### Delete User

**DELETE** `/api/users/{user_id}`

**Requires:** Superuser access

---

## Role Management Endpoints

### Get All Roles

**GET** `/api/roles`

**Requires:** `users:read` permission

### Assign Role to User

**POST** `/api/users/{user_id}/roles/{role_id}`

**Requires:** `users:write` permission

### Remove Role from User

**DELETE** `/api/users/{user_id}/roles/{role_id}`

**Requires:** `users:write` permission

---

## Audit Logs

### Get Audit Logs

**GET** `/api/audit-logs?user_id=1&limit=100`

**Requires:** `audit:read` permission

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "action": "user_created",
    "resource": "users",
    "resource_id": "2",
    "details": "{\"username\": \"jdoe\"}",
    "ip_address": null,
    "user_agent": null,
    "created_at": "2025-12-03T12:00:00"
  }
]
```

---

## Permission System

### Permission Format

Permissions follow the format: `resource:action`

Examples:
- `employees:read` - Read employee data
- `employees:write` - Create/update employees
- `employees:delete` - Delete employees
- `attendance:read` - View attendance logs
- `reports:export` - Export reports
- `*` - All permissions (admin only)

### Wildcard Permissions

- `employees:*` - All employee operations
- `*` - All permissions (superuser)

### Checking Permissions in Code

```python
from app.auth import require_permission, require_role, require_superuser

# Require specific permission
@app.get("/api/protected")
async def protected_endpoint(
    current_user: dict = Depends(require_permission("employees:read"))
):
    return {"message": "You have access"}

# Require specific role
@app.get("/api/admin-only")
async def admin_endpoint(
    current_user: dict = Depends(require_role("admin"))
):
    return {"message": "Admin access"}

# Require superuser
@app.delete("/api/critical")
async def critical_endpoint(
    current_user: dict = Depends(require_superuser)
):
    return {"message": "Superuser access"}
```

---

## Using JWT Tokens

### In API Requests

Include the JWT token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer <access_token>" \
     http://localhost:8000/api/auth/me
```

### Token Expiration

- Default expiration: **24 hours**
- Configurable in `app/auth.py`: `ACCESS_TOKEN_EXPIRE_MINUTES`

### Refreshing Tokens

Currently, tokens must be refreshed by logging in again. To implement refresh tokens, add a separate refresh endpoint.

---

## Security Best Practices

1. **Change Default Password**
   - Immediately change the default admin password after first login

2. **Use Strong Passwords**
   - Minimum 8 characters
   - Mix of uppercase, lowercase, numbers, and symbols

3. **Secure SECRET_KEY**
   - Set a strong `SECRET_KEY` in `.env`
   - Minimum 32 characters
   - Never commit to version control

4. **HTTPS in Production**
   - Always use HTTPS in production
   - JWT tokens are vulnerable if transmitted over HTTP

5. **Regular Audits**
   - Review audit logs regularly
   - Monitor for suspicious activity

6. **Principle of Least Privilege**
   - Assign minimum required permissions
   - Use specific roles instead of admin

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    department TEXT,
    employee_pin TEXT,
    is_active INTEGER DEFAULT 1,
    is_superuser INTEGER DEFAULT 0,
    last_login TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

### Roles Table

```sql
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT,  -- JSON array
    created_at TEXT,
    updated_at TEXT
);
```

### User-Role Mapping

```sql
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TEXT,
    PRIMARY KEY (user_id, role_id)
);
```

### Audit Logs

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource TEXT,
    resource_id TEXT,
    details TEXT,  -- JSON
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT
);
```

---

## Example Workflows

### Creating a New HR Manager

```bash
# 1. Login as admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}

# 2. Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "hr_manager",
    "email": "hr@company.com",
    "password": "SecurePass123!",
    "full_name": "HR Manager",
    "department": "Human Resources"
  }'

# 3. Get hr_manager role ID
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/roles

# Response: [{"id": 2, "name": "hr_manager", ...}]

# 4. Assign hr_manager role
curl -X POST http://localhost:8000/api/users/2/roles/2 \
  -H "Authorization: Bearer <token>"
```

### Viewing Audit Logs

```bash
# Get all audit logs
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/audit-logs?limit=50

# Get logs for specific user
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/audit-logs?user_id=2&limit=20
```

---

## Troubleshooting

### "Could not validate credentials"

- Token expired (24 hours)
- Invalid token format
- Token signed with different SECRET_KEY

**Solution:** Login again to get a new token

### "Permission denied"

- User doesn't have required permission
- User's role doesn't include the permission

**Solution:** Assign appropriate role or permission

### "Incorrect username or password"

- Wrong credentials
- User account is inactive

**Solution:** Verify credentials or activate account

### Default admin not created

- Database already has a superuser
- Check logs for errors

**Solution:** Manually create admin or check database

---

## Configuration

### Environment Variables

Add to `.env`:

```env
# JWT Secret Key (REQUIRED - change in production!)
SECRET_KEY=your-super-secret-key-min-32-characters-long

# Token expiration (optional, default 24 hours)
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### Customizing Roles

Edit `app/database.py` to add custom roles:

```python
default_roles = [
    ("custom_role", "Custom role description", json.dumps([
        "employees:read",
        "attendance:read"
    ]), now, now),
]
```

---

## API Testing with Swagger

Visit `http://localhost:8000/docs` for interactive API documentation.

1. Click **Authorize** button
2. Enter: `Bearer <your_access_token>`
3. Test endpoints directly in browser

---

## Next Steps

1. **Change default admin password**
2. **Create user accounts for your team**
3. **Assign appropriate roles**
4. **Test permissions**
5. **Monitor audit logs**
6. **Set strong SECRET_KEY in production**
