"""
ZK Attendance Pro - Main Application
ADMS Protocol Server for ZKTeco K60 Devices
"""
from typing import Optional
from fastapi import FastAPI, Request, Query, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse, HTMLResponse, FileResponse
from datetime import datetime, timedelta, timezone
import logging
import os
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.database import get_database
from app.auth import (
    authenticate_user, create_access_token, get_current_user, get_current_active_user,
    require_permission, require_role, require_superuser, get_user_response,
    create_default_admin, hash_password,
    Token, UserLogin, UserRegister, UserResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title="ZK Attendance Pro",
    description="ADMS Protocol Server for ZKTeco Devices",
    version="1.0.0",
    debug=settings.debug
)

# Initialize database
db = get_database()

# In-memory storage (for real-time operations, synced to DB)
device_registry = {}
attendance_logs = []
device_commands = {}
debug_requests = []  # Store all device requests for debugging


def get_local_time() -> datetime:
    """Get current time in the configured timezone (for device sync)"""
    tz_name = settings.org_timezone or "UTC"
    try:
        tz = ZoneInfo(tz_name)
        return datetime.now(tz)
    except Exception:
        # Fallback to UTC if timezone is invalid
        return datetime.now(timezone.utc)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize default admin user on startup"""
    admin = create_default_admin()
    if admin:
        logger.info("✅ Default admin user created: username='admin', password='admin123'")
        logger.warning("⚠️  IMPORTANT: Change the default admin password immediately!")
    else:
        logger.info("✅ Admin user already exists")


# Middleware to log ALL requests for debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log every incoming request from device
    if "/iclock/" in str(request.url):
        logger.warning(f"🔔 DEVICE: {request.method} {request.url}")
    response = await call_next(request)
    if "/iclock/" in str(request.url) and response.status_code != 200:
        logger.error(f"❌ Response: {response.status_code}")
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - redirect to login"""
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/login">
        </head>
        <body>
            <p>Redirecting to login...</p>
        </body>
    </html>
    """


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Login page"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "login.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "online",
        "app": "ZK Attendance Pro",
        "version": "1.0.0",
        "devices_connected": len(device_registry)
    }


@app.get("/monitor", response_class=HTMLResponse)
async def monitor():
    """Live monitoring dashboard"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "monitor.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard with insights"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/device-sync", response_class=HTMLResponse)
async def device_sync_page():
    """Device sync test page"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "device-sync.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/employees", response_class=HTMLResponse)
async def employees_page():
    """Employee management page"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "employees.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/users", response_class=HTMLResponse)
