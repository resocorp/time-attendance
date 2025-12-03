# 🚀 ZK Attendance Pro - Quick Start Guide

## ✅ Current Status

**Server is RUNNING!** 🎉

- **Server URL**: http://192.168.100.92:8000
- **Your Computer IP**: 192.168.100.92
- **K60 Device IP**: 192.168.100.188
- **Status**: Both devices on same network ✓

---

## 🌐 Access Points

### 1. Live Monitor Dashboard (Recommended)
**Open in your browser**: http://192.168.100.92:8000/monitor

- Real-time attendance logs
- Device connection status
- Auto-refreshes every 5 seconds
- Visual badges for punch types

### 2. API Documentation
**Open in your browser**: http://192.168.100.92:8000/docs

- Interactive API testing (Swagger UI)
- Try out endpoints directly

### 3. API Endpoints

| URL | Description |
|-----|-------------|
| http://192.168.100.92:8000 | Server health check |
| http://192.168.100.92:8000/monitor | **Live dashboard** |
| http://192.168.100.92:8000/api/devices | List connected devices (JSON) |
| http://192.168.100.92:8000/api/logs | Recent logs (JSON) |
| http://192.168.100.92:8000/docs | API documentation |

---

## 📱 Configure K60 Device NOW

### Step 1: Access Device Menu
On the K60 touchscreen:
1. Tap **Menu**
2. Enter admin password (if prompted)

### Step 2: Configure Cloud Server
Navigate to: **Menu → Comm → Cloud Server**

Set these values:
```
Server URL: http://192.168.100.92:8000/iclock/cdata
```
⚠️ **IMPORTANT**: Must include `/iclock/cdata` at the end!

### Step 3: Check/Set Serial Number
Navigate to: **Menu → System → Device Info**

- Check the **SN** (Serial Number) field
- If empty, set it to: `K60001`
- Remember this number!

### Step 4: Enable Push Mode
In Cloud Server settings:
- Find **"Cloud Server Enable"** or **"ADMS Enable"**
- Set to: **Enabled** or **On**

### Step 5: Save Settings
- Save the configuration
- Device will immediately try to connect

---

## 🧪 Test the Connection

### Test 1: Watch Server Logs
Look at the terminal/console where the server is running.

**When device connects, you'll see:**
```
📡 Device Request: SN=K60001, table=options, command=registry
✅ Device K60001 attempting registration
```

### Test 2: Check Monitor Dashboard
Open: http://192.168.100.92:8000/monitor

**Expected result:**
- "Devices Connected" should show `1`
- Device should appear in the list

### Test 3: Create a Punch
On the K60 device:
1. Use fingerprint/face/card to punch in
2. Or manually enter a user ID

**Monitor dashboard will show:**
- New log appears automatically
- Highlighted in green
- Shows user PIN, time, punch type, verify method

---

## 🐛 Troubleshooting

### Device Not Connecting?

**1. Check Windows Firewall**

Windows might be blocking port 8000. To check:

```powershell
# Run in PowerShell as Administrator
New-NetFirewallRule -DisplayName "ZK Attendance Server" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

Or manually:
- Control Panel → Windows Defender Firewall
- Advanced Settings → Inbound Rules → New Rule
- Port: 8000, TCP, Allow

**2. Verify Network Connection**

```bash
# From Windows Command Prompt, ping the device
ping 192.168.100.188
```

Should get replies. If not:
- Check device is powered on
- Check both on same WiFi/network
- Check router settings (no device isolation)

**3. Verify Server is Running**

Check the terminal - should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

If not running, restart:
```bash
cd "C:\Users\conwu\Downloads\winsurf projects\time&attendance"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**4. Check Device Configuration**

Double-check on K60:
- Server URL: `http://192.168.100.92:8000/iclock/cdata` (exact!)
- Cloud Server: **Enabled**
- Serial Number: Set (e.g., `K60001`)

Try rebooting the device after configuration.

---

## 📊 What to Expect

### When Device First Connects:
1. **Registration** - Device sends initial handshake
2. **Server logs**: `✅ Device K60001 attempting registration`
3. **Monitor shows**: Devices Connected = 1

### When Someone Punches In/Out:
1. **Device captures**: Fingerprint/face/card scan
2. **Sends to server**: Within seconds (real-time mode)
3. **Server logs**: `📝 Attendance Logs from K60001:`
4. **Monitor updates**: New log appears, highlighted in green

### Ongoing:
- Device polls server every 30 seconds (default)
- Sends logs immediately when created
- Monitor auto-refreshes every 5 seconds

---

## ✅ Success Checklist

- [ ] Server running at http://192.168.100.92:8000
- [ ] Can open http://192.168.100.92:8000/monitor in browser
- [ ] K60 configured with correct server URL
- [ ] K60 Serial Number is set
- [ ] Cloud Server enabled on K60
- [ ] See device registration in terminal logs
- [ ] Device appears in monitor dashboard
- [ ] Test punch creates log entry
- [ ] Log appears in monitor (within 5 seconds)

---

## 🎯 Next Steps (After Successful Connection)

Once you confirm:
✅ Device connects and registers
✅ Attendance logs are received
✅ Monitor dashboard shows logs

We can proceed to:
1. **Set up Supabase** - Database for permanent storage
2. **Build Full Dashboard** - With analytics, reports, charts
3. **Add Authentication** - User login with RBAC
4. **Employee Management** - Add/edit employees, sync to device
5. **Advanced Reports** - Daily, monthly, late arrivals, exports

---

## 📞 Need Help?

If you encounter issues:
1. **Check terminal logs** - They show detailed device communication
2. **Check monitor dashboard** - Shows real-time status
3. **Verify network** - Ping device, check firewall
4. **Try device reboot** - Sometimes needed after config changes

---

## 🎉 You're All Set!

Your ADMS server is running and ready to receive attendance data from your ZKTeco K60 device!

**Key URLs to bookmark:**
- 📊 **Monitor Dashboard**: http://192.168.100.92:8000/monitor
- 📚 **API Docs**: http://192.168.100.92:8000/docs

Configure your K60 device now and watch the logs flow in! 🚀
