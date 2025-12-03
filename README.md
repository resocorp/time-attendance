# ZK Attendance Pro

Cloud-native time & attendance system for ZKTeco K60 devices using ADMS Push Protocol.

## 🚀 Quick Start (Local Testing)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional for local testing)
```

### 3. Run the Server

```bash
# Start the FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://0.0.0.0:8000`

### 4. Verify Server is Running

Open your browser to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/
- **View Devices**: http://localhost:8000/api/devices
- **View Logs**: http://localhost:8000/api/logs

## 📱 Configure K60 Device

### Find Your Computer's Local IP

```bash
# Windows:
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.100.x)

# Mac/Linux:
ifconfig
# or
ip addr show
```

### Configure Device (via K60 Menu)

1. **On the K60 device**, go to:
   - `Menu` → `Comm` → `Cloud Server`

2. **Set Server URL**:
   ```
   http://192.168.100.92:8000/iclock/cdata
   ```
   **Note**: The full path `/iclock/cdata` is required!

3. **Set Device Serial Number** (if not set):
   - Check current SN: `Menu` → `System` → `Device Info`
   - If blank, set a unique SN like `K60001`

4. **Enable Cloud Server**:
   - Set to `Enabled` or `On`

5. **Test Connection**:
   - Device should attempt to register immediately
   - Check server logs for connection attempts

## 🧪 Testing the Connection

### Test 1: Device Registration

**Expected behavior**:
- Device sends registration request on connection
- Server logs should show:
  ```
  📡 Device Request: SN=K60001, table=options, command=registry
  ✅ Device K60001 attempting registration
  ```

**Check registered devices**:
```bash
curl http://localhost:8000/api/devices
```

### Test 2: Attendance Log

**Expected behavior**:
- When someone punches in/out on K60
- Server logs should show:
  ```
  📝 Attendance Logs from K60001:
     → {'PIN': '1001', 'DateTime': '2024-12-02 14:30:00', ...}
  ```

**Check received logs**:
```bash
curl http://localhost:8000/api/logs
```

### Test 3: Send Command to Device

**Test adding a user**:
```bash
curl -X POST "http://localhost:8000/api/test-command?device_sn=K60001&command=USER%20ADD%20PIN=9999%09Name=Test%20User%09Privilege=0"
```

The device will pick up this command on next poll (usually within 30 seconds).

## 📊 Current Features (Phase 1)

- ✅ ADMS Protocol Server
- ✅ Device registration
- ✅ Real-time attendance log receiving
- ✅ Device command queue
- ✅ Basic API endpoints for monitoring
- ✅ In-memory storage (for testing)

## 🔄 Next Steps

Once device connectivity is confirmed:

1. **Add Supabase Integration**
   - Store attendance logs in database
   - Implement proper schema
   - Add RLS policies

2. **Add Authentication**
   - Supabase Auth integration
   - JWT token validation
   - RBAC implementation

3. **Build Dashboard**
   - Real-time attendance feed
   - Device status monitoring
   - Employee management

4. **Add Advanced Features**
   - Reports and exports
   - Manual entry
   - User sync with device

## 🐛 Troubleshooting

### Device won't connect

1. **Check firewall**: Ensure port 8000 is not blocked
2. **Check IP address**: Make sure you're using the correct local IP
3. **Check network**: Device and computer must be on same network
4. **Check server logs**: Look for error messages

### Logs not appearing

1. **Verify device is registered**: Check `/api/devices`
2. **Check device clock**: Time sync issues can cause problems
3. **Test with actual punch**: Create attendance event on device

### Server won't start

1. **Port already in use**: Try different port with `--port 8001`
2. **Python version**: Requires Python 3.11+
3. **Dependencies**: Run `pip install -r requirements.txt` again

## 📝 Server Logs

The server provides detailed logging of all device interactions:

- `📡` Device requests
- `✅` Successful operations
- `📝` Attendance logs received
- `👤` User data sync
- `⚙️` Configuration sync
- `📥` Device polling for commands
- `📤` Commands sent to device

## 🔗 Useful Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/iclock/cdata` | GET/POST | ADMS main endpoint |
| `/iclock/getrequest` | GET | Device command polling |
| `/api/devices` | GET | List registered devices |
| `/api/logs` | GET | View attendance logs |
| `/api/test-command` | POST | Send test command to device |
| `/docs` | GET | Interactive API documentation |

## 📚 ADMS Protocol Reference

Based on ZKTeco ADMS documentation:

**Verify Methods**:
- `0` = Password
- `1` = Fingerprint
- `3` = RFID Card
- `4` = Face
- `15` = Palm

**Punch Types**:
- `0` = Check In
- `1` = Check Out
- `2` = Break Out
- `3` = Break In
- `4` = Overtime In
- `5` = Overtime Out

**User Privileges**:
- `0` = Normal User
- `14` = Administrator

## 📧 Support

For issues or questions, check the server logs first - they provide detailed information about all device interactions.
