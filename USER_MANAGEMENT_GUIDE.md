# User Management & Password Change Guide

## ✅ New Features Implemented

### 1. **User Management Page** (`/users`)
Complete user administration interface with:
- ✅ View all users in a table
- ✅ Add new users
- ✅ Edit existing users
- ✅ Delete users (except superusers and yourself)
- ✅ Assign/remove roles
- ✅ Activate/deactivate users
- ✅ Role-based access control (requires `users:write` permission)

### 2. **Change Password Functionality**
Available in two places:
- ✅ Dashboard user menu → Change Password
- ✅ Users page user menu → Change Password
- ✅ Validates current password
- ✅ Enforces minimum 8 characters
- ✅ Confirms new password match
- ✅ Logs password changes in audit trail

### 3. **Enhanced Navigation**
- ✅ "Users" link added to dashboard navigation
- ✅ User dropdown menu with change password option
- ✅ Logout functionality
- ✅ Active user display

---

## 🎯 How to Use

### Accessing User Management

1. **Login as Admin**
   ```
   Username: admin
   Password: admin123
   ```

2. **Navigate to Users Page**
   - Click "Users" in the top navigation
   - Or visit: `http://localhost:8000/users`

3. **Permission Check**
   - Only users with `users:write` permission can access
   - Admin role has full access

---

## 👥 Managing Users

### Add New User

1. Click **"Add User"** button (top right)
2. Fill in the form:
   - **Username*** (required, unique)
   - **Email*** (required, unique)
   - **Password*** (required, min 8 chars)
   - **Confirm Password*** (required)
   - **Full Name** (optional)
   - **Department** (optional)
   - **Employee PIN** (optional - links to employee record)
   - **Roles*** (required - select at least one)
   - **Active** (checkbox - default checked)

3. Click **"Save User"**

**Example:**
```
Username: jsmith
Email: jsmith@company.com
Password: SecurePass123!
Full Name: John Smith
Department: IT
Roles: [✓] hr_manager
Active: [✓]
```

### Edit User

1. Click the **edit icon** (pencil) next to user
2. Modify fields (password not required for edit)
3. Update roles as needed
4. Click **"Save User"**

**Note:** Password fields are hidden when editing. Use "Change Password" to update passwords.

### Delete User

1. Click the **delete icon** (trash) next to user
2. Confirm deletion
3. User is permanently removed

**Restrictions:**
- ❌ Cannot delete superusers
- ❌ Cannot delete yourself
- ✅ Can delete regular users

### Assign/Remove Roles

**During User Creation/Edit:**
1. Check/uncheck role checkboxes
2. Available roles:
   - **admin** - Full system access
   - **hr_manager** - HR and employee management
   - **department_manager** - Department-level access
   - **employee** - View own attendance
   - **viewer** - Read-only access

3. Click "Save User"

**Via API:**
```bash
# Assign role
POST /api/users/{user_id}/roles/{role_id}

# Remove role
DELETE /api/users/{user_id}/roles/{role_id}
```

---

## 🔑 Changing Passwords

### Change Your Own Password

**Method 1: From Dashboard**
1. Click your username (top right)
2. Click **"Change Password"**
3. Enter:
   - Current Password
   - New Password (min 8 chars)
   - Confirm New Password
4. Click **"Change Password"**

**Method 2: From Users Page**
1. Click your username (top right)
2. Click **"Change Password"**
3. Same process as above

### Change Admin Password (IMPORTANT!)

**First Login - Change Default Password:**
1. Login with `admin` / `admin123`
2. Click "admin" in top right
3. Click "Change Password"
4. Enter:
   ```
   Current Password: admin123
   New Password: YourNewSecurePassword123!
   Confirm: YourNewSecurePassword123!
   ```
5. Click "Change Password"
6. ✅ Default password changed!

**Password Requirements:**
- ✅ Minimum 8 characters
- ✅ Must match confirmation
- ✅ Current password must be correct

---

## 📊 User Table Columns

| Column | Description |
|--------|-------------|
| **User** | Avatar, full name, and username |
| **Email** | User's email address |
| **Department** | Department assignment |
| **Roles** | Colored badges showing assigned roles |
| **Status** | Active (green) or Inactive (red) |
| **Actions** | Edit and Delete buttons |

### Role Badges

- 🔴 **admin** - Red badge
- 🔵 **hr_manager** - Blue badge
- 🟣 **department_manager** - Purple badge
- 🟢 **employee** - Green badge
- ⚫ **viewer** - Gray badge

---

## 🔒 Security Features

### Password Security
- ✅ Bcrypt hashing (72-byte limit handled)
- ✅ Minimum 8 characters enforced
- ✅ Current password verification required
- ✅ Password confirmation required
- ✅ Audit logging of password changes

### Access Control
- ✅ JWT token authentication
- ✅ Permission-based access (`users:write`)
- ✅ Cannot delete superusers
- ✅ Cannot delete yourself
- ✅ Session validation on every request

### Audit Trail
All user management actions are logged:
- User creation
- User updates
- Role assignments/removals
- Password changes
- User deletions

View audit logs:
```bash
GET /api/audit-logs?user_id=1&limit=100
```

---

