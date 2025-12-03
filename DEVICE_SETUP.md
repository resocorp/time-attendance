# K60 Device Configuration Guide

## ✅ Server Status
- **Server Running**: http://192.168.100.92:8000
- **K60 Device IP**: 192.168.100.188
- **Network**: Both on 192.168.100.x subnet ✓

## 📱 Configure Your K60 Device

### Method 1: Via Device Menu

1. **Access Device Menu**
   - On the K60 touchscreen, go to: `Menu`
   - Enter admin password if prompted

2. **Navigate to Cloud Server Settings**
   - `Menu` → `Comm` → `Cloud Server` (or `ADMS` or `Push Server`)
   - Different firmware versions may have slightly different menu names

3. **Configure Server URL**
   ```
   Server URL: http://192.168.100.92:8000/iclock/cdata
   ```
   
   **Important**: Must include `/iclock/cdata` at the end!

4. **Check/Set Device Serial Number**
   - Go to: `Menu` → `System` → `Device Info`
   - Check the `SN` (Serial Number) field
   - If empty, set it to something like: `K60001`
   - Remember this SN - you'll see it in server logs

5. **Enable Push Mode**
   - Find option like "Cloud Server Enable" or "ADMS Enable"
   - Set to: `Enabled` or `On`

6. **Set Push Interval (Optional)**
   - Look for "Upload Interval" or "Push Interval"
   - Recommended: `30` seconds (for testing)
   - Lower = more frequent updates, but more traffic

7. **Save and Test**
   - Save the settings
   - Device should immediately try to connect
   - You should see connection attempts in the server logs

### Method 2: Via Web Interface (if K60 supports it)

1. **Access Device Web UI**
   - Open browser: `http://192.168.100.188`
   - Login with admin credentials

2. **Configure ADMS Settings**
   - Look for ADMS/Cloud Server section
   - Enter:
     - Server: `192.168.100.92`
     - Port: `8000`
     - Path: `/iclock/cdata`
   - Or full URL: `http://192.168.100.92:8000/iclock/cdata`

3. **Enable and Save**

---

## 🧪 Test the Connection

### Step 1: Check Server Health

Open in browser: http://192.168.100.92:8000

Expected response:
```json
{
  "status": "online",
  "app": "ZK Attendance Pro",
  "version": "1.0.0",
  "devices_connected": 0
}
```

### Step 2: Watch Server Logs

Monitor the terminal/console where the server is running. When device connects, you'll see:

```
📡 Device Request: SN=K60001, table=options, command=registry
✅ Device K60001 attempting registration
```

### Step 3: Check Registered Devices

Open in browser: http://192.168.100.92:8000/api/devices

Expected response (after device connects):
```json
{
  "devices": [
    {
      "serial_number": "K60001",
      "last_seen": "2024-12-02T14:30:00",
      "status": "online"
    }
  ],
  "total": 1
}
```

### Step 4: Test Attendance Logging

1. **Create a punch on the K60**:
   - Use fingerprint/face/card to punch in
   - Or manually enter user ID and verify

2. **Check server logs** - you should see:
```
📝 Attendance Logs from K60001:
   → {'PIN': '1001', 'DateTime': '2024-12-02 14:35:00', 'verify_method': 'FINGERPRINT', 'punch_type': 'CHECK_IN', ...}
```

3. **View logs in browser**: http://192.168.100.92:8000/api/logs

---

## 🔍 Troubleshooting

### Device Not Connecting

**Check 1: Network Connectivity**
```bash
# From your computer, ping the device
ping 192.168.100.188
```
Should get replies. If not, check:
- Device is powered on
- Both on same network
- No network isolation between devices

**Check 2: Firewall**
- Windows Firewall might be blocking port 8000
- Temporarily disable or add rule:
  - Control Panel → Windows Defender Firewall
  - Advanced Settings → Inbound Rules → New Rule
  - Port: 8000, TCP, Allow

**Check 3: Server Running**
- Make sure server is still running (check terminal)
- Try restarting: Ctrl+C, then run again:
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Check 4: Device Settings**
- Verify Server URL is exact: `http://192.168.100.92:8000/iclock/cdata`
- Check device has valid SN set
- Check "Cloud Server" is enabled
- Try rebooting the device

### Device Connects But No Logs

**Check 1: Users Enrolled**
- Ensure users are enrolled in the K60
- Menu → User Management → verify users exist

**Check 2: Time Sync**
- Device time should be correct
- Menu → System → Date/Time

**Check 3: Try Manual Punch**
- Go to device attendance screen
- Enter user ID manually
- Press OK/Verify

### Check Server Logs

Always check the terminal where uvicorn is running - it shows all device communication in real-time with detailed logging.

---

## 📊 API Endpoints for Testing

| Endpoint | Description |
|----------|-------------|
| http://192.168.100.92:8000 | Health check |
| http://192.168.100.92:8000/docs | Interactive API docs (Swagger UI) |
| http://192.168.100.92:8000/api/devices | List registered devices |
| http://192.168.100.92:8000/api/logs | View attendance logs (last 50) |

---

## ✅ Success Checklist

- [ ] Server running on http://192.168.100.92:8000
- [ ] Can access http://192.168.100.92:8000 in browser
- [ ] K60 configured with server URL
- [ ] Device SN is set
- [ ] Cloud Server enabled on device
- [ ] Device appears in `/api/devices`
- [ ] Can see registration in server logs
- [ ] Punch creates log entry
- [ ] Log appears in `/api/logs`

Once all checked, device connectivity is confirmed and we can proceed to add Supabase integration and build the dashboard!

---

## 🔄 Next Steps (After Successful Connection)

1. ✅ Confirm device registration
2. ✅ Confirm attendance logs received
3. 🔄 Add Supabase database integration
4. 🔄 Build real-time dashboard
5. 🔄 Add user management & sync
6. 🔄 Implement RBAC and authentication