async def users_page():
    """User management page"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "users.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/test", response_class=PlainTextResponse)
async def test_endpoint():
    """Simple test endpoint for device connectivity testing"""
    logger.info("🧪 Test endpoint accessed!")
    return "OK - Server is reachable!"


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/api/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Login with username and password"""
    user = authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    db.update_last_login(user["id"])
    
    # Create access token (sub must be string for JWT)
    access_token = create_access_token(
        data={"sub": str(user["id"]), "username": user["username"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/register", response_model=UserResponse)
async def register(
    user_register: UserRegister,
    current_user: dict = Depends(require_permission("users:write"))
):
    """Register a new user (requires users:write permission)"""
    # Check if username already exists
    existing = db.get_user_by_username(user_register.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing = db.get_user_by_email(user_register.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_data = {
        "username": user_register.username,
        "email": user_register.email,
        "password_hash": hash_password(user_register.password),
        "full_name": user_register.full_name,
        "department": user_register.department,
        "employee_pin": user_register.employee_pin,
        "is_active": True,
        "is_superuser": False
    }
    
    user = db.create_user(user_data)
    
    # Assign default "employee" role
    employee_role = db.get_role_by_name("employee")
    if employee_role:
        db.assign_role_to_user(user["id"], employee_role["id"])
    
    # Log audit
    db.add_audit_log({
        "user_id": current_user["id"],
        "action": "user_created",
        "resource": "users",
        "resource_id": str(user["id"]),
        "details": {"username": user["username"]}
    })
    
    return get_user_response(user)


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return get_user_response(current_user)


@app.post("/api/auth/change-password")
async def change_password(
    request: Request,
    current_user: dict = Depends(get_current_active_user)
):
    """Change current user's password"""
    from app.auth import verify_password
    
    # Get JSON body
    body = await request.json()
    old_password = body.get("old_password")
    new_password = body.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both old_password and new_password are required"
        )
    
    # Verify old password
    if not verify_password(old_password, current_user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password"
        )
    
    # Validate new password
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters"
        )
    
    # Update password
    db.update_user(current_user["id"], {
        "password_hash": hash_password(new_password)
    })
    
    # Log audit
    db.add_audit_log({
        "user_id": current_user["id"],
        "action": "password_changed",
        "resource": "users",
        "resource_id": str(current_user["id"])
    })
    
    return {"message": "Password changed successfully"}


@app.api_route("/iclock/cdata", methods=["GET", "POST"], response_class=PlainTextResponse)
async def cdata(request: Request):
    """
    Main ADMS endpoint for device communication
    
    Handles ALL device requests including:
    - Device registration (c=registry)
    - Attendance logs (table=ATTLOG)
    - User data sync (table=USER)
    - Operation logs (table=OPERLOG)
    - Device options (table=options)
    - First data sync (table=FIRSTDATA)
    """
    
    # Get all query parameters
    params = dict(request.query_params)
    SN = params.get("SN", "UNKNOWN")
    table = params.get("table", "")
    c = params.get("c", "")
    
    # Log ALL parameters for debugging
    logger.info(f"📡 Device Request: SN={SN}, table={table}, command={c}, method={request.method}")
    logger.info(f"   Full URL: {request.url}")
    logger.info(f"   All params: {params}")
    
    # Always register/update device on any request
    if SN != "UNKNOWN":
        device_registry[SN] = {
            "serial_number": SN,
            "last_seen": datetime.now().isoformat(),
            "status": "online",
            "last_table": table,
            "last_command": c
        }
    
    # Handle device registration
    if c == "registry":
        logger.info(f"✅ Device {SN} registered successfully!")
        # Return device configuration
        return "OK"
    
    # Handle attendance logs (ATTLOG)
    if table == "ATTLOG":
        body = await request.body()
        if body:
            logs_text = body.decode("utf-8", errors="ignore").strip()
            logger.info(f"📝 RAW ATTLOG DATA from {SN}:")
            logger.info(f"   Raw: {logs_text[:1000]}")
            
            if logs_text:
                lines = logs_text.splitlines()
                
                for line in lines:
                    if not line.strip():
                        continue
                    
                    logger.info(f"   Line: {line}")
                    # Parse log line
                    log_data = parse_log_line(line)
                    log_data["device_sn"] = SN
                    log_data["received_at"] = datetime.now().isoformat()
                    log_data["raw_line"] = line  # Store raw for debugging
                    
                    # Store in memory
                    attendance_logs.append(log_data)
                    logger.info(f"   ✅ STORED IN MEMORY: {log_data}")
                    
                    # Save to database for persistence
                    if log_data.get("PIN"):
                        try:
                            db.add_attendance_log({
                                "pin": log_data.get("PIN"),
                                "device_sn": SN,
                                "punch_time": log_data.get("DateTime", datetime.now().isoformat()).replace(" ", "T"),
                                "punch_type": log_data.get("punch_type"),
                                "verify_method": log_data.get("verify_method"),
                                "work_code": log_data.get("WorkCode"),
                                "raw_data": str(log_data)
                            })
                            logger.info(f"   💾 SAVED TO DATABASE: PIN={log_data.get('PIN')}")
                        except Exception as e:
                            logger.error(f"   ❌ Database save failed: {e}")
        
        return "OK"
    
    # Handle operation logs (OPERLOG) - device operations like user add/delete
    if table == "OPERLOG":
        if request.method == "POST":
            body = await request.body()
            logs_text = body.decode("utf-8").strip()
            if logs_text:
                logger.info(f"📋 Operation Logs from {SN}:")
                for line in logs_text.splitlines():
                    if line.strip():
                        logger.info(f"   → {line}")
        return "OK"
    
    # Handle user data sync (USER)
    if table == "USER":
        if request.method == "POST":
            body = await request.body()
            users_text = body.decode("utf-8").strip()
            
            if users_text:
                logger.info(f"👤 User Data from {SN}:")
                lines = users_text.splitlines()
                
                for line in lines:
                    if not line.strip():
                        continue
                        
                    user_data = parse_user_line(line)
                    logger.info(f"   → {user_data}")
        
        return "OK"
    
    # Handle options/config - RETURN LOCAL TIME FOR DEVICE SYNC
    if table == "options":
        logger.info(f"⚙️  Device {SN} options sync")
        # Return server time in configured timezone
        local_time = get_local_time()
        options_response = f"GET OPTION FROM: {SN}\r\nServerTime={local_time.strftime('%Y-%m-%d %H:%M:%S')}\r\nStamp=0"
        logger.info(f"   Returning ServerTime: {local_time.strftime('%Y-%m-%d %H:%M:%S')} ({settings.org_timezone})")
        return options_response
    
    # Handle FIRSTDATA - initial sync request
    if table == "FIRSTDATA":
        logger.info(f"🔄 Device {SN} requesting first data sync")
        return "OK"
    
    # Handle any other table types
    if table:
        logger.info(f"📦 Device {SN} sent {table} data")
        if request.method == "POST":
            body = await request.body()
            if body:
                logger.info(f"   Body: {body.decode('utf-8', errors='ignore')[:500]}")
        return "OK"
    
    # Default response for any unhandled request
    logger.info(f"✓ Device {SN} - returning OK")
    return "OK"


@app.api_route("/iclock/getrequest", methods=["GET", "POST"], response_class=PlainTextResponse)
async def getrequest(request: Request):
    """
    Device polls for pending commands from server
    
    Server can return commands like:
    - USER ADD PIN=1001\tName=John Doe\tPrivilege=0\tCard=12345678
    - USER DEL PIN=1002
    - DATA QUERY USERINFO PIN=1001
    """
    params = dict(request.query_params)
    SN = params.get("SN", "UNKNOWN")
    
    logger.info(f"📥 Device {SN} polling for commands")
    
    # Update last seen
    if SN in device_registry:
        device_registry[SN]["last_seen"] = datetime.now().isoformat()
    
    # Check if there are pending commands for this device
    if SN in device_commands and device_commands[SN]:
        command = device_commands[SN].pop(0)
        logger.info(f"📤 Sending command to {SN}: {command}")
        return command
    
    # No commands
    return "OK"


@app.api_route("/iclock/devicecmd", methods=["GET", "POST"], response_class=PlainTextResponse)
async def devicecmd(request: Request):
    """
    Device reports command execution results
    """
    params = dict(request.query_params)
    SN = params.get("SN", "UNKNOWN")
    
    body = await request.body()
    result = body.decode("utf-8", errors="ignore").strip()
    
    logger.info(f"✅ Device {SN} command result: {result}")
    
    return "OK"


@app.get("/api/devices")
async def list_devices():
    """API endpoint to view registered devices"""
    return {
        "devices": list(device_registry.values()),
        "total": len(device_registry)
    }


@app.get("/api/server-time")
async def get_server_time():
    """Get current server time in configured timezone (for dashboard clock sync)"""
    local_time = get_local_time()
    return {
        "datetime": local_time.isoformat(),
        "timezone": settings.org_timezone,
        "formatted": local_time.strftime("%Y-%m-%d %H:%M:%S"),
        "date": local_time.strftime("%Y-%m-%d"),
        "time": local_time.strftime("%H:%M:%S")
    }


@app.get("/api/logs")
async def list_logs():
    """API endpoint to view attendance logs from database"""
    try:
        # Get logs from database (persistent)
        db_logs = db.get_attendance_logs(limit=50)
        
        # Also include recent in-memory logs (for real-time display)
        combined_logs = db_logs + attendance_logs[-10:]
        
        # Remove duplicates and sort by time
        seen = set()
        unique_logs = []
        for log in reversed(combined_logs):
            log_key = f"{log.get('pin')}_{log.get('punch_time')}"
            if log_key not in seen:
                seen.add(log_key)
                unique_logs.append(log)
        
        return {
            "logs": list(reversed(unique_logs))[:50],
            "total": len(db_logs),
            "source": "database + memory"
        }
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        # Fallback to memory if database fails
        return {
            "logs": attendance_logs[-50:],
            "total": len(attendance_logs),
            "source": "memory_only"
        }


@app.post("/api/logs/clear")
async def clear_logs():
    """Clear all attendance logs (for testing)"""
    global attendance_logs
    count = len(attendance_logs)
    attendance_logs = []
    logger.info(f"🗑️ Cleared {count} logs")
    return {"status": "cleared", "count": count}


@app.get("/api/debug")
async def get_debug():
    """View all captured device requests for debugging"""
    return {
        "requests": debug_requests[-50:],
        "total": len(debug_requests)
    }


# ==================== EMPLOYEE API ====================

@app.get("/api/employees")
async def list_employees():
    """Get all employees"""
    employees = db.get_all_employees()
    return {"employees": employees, "total": len(employees)}


@app.get("/api/employees/{pin}")
async def get_employee(pin: str):
    """Get a specific employee by PIN"""
    employee = db.get_employee(pin)
    if not employee:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.post("/api/employees")
async def create_employee(request: Request):
    """Create a new employee"""
    from fastapi import HTTPException
    data = await request.json()
    
    # Validate required fields
    if not data.get("pin") or not data.get("name"):
        raise HTTPException(status_code=400, detail="PIN and name are required")
    
    # Check if PIN already exists
    existing = db.get_employee(data["pin"])
    if existing:
        raise HTTPException(status_code=400, detail="Employee with this PIN already exists")
    
    employee = db.create_employee(data)
    logger.info(f"👤 Created employee: {employee['name']} (PIN: {employee['pin']})")
    return employee


@app.put("/api/employees/{pin}")
async def update_employee(pin: str, request: Request):
    """Update an employee"""
    from fastapi import HTTPException
    data = await request.json()
    
    existing = db.get_employee(pin)
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee = db.update_employee(pin, data)
    logger.info(f"👤 Updated employee: {employee['name']} (PIN: {pin})")
    return employee


@app.delete("/api/employees/{pin}")
async def delete_employee(pin: str):
    """Delete an employee"""
    from fastapi import HTTPException
    
    existing = db.get_employee(pin)
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete_employee(pin)
    logger.info(f"👤 Deleted employee PIN: {pin}")
    return {"status": "deleted", "pin": pin}


# ============================================
# TIME WINDOWS & SETTINGS API
# ============================================

@app.get("/api/settings")
async def get_settings_api():
    """Get all system settings"""
    return db.get_all_settings()


@app.put("/api/settings/{key}")
async def update_setting(key: str, request: Request):
    """Update a system setting"""
    data = await request.json()
    value = data.get("value")
    description = data.get("description")
    
    if value is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Value is required")
    
    result = db.set_setting(key, str(value), description)
    logger.info(f"⚙️ Updated setting: {key} = {value}")
    return result


@app.get("/api/time-windows")
async def get_time_windows(active_only: bool = False):
    """Get all punch time windows"""
    windows = db.get_time_windows(active_only=active_only)
    return {
        "windows": windows,
        "auto_enabled": db.is_auto_punch_type_enabled()
    }


@app.post("/api/time-windows")
async def create_time_window(request: Request):
    """Create a new time window"""
    data = await request.json()
    
    required = ["punch_type", "start_time", "end_time"]
    for field in required:
        if not data.get(field):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"{field} is required")
    
    # Validate punch_type
    valid_types = ["CHECK_IN", "CHECK_OUT", "BREAK_OUT", "BREAK_IN", "OVERTIME_IN", "OVERTIME_OUT"]
    if data["punch_type"] not in valid_types:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"punch_type must be one of: {valid_types}")
    
    window = db.create_time_window(data)
    logger.info(f"⏰ Created time window: {data['punch_type']} {data['start_time']}-{data['end_time']}")
    return window


@app.put("/api/time-windows/{window_id}")
async def update_time_window(window_id: int, request: Request):
    """Update a time window"""
    data = await request.json()
    
    existing = db.get_time_window(window_id)
    if not existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Time window not found")
    
    window = db.update_time_window(window_id, data)
    logger.info(f"⏰ Updated time window {window_id}")
    return window


@app.delete("/api/time-windows/{window_id}")
async def delete_time_window(window_id: int):
    """Delete a time window"""
    existing = db.get_time_window(window_id)
    if not existing:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Time window not found")
    
    db.delete_time_window(window_id)
    logger.info(f"⏰ Deleted time window {window_id}")
    return {"status": "deleted", "id": window_id}


@app.get("/api/test-punch-type")
async def test_punch_type(time: str = None, date: str = None):
    """
    Test what punch type would be assigned for a given time and date.
    If no time provided, uses current time.
    If no date provided, uses today.
    
    Example: /api/test-punch-type?time=09:30&date=2025-12-02
    
    Days of week: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
    """
    now = datetime.now()
    
    if not time:
        time = now.strftime("%H:%M")
    
    if not date:
        date = now.strftime("%Y-%m-%d")
    
    # Ensure time has seconds for the function
    if len(time.split(":")) == 2:
        time = f"{time}:00"
    
    # Combine date and time for the function
    full_datetime = f"{date} {time}"
    
    punch_type = db.determine_punch_type_by_time(full_datetime)
    auto_enabled = db.is_auto_punch_type_enabled()
    
    # Get day of week name
    try:
        test_date = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = test_date.weekday()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[day_of_week]
    except:
        day_of_week = now.weekday()
        day_name = "Unknown"
    
    return {
        "input_time": time,
        "input_date": date,
        "day_of_week": day_of_week,
        "day_name": day_name,
        "determined_punch_type": punch_type,
        "auto_punch_enabled": auto_enabled,
        "would_use": punch_type if auto_enabled and punch_type else "DEVICE_STATUS"
    }


@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    """Settings page for time window configuration"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "settings.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/reports", response_class=HTMLResponse)
async def reports_page():
    """Reports and analytics page"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "reports.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/stats")
async def get_stats(date: str = None):
    """Get attendance statistics for a specific date"""
    from collections import defaultdict
    
    # Use today if no date provided
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # Filter logs for the specified date
    day_logs = [log for log in attendance_logs if log.get("DateTime", "").startswith(date)]
    
    # Group by employee PIN
    employees = defaultdict(lambda: {"check_ins": [], "check_outs": []})
    
    for log in day_logs:
        pin = log.get("PIN", "Unknown")
        punch_type = log.get("punch_type", log.get("Status", ""))
        time = log.get("DateTime", "").split(" ")[-1] if log.get("DateTime") else ""
        
        if punch_type in ["CHECK_IN", "0"]:
            employees[pin]["check_ins"].append(time)
        elif punch_type in ["CHECK_OUT", "1"]:
            employees[pin]["check_outs"].append(time)
    
    # Calculate statistics
    present = 0
    late = 0
    total_hours = 0
    arrival_times = []
    departure_times = []
    
    WORK_START = "09:00"
    
    for pin, data in employees.items():
        if data["check_ins"]:
            present += 1
            first_in = min(data["check_ins"])
            arrival_times.append(first_in)
            
            if first_in > WORK_START:
                late += 1
        
        if data["check_outs"]:
            last_out = max(data["check_outs"])
            departure_times.append(last_out)
            
            if data["check_ins"]:
                # Calculate hours worked
                try:
                    first_in = min(data["check_ins"])
                    in_parts = first_in.split(":")
                    out_parts = last_out.split(":")
                    in_mins = int(in_parts[0]) * 60 + int(in_parts[1])
                    out_mins = int(out_parts[0]) * 60 + int(out_parts[1])
                    hours = (out_mins - in_mins) / 60
                    total_hours += hours
                except:
                    pass
    
    return {
        "date": date,
        "total_employees": len(employees),
        "present": present,
        "absent": 0,  # Would need employee roster to calculate
        "late": late,
        "total_punches": len(day_logs),
        "avg_arrival": calculate_avg_time(arrival_times) if arrival_times else None,
        "avg_departure": calculate_avg_time(departure_times) if departure_times else None,
        "avg_hours": round(total_hours / present, 1) if present > 0 else 0,
        "on_time_rate": round((present - late) / present * 100) if present > 0 else 0
    }


def calculate_avg_time(times: list) -> str:
    """Calculate average time from list of HH:MM:SS strings"""
    if not times:
        return None
    
    total_mins = 0
    for t in times:
        parts = t.split(":")
        total_mins += int(parts[0]) * 60 + int(parts[1])
    
    avg_mins = total_mins // len(times)
    hours = avg_mins // 60
    mins = avg_mins % 60
    return f"{hours:02d}:{mins:02d}"


@app.post("/api/device/add-user")
async def add_user_to_device(request: Request):
    """
    Add a user to the device
    
    Accepts JSON body with:
        pin: User PIN (unique identifier)
        name: User name (max 24 chars)
        device_sn: Device serial number (optional, uses first connected device)
        card: Card number (optional)
        privilege: 0=User, 14=Admin (optional)
    """
    data = await request.json()
    pin = data.get("pin")
    name = data.get("name", "")[:24]  # Truncate to 24 chars
    card = data.get("card", "")
    privilege = data.get("privilege", 0)
    
    # Get device_sn from request or use first connected device
    device_sn = data.get("device_sn")
    if not device_sn:
        if device_registry:
            device_sn = list(device_registry.keys())[0]
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No devices connected")
    
    if not pin or not name:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="PIN and name are required")
    
    # Build command
    command = f"C:{pin}:DATA USER PIN={pin}\tName={name}\tPri={privilege}"
    if card:
        command += f"\tCard={card}"
    
    if device_sn not in device_commands:
        device_commands[device_sn] = []
    
    device_commands[device_sn].append(command)
    
    logger.info(f"📤 Queued USER ADD for {device_sn}: PIN={pin}, Name={name}")
    
    return {
        "status": "queued",
        "device": device_sn,
        "command": command,
        "message": f"User {name} (PIN={pin}) will be added when device polls"
    }


