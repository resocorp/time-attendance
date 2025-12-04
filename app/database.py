"""
Database module for SQLite persistence
Handles all database operations for attendance system
"""
import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from functools import lru_cache
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "attendance.db")


class Database:
    """SQLite database for persistent storage"""

    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        """Initialize database and create tables"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Employees table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pin TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    department TEXT,
                    position TEXT,
                    card_number TEXT,
                    is_active INTEGER DEFAULT 1,
                    hire_date TEXT,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            # Attendance logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pin TEXT NOT NULL,
                    employee_name TEXT,
                    department TEXT,
                    device_sn TEXT,
                    punch_time TEXT NOT NULL,
                    punch_type TEXT,
                    verify_method TEXT,
                    work_code TEXT,
                    raw_data TEXT,
                    created_at TEXT
                )
            ''')

            # Devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    serial_number TEXT PRIMARY KEY,
                    name TEXT,
                    location TEXT,
                    ip_address TEXT,
                    firmware_version TEXT,
                    model TEXT,
                    status TEXT DEFAULT 'offline',
                    last_seen TEXT,
                    config TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            # Device commands table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_sn TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at TEXT,
                    sent_at TEXT,
                    completed_at TEXT
                )
            ''')

            # Punch time windows table - for automatic status switching
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS punch_time_windows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    punch_type TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    days_of_week TEXT DEFAULT '0,1,2,3,4,5,6',
                    priority INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    description TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Add days_of_week column if it doesn't exist (migration for existing DBs)
            cursor.execute("PRAGMA table_info(punch_time_windows)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'days_of_week' not in columns:
                cursor.execute("ALTER TABLE punch_time_windows ADD COLUMN days_of_week TEXT DEFAULT '0,1,2,3,4,5,6'")

            # System settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TEXT
                )
            ''')

            # ==================== RBAC TABLES ====================
            
            # Users table (for authentication)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
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
                    updated_at TEXT,
                    FOREIGN KEY (employee_pin) REFERENCES employees(pin) ON DELETE SET NULL
                )
            ''')

            # Roles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    permissions TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')

            # User-Role mapping (many-to-many)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    assigned_at TEXT,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
            ''')

            # Audit log for security tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    resource TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')

            # Insert default time windows if table is empty
            cursor.execute("SELECT COUNT(*) FROM punch_time_windows")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                # Days: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
                weekdays = "0,1,2,3,4"  # Monday-Friday
                all_days = "0,1,2,3,4,5,6"  # All week
                default_windows = [
                    ("CHECK_IN", "06:00", "10:00", weekdays, 1, "Morning check-in (Mon-Fri)"),
                    ("BREAK_OUT", "11:30", "12:30", weekdays, 2, "Lunch break start (Mon-Fri)"),
                    ("BREAK_IN", "12:30", "14:00", weekdays, 3, "Lunch break end (Mon-Fri)"),
                    ("CHECK_OUT", "16:00", "20:00", weekdays, 4, "Evening check-out (Mon-Fri)"),
                    ("OVERTIME_IN", "20:00", "22:00", weekdays, 5, "Overtime start (Mon-Fri)"),
                    ("OVERTIME_OUT", "22:00", "23:59", weekdays, 6, "Overtime end (Mon-Fri)"),
                ]
                for punch_type, start, end, days, priority, desc in default_windows:
                    cursor.execute('''
                        INSERT INTO punch_time_windows (punch_type, start_time, end_time, days_of_week, priority, is_active, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
                    ''', (punch_type, start, end, days, priority, desc, now, now))

            # Insert default settings if not exist
            cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key = 'auto_punch_type_enabled'")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO system_settings (key, value, description, updated_at)
                    VALUES ('auto_punch_type_enabled', 'true', 'Enable automatic punch type based on time windows', ?)
                ''', (now,))
                cursor.execute('''
                    INSERT INTO system_settings (key, value, description, updated_at)
                    VALUES ('work_start_time', '09:00', 'Standard work start time for late calculation', ?)
                ''', (now,))
                cursor.execute('''
                    INSERT INTO system_settings (key, value, description, updated_at)
                    VALUES ('work_end_time', '17:00', 'Standard work end time', ?)
                ''', (now,))
                cursor.execute('''
                    INSERT INTO system_settings (key, value, description, updated_at)
                    VALUES ('overtime_threshold_hours', '8', 'Hours after which overtime starts', ?)
                ''', (now,))

            # Insert default roles if not exist
            cursor.execute("SELECT COUNT(*) FROM roles")
            if cursor.fetchone()[0] == 0:
                now = datetime.now().isoformat()
                default_roles = [
                    ("admin", "Full system access", json.dumps(["*"]), now, now),
                    ("hr_manager", "HR and employee management", json.dumps([
                        "employees:read", "employees:write", "employees:delete",
                        "attendance:read", "reports:read", "reports:export"
                    ]), now, now),
                    ("department_manager", "Department-level access", json.dumps([
                        "employees:read", "attendance:read", "reports:read"
                    ]), now, now),
                    ("employee", "View own attendance", json.dumps([
                        "attendance:read_own"
                    ]), now, now),
                    ("viewer", "Read-only access", json.dumps([
                        "attendance:read", "reports:read"
                    ]), now, now),
                ]
                cursor.executemany('''
                    INSERT INTO roles (name, description, permissions, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', default_roles)
                logger.info("✅ Default roles created")

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_pin ON attendance_logs(pin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_time ON attendance_logs(punch_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_device ON attendance_logs(device_sn)')

            conn.commit()
            logger.info(f"✅ SQLite database initialized: {self.db_path}")

    @contextmanager
    def _get_conn(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ==================== EMPLOYEES ====================

    def get_employee(self, pin: str) -> Optional[dict]:
        """Get employee by PIN"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE pin = ?", (pin,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_employees(self) -> List[dict]:
        """Get all employees"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees ORDER BY pin")
            return [dict(row) for row in cursor.fetchall()]

    def create_employee(self, employee: dict) -> dict:
        """Create a new employee"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO employees (pin, name, email, phone, department, position, 
                                       card_number, is_active, hire_date, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                employee.get("pin"),
                employee.get("name"),
                employee.get("email"),
                employee.get("phone"),
                employee.get("department"),
                employee.get("position"),
                employee.get("card_number"),
                1 if employee.get("is_active", True) else 0,
                employee.get("hire_date"),
                employee.get("notes"),
                now,
                now
            ))
            conn.commit()
            employee["id"] = cursor.lastrowid
            employee["created_at"] = now
            employee["updated_at"] = now
        return employee

    def update_employee(self, pin: str, updates: dict) -> Optional[dict]:
        """Update an employee"""
        updates["updated_at"] = datetime.now().isoformat()
        
        # Build dynamic update query
        fields = []
        values = []
        for key, value in updates.items():
            if key not in ["id", "pin", "created_at"]:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return self.get_employee(pin)
        
        values.append(pin)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE employees SET {', '.join(fields)} WHERE pin = ?", values)
            conn.commit()
        
        return self.get_employee(pin)

    def delete_employee(self, pin: str) -> bool:
        """Delete an employee"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM employees WHERE pin = ?", (pin,))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== ATTENDANCE LOGS ====================

    def add_attendance_log(self, log: dict) -> dict:
        """Add an attendance log entry"""
        now = datetime.now().isoformat()
        
        # Look up employee name if we have PIN
        if log.get("pin"):
            employee = self.get_employee(log["pin"])
            if employee:
                log["employee_name"] = employee.get("name", f"Employee {log['pin']}")
                log["department"] = employee.get("department", "")
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO attendance_logs (pin, employee_name, department, device_sn, 
                                             punch_time, punch_type, verify_method, work_code, raw_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log.get("pin"),
                log.get("employee_name"),
                log.get("department"),
                log.get("device_sn"),
                log.get("punch_time"),
                log.get("punch_type"),
                log.get("verify_method"),
                log.get("work_code"),
                json.dumps(log.get("raw_data")) if log.get("raw_data") else None,
                now
            ))
            conn.commit()
            log["id"] = cursor.lastrowid
            log["created_at"] = now
        return log

    def get_attendance_logs(
        self, 
        date: Optional[str] = None,
        pin: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get attendance logs with optional filters"""
        query = "SELECT * FROM attendance_logs WHERE 1=1"
        params = []
        
        if date:
            query += " AND punch_time LIKE ?"
            params.append(f"{date}%")
        if pin:
            query += " AND pin = ?"
            params.append(pin)
        
        query += " ORDER BY punch_time DESC LIMIT ?"
        params.append(limit)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_attendance_stats(self, date: str) -> dict:
        """Get attendance statistics for a specific date"""
        logs = self.get_attendance_logs(date=date, limit=1000)
        
        # Group by employee
        employees = {}
        for log in logs:
            pin = log.get("pin", "Unknown")
            if pin not in employees:
                employees[pin] = {
                    "pin": pin,
                    "name": log.get("employee_name", f"Employee {pin}"),
                    "check_ins": [],
                    "check_outs": []
                }
            
            punch_type = log.get("punch_type", "")
            punch_time = log.get("punch_time", "").split("T")[-1][:8] if log.get("punch_time") else ""
            
            if "IN" in punch_type.upper():
                employees[pin]["check_ins"].append(punch_time)
            elif "OUT" in punch_type.upper():
                employees[pin]["check_outs"].append(punch_time)
        
        # Calculate stats
        present = 0
        late = 0
        work_start = "09:00:00"
        
        for emp in employees.values():
            if emp["check_ins"]:
                present += 1
                first_in = min(emp["check_ins"])
                if first_in > work_start:
                    late += 1
        
        return {
            "date": date,
            "total_employees": len(employees),
            "present": present,
            "late": late,
            "total_punches": len(logs),
            "employees": list(employees.values())
        }

    # ==================== DEVICES ====================

    def register_device(self, device: dict) -> dict:
        """Register or update a device"""
        now = datetime.now().isoformat()
        sn = device.get("serial_number")
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # Try to update first
            cursor.execute('''
                UPDATE devices SET status = 'online', last_seen = ?, updated_at = ?
                WHERE serial_number = ?
            ''', (now, now, sn))
            
            if cursor.rowcount == 0:
                # Insert new device
                cursor.execute('''
                    INSERT INTO devices (serial_number, name, location, status, last_seen, created_at, updated_at)
                    VALUES (?, ?, ?, 'online', ?, ?, ?)
                ''', (sn, device.get("name"), device.get("location"), now, now, now))
            
            conn.commit()
        
        device["last_seen"] = now
        device["status"] = "online"
        return device

    def get_devices(self) -> List[dict]:
        """Get all registered devices"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC")
            return [dict(row) for row in cursor.fetchall()]

    def update_device_status(self, serial_number: str, status: str = "online"):
        """Update device status and last seen time"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE devices SET status = ?, last_seen = ?, updated_at = ?
                WHERE serial_number = ?
            ''', (status, now, now, serial_number))
            conn.commit()

    # ==================== PUNCH TIME WINDOWS ====================

    def get_time_windows(self, active_only: bool = True) -> List[dict]:
        """Get all punch time windows"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM punch_time_windows WHERE is_active = 1 ORDER BY priority")
            else:
                cursor.execute("SELECT * FROM punch_time_windows ORDER BY priority")
            return [dict(row) for row in cursor.fetchall()]

    def get_time_window(self, window_id: int) -> Optional[dict]:
        """Get a specific time window by ID"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM punch_time_windows WHERE id = ?", (window_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_time_window(self, window: dict) -> dict:
        """Create a new time window"""
        now = datetime.now().isoformat()
        # Default to all days if not specified
        days_of_week = window.get("days_of_week", "0,1,2,3,4,5,6")
        if isinstance(days_of_week, list):
            days_of_week = ",".join(str(d) for d in days_of_week)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO punch_time_windows (punch_type, start_time, end_time, days_of_week, priority, is_active, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                window.get("punch_type"),
                window.get("start_time"),
                window.get("end_time"),
                days_of_week,
                window.get("priority", 0),
                1 if window.get("is_active", True) else 0,
                window.get("description"),
                now,
                now
            ))
            conn.commit()
            window["id"] = cursor.lastrowid
            window["days_of_week"] = days_of_week
            window["created_at"] = now
            window["updated_at"] = now
        return window

    def update_time_window(self, window_id: int, updates: dict) -> Optional[dict]:
        """Update a time window"""
        updates["updated_at"] = datetime.now().isoformat()
        
        # Convert days_of_week list to string if needed
        if "days_of_week" in updates and isinstance(updates["days_of_week"], list):
            updates["days_of_week"] = ",".join(str(d) for d in updates["days_of_week"])
        
        fields = []
        values = []
        for key, value in updates.items():
            if key not in ["id", "created_at"]:
                if key == "is_active":
                    value = 1 if value else 0
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return self.get_time_window(window_id)
        
        values.append(window_id)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE punch_time_windows SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()
        
        return self.get_time_window(window_id)

    def delete_time_window(self, window_id: int) -> bool:
        """Delete a time window"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM punch_time_windows WHERE id = ?", (window_id,))
            conn.commit()
            return cursor.rowcount > 0

    def determine_punch_type_by_time(self, punch_time: str, check_date: str = None) -> Optional[str]:
        """
        Determine punch type based on time of day and day of week using configured time windows.
        Returns None if no matching window found (will use device status instead).
        
        Args:
            punch_time: DateTime string like "2025-12-02 15:54:20" or just "15:54:20"
            check_date: Optional date string "YYYY-MM-DD" to check specific day. If not provided,
                       extracts from punch_time or uses today.
        
        Days of week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        """
        # Validate punch_time - must be a valid datetime or time string
        if not punch_time or punch_time == "0" or len(str(punch_time)) < 5:
            # Invalid time, return None to use device status instead
            return None
        
        punch_time = str(punch_time)
        
        # Extract date and time portions
        if " " in punch_time:
            date_str, time_str = punch_time.split(" ", 1)
        else:
            time_str = punch_time
            date_str = check_date or datetime.now().strftime("%Y-%m-%d")
        
        # Validate time_str format (should contain ":")
        if ":" not in time_str:
            return None
        
        # Get day of week (0=Monday, 6=Sunday)
        try:
            punch_date = datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = punch_date.weekday()
        except:
            day_of_week = datetime.now().weekday()
        
        # Get HH:MM format
        time_parts = time_str.split(":")
        if len(time_parts) < 2:
            return None
        current_time = f"{time_parts[0]}:{time_parts[1]}"
        
        # Get active time windows
        windows = self.get_time_windows(active_only=True)
        
        for window in windows:
            start = window["start_time"]
            end = window["end_time"]
            
            # Check if this window applies to the current day
            days_str = window.get("days_of_week", "0,1,2,3,4,5,6")
            if days_str:
                applicable_days = [int(d.strip()) for d in days_str.split(",") if d.strip()]
                if day_of_week not in applicable_days:
                    continue  # Skip this window, doesn't apply to this day
            
            # Handle overnight windows (e.g., 22:00 - 06:00)
            if start <= end:
                # Normal window (same day)
                if start <= current_time <= end:
                    return window["punch_type"]
            else:
                # Overnight window
                if current_time >= start or current_time <= end:
                    return window["punch_type"]
        
        return None  # No matching window

    # ==================== SYSTEM SETTINGS ====================

    def get_setting(self, key: str) -> Optional[str]:
        """Get a system setting value"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all system settings as a dictionary"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value, description FROM system_settings")
            return {row["key"]: {"value": row["value"], "description": row["description"]} for row in cursor.fetchall()}

    def set_setting(self, key: str, value: str, description: str = None) -> dict:
        """Set a system setting (upsert)"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key FROM system_settings WHERE key = ?", (key,))
            if cursor.fetchone():
                if description:
                    cursor.execute("UPDATE system_settings SET value = ?, description = ?, updated_at = ? WHERE key = ?",
                                   (value, description, now, key))
                else:
                    cursor.execute("UPDATE system_settings SET value = ?, updated_at = ? WHERE key = ?",
                                   (value, now, key))
            else:
                cursor.execute("INSERT INTO system_settings (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                               (key, value, description, now))
            conn.commit()
        return {"key": key, "value": value, "updated_at": now}

    def is_auto_punch_type_enabled(self) -> bool:
        """Check if automatic punch type determination is enabled"""
        value = self.get_setting("auto_punch_type_enabled")
        return value and value.lower() == "true"

    # ==================== RBAC - USERS ====================

    def create_user(self, user: dict) -> dict:
        """Create a new user"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, department, 
                                   employee_pin, is_active, is_superuser, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.get("username"),
                user.get("email"),
                user.get("password_hash"),
                user.get("full_name"),
                user.get("department"),
                user.get("employee_pin"),
                1 if user.get("is_active", True) else 0,
                1 if user.get("is_superuser", False) else 0,
                now,
                now
            ))
            conn.commit()
            user["id"] = cursor.lastrowid
            user["created_at"] = now
            user["updated_at"] = now
        return user

    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Get user by ID"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_users(self) -> List[dict]:
        """Get all users"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY username")
            return [dict(row) for row in cursor.fetchall()]

    def update_user(self, user_id: int, updates: dict) -> Optional[dict]:
        """Update a user"""
        updates["updated_at"] = datetime.now().isoformat()
        
        fields = []
        values = []
        for key, value in updates.items():
            if key not in ["id", "created_at"]:
                if key in ["is_active", "is_superuser"]:
                    value = 1 if value else 0
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return self.get_user_by_id(user_id)
        
        values.append(user_id)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
            conn.commit()
        
        return self.get_user_by_id(user_id)

    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, user_id))
            conn.commit()

    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ==================== RBAC - ROLES ====================

    def get_role_by_name(self, name: str) -> Optional[dict]:
        """Get role by name"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                role = dict(row)
                role["permissions"] = json.loads(role["permissions"]) if role["permissions"] else []
                return role
            return None

    def get_role_by_id(self, role_id: int) -> Optional[dict]:
        """Get role by ID"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()
            if row:
                role = dict(row)
                role["permissions"] = json.loads(role["permissions"]) if role["permissions"] else []
                return role
            return None

    def get_all_roles(self) -> List[dict]:
        """Get all roles"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM roles ORDER BY name")
            roles = []
            for row in cursor.fetchall():
                role = dict(row)
                role["permissions"] = json.loads(role["permissions"]) if role["permissions"] else []
                roles.append(role)
            return roles

    def create_role(self, role: dict) -> dict:
        """Create a new role"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO roles (name, description, permissions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                role.get("name"),
                role.get("description"),
                json.dumps(role.get("permissions", [])),
                now,
                now
            ))
            conn.commit()
            role["id"] = cursor.lastrowid
            role["created_at"] = now
            role["updated_at"] = now
        return role

    # ==================== RBAC - USER ROLES ====================

    def assign_role_to_user(self, user_id: int, role_id: int):
        """Assign a role to a user"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO user_roles (user_id, role_id, assigned_at)
                VALUES (?, ?, ?)
            ''', (user_id, role_id, now))
            conn.commit()

    def remove_role_from_user(self, user_id: int, role_id: int):
        """Remove a role from a user"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_roles WHERE user_id = ? AND role_id = ?", (user_id, role_id))
            conn.commit()

    def get_user_roles(self, user_id: int) -> List[dict]:
        """Get all roles assigned to a user"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.* FROM roles r
                JOIN user_roles ur ON r.id = ur.role_id
                WHERE ur.user_id = ?
            ''', (user_id,))
            roles = []
            for row in cursor.fetchall():
                role = dict(row)
                role["permissions"] = json.loads(role["permissions"]) if role["permissions"] else []
                roles.append(role)
            return roles

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user (aggregated from all roles)"""
        roles = self.get_user_roles(user_id)
        permissions = set()
        for role in roles:
            for perm in role.get("permissions", []):
                if perm == "*":
                    return ["*"]  # Admin has all permissions
                permissions.add(perm)
        return list(permissions)

    def user_has_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has a specific permission"""
        # Check if user is superuser
        user = self.get_user_by_id(user_id)
        if user and user.get("is_superuser"):
            return True
        
        permissions = self.get_user_permissions(user_id)
        if "*" in permissions:
            return True
        
        # Check exact match or wildcard
        for perm in permissions:
            if perm == permission:
                return True
            # Check wildcard patterns (e.g., "employees:*" matches "employees:read")
            if perm.endswith(":*") and permission.startswith(perm[:-1]):
                return True
        
        return False

    # ==================== RBAC - AUDIT LOGS ====================

    def add_audit_log(self, log: dict):
        """Add an audit log entry"""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_logs (user_id, action, resource, resource_id, details, ip_address, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log.get("user_id"),
                log.get("action"),
                log.get("resource"),
                log.get("resource_id"),
                json.dumps(log.get("details")) if log.get("details") else None,
                log.get("ip_address"),
                log.get("user_agent"),
                now
            ))
            conn.commit()

    def get_audit_logs(self, user_id: Optional[int] = None, limit: int = 100) -> List[dict]:
        """Get audit logs, optionally filtered by user"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            else:
                cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
@lru_cache()
def get_database() -> Database:
    """Get the database instance (singleton)"""
    return Database()