## 🎨 UI Features

### User Management Page
- ✅ Clean table layout
- ✅ Color-coded role badges
- ✅ Status indicators (Active/Inactive)
- ✅ Inline edit/delete actions
- ✅ Modal forms for add/edit
- ✅ Real-time validation
- ✅ Success/error alerts

### Change Password Modal
- ✅ Clean, centered modal
- ✅ Password strength hint
- ✅ Inline validation
- ✅ Success/error messages
- ✅ Auto-close on success

---

## 📝 API Endpoints

### User Management

```bash
# Get all users
GET /api/users
Authorization: Bearer <token>
Requires: users:read

# Get specific user
GET /api/users/{user_id}
Authorization: Bearer <token>
Requires: users:read

# Create user
POST /api/auth/register
Authorization: Bearer <token>
Requires: users:write
Body: {
  "username": "jsmith",
  "email": "jsmith@company.com",
  "password": "SecurePass123!",
  "full_name": "John Smith",
  "department": "IT"
}

# Update user
PUT /api/users/{user_id}
Authorization: Bearer <token>
Requires: users:write
Body: {
  "full_name": "John Smith Jr.",
  "department": "Engineering",
  "is_active": true
}

# Delete user
DELETE /api/users/{user_id}
Authorization: Bearer <token>
Requires: Superuser
```

### Role Management

```bash
# Get all roles
GET /api/roles
Authorization: Bearer <token>
Requires: users:read

# Assign role to user
POST /api/users/{user_id}/roles/{role_id}
Authorization: Bearer <token>
Requires: users:write

# Remove role from user
DELETE /api/users/{user_id}/roles/{role_id}
Authorization: Bearer <token>
Requires: users:write
```

### Password Management

```bash
# Change password
POST /api/auth/change-password
Authorization: Bearer <token>
Body: {
  "old_password": "admin123",
  "new_password": "NewSecurePass123!"
}
```

---

## 🧪 Testing

### Test User Creation

1. Login as admin
2. Go to `/users`
3. Click "Add User"
4. Create test user:
   ```
   Username: testuser
   Email: test@example.com
   Password: Test1234!
   Roles: employee
   ```
5. Verify user appears in table

### Test Password Change

1. Login as admin
2. Click "admin" → "Change Password"
3. Enter:
   ```
   Current: admin123
   New: NewAdmin123!
   Confirm: NewAdmin123!
   ```
4. Submit
5. Logout
6. Login with new password

### Test Role Assignment

1. Edit a user
2. Check "hr_manager" role
3. Save
4. Verify badge appears in table
5. Login as that user
6. Verify access to HR features

---

## ⚠️ Important Notes

### Default Admin Password
```
⚠️ CRITICAL: Change the default admin password immediately!
Username: admin
Password: admin123 (CHANGE THIS!)
```

### Permission Requirements

| Action | Required Permission |
|--------|-------------------|
| View users | `users:read` or `*` |
| Create users | `users:write` or `*` |
| Edit users | `users:write` or `*` |
| Delete users | Superuser only |
| Assign roles | `users:write` or `*` |
| Change own password | Authenticated user |

### Best Practices

1. **Change Default Password**
   - First thing after installation
   - Use strong, unique password

2. **Principle of Least Privilege**
   - Assign minimum required roles
   - Don't make everyone admin

3. **Regular Audits**
   - Review user list monthly
   - Deactivate unused accounts
   - Check audit logs

4. **Password Policy**
   - Enforce 8+ characters
   - Encourage complexity
   - Rotate passwords regularly

---

## 🐛 Troubleshooting

### Cannot Access Users Page
**Problem:** "Permission denied" or redirect
**Solution:** User needs `users:write` permission. Assign hr_manager or admin role.

### Password Change Fails
**Problem:** "Incorrect password"
**Solution:** Verify current password is correct. Check caps lock.

### Cannot Delete User
**Problem:** Delete button disabled
**Solution:** Cannot delete superusers or yourself. This is by design.

### Role Not Showing
**Problem:** Role assigned but not visible
**Solution:** Refresh page. Check API response in browser console.

### Modal Not Closing
**Problem:** Modal stuck open
**Solution:** Click X button or Cancel. Refresh page if needed.

---

## 📂 Files Modified/Created

| File | Status | Description |
|------|--------|-------------|
| `app/templates/users.html` | ✅ Created | User management page |
| `app/templates/dashboard.html` | ✅ Updated | Added change password modal |
| `app/main.py` | ✅ Updated | Added `/users` route, fixed password endpoint |
| `USER_MANAGEMENT_GUIDE.md` | ✅ Created | This documentation |

---

## 🎉 Summary

You now have a complete user management system with:

✅ **User CRUD Operations**
- Create, read, update, delete users
- Role assignment
- Status management

✅ **Password Management**
- Change password modal
- Validation and security
- Audit logging

✅ **Access Control**
- Permission-based access
- Role-based authorization
- Superuser protections

✅ **Professional UI**
- Clean, modern interface
- Responsive design
- Real-time feedback

**Next Steps:**
1. Change default admin password
2. Create user accounts for your team
3. Assign appropriate roles
4. Test the system
5. Review audit logs regularly