@app.post("/api/device/delete-user")
async def delete_user_from_device(request: Request):
    """Delete a user from the device"""
    data = await request.json()
    pin = data.get("pin")
    
    # Get device_sn from request or use first connected device
    device_sn = data.get("device_sn")
    if not device_sn:
        if device_registry:
            device_sn = list(device_registry.keys())[0]
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No devices connected")
    
    if not pin:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="PIN is required")
    
    command = f"C:{pin}:DATA DEL USER PIN={pin}"
    
    if device_sn not in device_commands:
        device_commands[device_sn] = []
    
    device_commands[device_sn].append(command)
    
    logger.info(f"📤 Queued USER DEL for {device_sn}: PIN={pin}")
    
    return {
        "status": "queued",
        "device": device_sn,
        "command": command
    }


@app.get("/api/device/pending-commands")
async def get_pending_commands(device_sn: str = None):
    """View pending commands for devices"""
    if device_sn:
        return {
            "device": device_sn,
            "commands": device_commands.get(device_sn, [])
        }
    return {"all_commands": device_commands}


@app.post("/api/device/command")
async def send_device_command(device_sn: str, command: str):
    """
    Send a raw command to device
    
    Example commands:
    - C:1:DATA USER PIN=1\tName=Test User\tPri=0
    - C:1:DATA DEL USER PIN=1
    """
    if device_sn not in device_commands:
        device_commands[device_sn] = []
    
    device_commands[device_sn].append(command)
    
    logger.info(f"📝 Queued command for {device_sn}: {command}")
    
    return {
        "status": "queued",
        "device": device_sn,
        "command": command
    }


# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.get("/api/users", dependencies=[Depends(require_permission("users:read"))])
async def get_users():
    """Get all users (requires users:read permission)"""
    users = db.get_all_users()
    # Remove password hashes from response
    for user in users:
        user.pop("password_hash", None)
    return users


@app.get("/api/users/{user_id}", dependencies=[Depends(require_permission("users:read"))])
async def get_user(user_id: int):
    """Get a specific user (requires users:read permission)"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("password_hash", None)
    return get_user_response(user)


@app.put("/api/users/{user_id}", dependencies=[Depends(require_permission("users:write"))])
async def update_user_endpoint(
    user_id: int,
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update a user (requires users:write permission)"""
    # Don't allow updating password through this endpoint
    updates.pop("password_hash", None)
    updates.pop("password", None)
    
    user = db.update_user(user_id, updates)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log audit
    db.add_audit_log({
        "user_id": current_user["id"],
        "action": "user_updated",
        "resource": "users",
        "resource_id": str(user_id),
        "details": updates
    })
    
    user.pop("password_hash", None)
    return user


@app.delete("/api/users/{user_id}", dependencies=[Depends(require_superuser)])
async def delete_user_endpoint(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a user (requires superuser)"""
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = db.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log audit
    db.add_audit_log({
        "user_id": current_user["id"],
        "action": "user_deleted",
        "resource": "users",
        "resource_id": str(user_id)
    })
    
    return {"message": "User deleted successfully"}


# ==================== ROLE MANAGEMENT ENDPOINTS ====================

@app.get("/api/roles", dependencies=[Depends(require_permission("users:read"))])
async def get_roles():
    """Get all roles (requires users:read permission)"""
    return db.get_all_roles()


@app.post("/api/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_permission("users:write"))])
async def assign_role(
    user_id: int,
    role_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Assign a role to a user (requires users:write permission)"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = db.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    db.assign_role_to_user(user_id, role_id)
    
    # Log audit
    db.add_audit_log({
        "user_id": current_user["id"],
        "action": "role_assigned",
        "resource": "user_roles",
        "resource_id": f"{user_id}:{role_id}",
        "details": {"user_id": user_id, "role_id": role_id, "role_name": role["name"]}
    })
    
    return {"message": f"Role '{role['name']}' assigned to user"}


@app.delete("/api/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_permission("users:write"))])
async def remove_role(
    user_id: int,
    role_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a role from a user (requires users:write permission)"""
    db.remove_role_from_user(user_id, role_id)
    
    # Log audit
    db.add_audit_log({
        "user_id": current_user["id"],
        "action": "role_removed",
        "resource": "user_roles",
        "resource_id": f"{user_id}:{role_id}",
        "details": {"user_id": user_id, "role_id": role_id}
    })
    
    return {"message": "Role removed from user"}


# ==================== AUDIT LOG ENDPOINTS ====================

@app.get("/api/audit-logs", dependencies=[Depends(require_permission("audit:read"))])
async def get_audit_logs(user_id: Optional[int] = None, limit: int = 100):
    """Get audit logs (requires audit:read permission)"""
    return db.get_audit_logs(user_id=user_id, limit=limit)


# ==================== HELPER FUNCTIONS ====================

def parse_log_line(line: str) -> dict:
    """
    Parse ADMS attendance log line
    
    K60 Format (tab-separated): PIN\tDateTime\tStatus\tVerified\t...
    Example: 1\t2025-12-02 15:54:20\t0\t1\t0\t0\t0\t0\t0\t0
    
    Alternative Format: PIN=1001\tDateTime=2025-09-02 14:32:11\tVerified=1\tStatus=0
    
    Punch type determination:
    - If auto_punch_type_enabled is True, uses time-based windows to determine punch type
    - Otherwise, uses the device's Status field
    """
    data = {}
    parts = line.split("\t")
    
    # Check if it's key=value format or positional format
    if "=" in line:
        # Key=value format
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                data[key.strip()] = value.strip()
    else:
        # K60 positional format: PIN, DateTime, Status, Verified, WorkCode, Reserved1, Reserved2, Reserved3, Reserved4, Reserved5
        if len(parts) >= 4:
            data["PIN"] = parts[0].strip()
            data["DateTime"] = parts[1].strip()
            data["Status"] = parts[2].strip()
            data["Verified"] = parts[3].strip()
            if len(parts) > 4:
                data["WorkCode"] = parts[4].strip()
            logger.info(f"   Parsed K60 format: PIN={data.get('PIN')}, DateTime={data.get('DateTime')}, Status={data.get('Status')}, Verified={data.get('Verified')}")
    
    # Add human-readable fields
    if "Verified" in data:
        verify_map = {
            "0": "PASSWORD",
            "1": "FINGERPRINT", 
            "2": "CARD",
            "3": "CARD",
            "4": "FACE",
            "15": "PALM"
        }
        data["verify_method"] = verify_map.get(data["Verified"], f"UNKNOWN({data['Verified']})")
    
    # Determine punch type - either from time windows or device status
    device_status_map = {
        "0": "CHECK_IN",
        "1": "CHECK_OUT",
        "2": "BREAK_OUT",
        "3": "BREAK_IN",
        "4": "OVERTIME_IN",
        "5": "OVERTIME_OUT"
    }
    
    # Store original device status for reference
    if "Status" in data:
        data["device_punch_type"] = device_status_map.get(data["Status"], f"UNKNOWN({data['Status']})")
    
    # Check if automatic time-based punch type is enabled
    if db.is_auto_punch_type_enabled() and "DateTime" in data:
        time_based_type = db.determine_punch_type_by_time(data["DateTime"])
        if time_based_type:
            data["punch_type"] = time_based_type
            data["punch_type_source"] = "TIME_WINDOW"
            logger.info(f"   ⏰ Auto punch type: {time_based_type} (based on time window)")
        else:
            # No matching time window, fall back to device status
            data["punch_type"] = data.get("device_punch_type", "CHECK_IN")
            data["punch_type_source"] = "DEVICE_STATUS"
            logger.info(f"   📱 Using device status: {data['punch_type']} (no matching time window)")
    elif "Status" in data:
        # Auto mode disabled, use device status
        data["punch_type"] = device_status_map.get(data["Status"], f"UNKNOWN({data['Status']})")
        data["punch_type_source"] = "DEVICE_STATUS"
    
    return data


def parse_user_line(line: str) -> dict:
    """
    Parse ADMS user data line
    
    Format: PIN=1001\tName=John Doe\tPrivilege=0\tCard=12345678
    """
    parts = line.split("\t")
    data = {}
    
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            data[key.strip()] = value.strip()
    
    # Add human-readable privilege
    if "Privilege" in data:
        priv_map = {
            "0": "USER",
            "14": "ADMIN"
        }
        data["privilege_name"] = priv_map.get(data["Privilege"], f"UNKNOWN({data['Privilege']})")
    
    return data


# ============================================
# CATCH-ALL for /iclock/ paths - MUST BE LAST!
# Handles malformed paths like /iclock/cdata/iclock/getrequest
# ============================================
@app.api_route("/iclock/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], response_class=PlainTextResponse)
async def iclock_catch_all(request: Request, path: str):
    """
    Catch-all handler for ANY /iclock/ request not matched above
    This ensures we never return 404 for device requests
    """
    params = dict(request.query_params)
    SN = params.get("SN", "UNKNOWN")
    table = params.get("table", "")
    c = params.get("c", "")
    
    # Read body first
    body = b""
    body_text = ""
    if request.method == "POST":
        body = await request.body()
        body_text = body.decode("utf-8", errors="ignore") if body else ""
    
    # Store debug info
    debug_entry = {
        "time": datetime.now().isoformat(),
        "path": path,
        "method": request.method,
        "SN": SN,
        "table": table,
        "c": c,
        "params": params,
        "body_length": len(body),
        "body_preview": body_text[:500] if body_text else ""
    }
    debug_requests.append(debug_entry)
    
    logger.info(f"🔶 CATCH-ALL: /iclock/{path} | SN={SN} | table={table} | body={len(body)}bytes")
    
    # Register device on ANY request
    if SN != "UNKNOWN":
        device_registry[SN] = {
            "serial_number": SN,
            "last_seen": datetime.now().isoformat(),
            "status": "online",
            "last_path": path,
            "last_table": table
        }
        # Save to SQLite
        try:
            db.register_device({"serial_number": SN})
        except Exception as e:
            logger.error(f"Failed to save device to DB: {e}")
    
    # Check if this is a getrequest poll (device asking for commands)
    if "getrequest" in path.lower():
        logger.info(f"📥 Device {SN} polling for commands (via catch-all)")
        # Check if there are pending commands for this device
        if SN in device_commands and device_commands[SN]:
            command = device_commands[SN].pop(0)
            logger.info(f"📤 SENDING COMMAND to {SN}: {command}")
            return command
        return "OK"
    
    # Only parse attendance data for ATTLOG table, skip OPERLOG and others
    if body_text and table and table.upper() == "ATTLOG":
        for line in body_text.strip().splitlines():
            if line.strip():
                try:
                    log_data = parse_log_line(line)
                    log_data["device_sn"] = SN
                    log_data["received_at"] = datetime.now().isoformat()
                    log_data["raw"] = line
                    log_data["source"] = "catch_all"
                    attendance_logs.append(log_data)
                    logger.info(f"   ✅ LOGGED: {log_data}")
                    
                    # Save to SQLite
                    if log_data.get("PIN") and log_data.get("PIN") != "OPLOG 0":
                        try:
                            db.add_attendance_log({
                                "pin": log_data.get("PIN"),
                                "device_sn": SN,
                                "punch_time": log_data.get("DateTime", datetime.now().isoformat()).replace(" ", "T"),
                                "punch_type": log_data.get("punch_type"),
                                "verify_method": log_data.get("verify_method"),
                                "work_code": log_data.get("WorkCode"),
                                "raw_data": log_data
                            })
                            logger.info(f"   💾 Saved to SQLite")
                        except Exception as e:
                            logger.error(f"   ❌ Failed to save to SQLite: {e}")
                except Exception as e:
                    logger.error(f"   ❌ Failed to parse line: {line} - Error: {e}")
    elif body_text and table:
        # Log other table types without parsing as attendance
        logger.info(f"   📦 Received {table} data (not attendance): {body_text[:200]}")
    
    return "OK"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
