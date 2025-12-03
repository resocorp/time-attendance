# 🔧 K60 Connection Troubleshooting Guide

## ✅ What We Know

**Good News:**
- ✅ Server is RUNNING on http://192.168.100.92:8000
- ✅ Network connectivity is PERFECT (ping successful)
- ✅ Device **IS** trying to connect!
- ✅ Device Serial Number detected: **TNA82350002**

**Issue:**
- ❌ Device requests are getting 404 errors
- Likely cause: URL configuration on device

---

## 🎯 Step-by-Step Fix

### Step 1: Double-Check Server URL on K60

On your K60 device:

1. Go to: **Menu → Comm → Cloud Server** (or **ADMS**)

2. **CRITICAL**: Check the Server URL is EXACTLY:
   ```
   http://192.168.100.92:8000/iclock/cdata
   ```

3. **Common Mistakes to Avoid:**
   - ❌ `http://192.168.100.92:8000/iclock/cdatanothing` (typo!)
   - ❌ `http://192.168.100.92:8000` (missing `/iclock/cdata`)
   - ❌ `http://192.168.100.92:8000/iclock` (missing `/cdata`)
   - ❌ Extra spaces or characters

4. **If you made a typo**, fix it and save

---

### Step 2: Alternative K60 Configuration Method

Some ZKTeco devices use separate fields instead of full URL:

**Option A: Full URL Field**
- Server URL: `http://192.168.100.92:8000/iclock/cdata`

**Option B: Separate Fields**
If your menu has separate fields, configure like this:
- Server IP: `192.168.100.92`
- Port: `8000`
- Path: `/iclock/cdata`
- Protocol: `HTTP` (not HTTPS)

**Option C: Different Menu Structure**
- Host: `192.168.100.92`
- Port: `8000`
- Enable: `Yes` or `On`

---

### Step 3: Check Other K60 Settings

1. **Serial Number** (Menu → System → Device Info)
   - Current: `TNA82350002` ✅ (detected by server)
   - This is correct!

2. **Cloud Server Enable** (in Comm → Cloud Server menu)
   - Must be set to: `Enabled` or `On`

3. **Upload Interval** (optional)
   - Set to: `30` seconds
   - Or: `1` minute

4. **Connection Mode**
   - Should be: `Push` or `ADMS` or `Cloud`
   - NOT: `Pull` or `P2P`

---

### Step 4: Save and Reboot Device

1. **Save all settings**
2. **Reboot the K60 device**:
   - Menu → System → Power → Reboot
   - Or power cycle (unplug/replug)

3. **Wait 30 seconds** for device to start up

---

### Step 5: Watch Server Logs

After device reboots:

1. **Look at your terminal/console** where uvicorn is running

2. **Expected output** (when working):
   ```
   🔔 INCOMING DEVICE REQUEST: GET http://192.168.100.92:8000/iclock/cdata?SN=TNA82350002...
   📡 Device Request: SN=TNA82350002, table=options, command=registry
   ✅ Device TNA82350002 attempting registration
   ```

3. **If you see 404 errors**, the URL is still wrong on the device

---

### Step 6: Test Basic Connectivity

**Test 1: Can device reach server at all?**

On your K60 device, try accessing the server web interface:
- Menu → Comm → Test Connection (if available)
- Or check if device shows "Server: Online" or similar status

**Test 2: From your computer**

Open in browser: http://192.168.100.92:8000/monitor
- Should show dashboard
- "Devices Connected" should change to 1 when K60 connects

---

## 🔍 Common K60 Menu Variations

Different firmware versions have different menu names:

### Variation 1: (Most Common)
```
Menu → Comm → Cloud Server
  - Server URL: http://192.168.100.92:8000/iclock/cdata
  - Enable: On
```

### Variation 2:
```
Menu → Communication → ADMS
  - ADMS Server: http://192.168.100.92:8000/iclock/cdata
  - ADMS Enable: Yes
```

### Variation 3:
```
Menu → Options → Comm → Push Protocol
  - Server: 192.168.100.92:8000/iclock/cdata
  - Push Mode: Enable
```

### Variation 4: (Older firmware)
```
Menu → Comm → Server Settings
  - IP: 192.168.100.92
  - Port: 8000
  - Path: /iclock/cdata
```

---

## 🧪 Verify Configuration

### Checklist:

- [ ] Server URL contains `192.168.100.92:8000`
- [ ] Server URL contains `/iclock/cdata` at the end
- [ ] No typos or extra characters
- [ ] Cloud Server/ADMS is **Enabled**
- [ ] Device serial number is visible (TNA82350002)
- [ ] Device rebooted after saving
- [ ] Watching terminal logs for connection attempts

---

## 📊 What to Look For in Logs

### Success Pattern:
```
🔔 INCOMING DEVICE REQUEST: GET http://...
📡 Device Request: SN=TNA82350002, table=options, command=registry
   Full URL: http://192.168.100.92:8000/iclock/cdata?SN=TNA82350002&options=all...
   All params: {'SN': 'TNA82350002', 'table': 'options', 'c': 'registry', ...}
✅ Device TNA82350002 attempting registration
```

### Failure Pattern (404):
```
🔔 INCOMING DEVICE REQUEST: GET http://...
❌ Response: 404
```
This means URL is wrong on device!

---

## 🔥 If Still Not Working

### Try Alternative Server Path

Some devices might expect slightly different paths. Try these URLs on the K60:

1. `http://192.168.100.92:8000/iclock/cdata`  (current - most common)
2. `http://192.168.100.92:8000/iclock/`  (shorter version)
3. `http://192.168.100.92:8000/iclock`  (no trailing slash)

### Check Firmware Version

1. Menu → System → Device Info → Firmware Version
2. Note the version number
3. Some very old firmware might not support ADMS push mode

### Factory Reset (Last Resort)

If nothing works:
1. Backup any enrolled users
2. Menu → System → Factory Reset
3. Reconfigure network and server settings

---

## 📞 Next Steps

Once you see this in the logs:
```
✅ Device TNA82350002 attempting registration
```

**You're connected!** Then:

1. Test a punch on the device
2. Check http://192.168.100.92:8000/monitor
3. Should see the attendance log appear
4. Ready to proceed to Phase 2 (Supabase integration)

---

## 💡 Quick Test

**Right now, please:**

1. Go to K60: **Menu → Comm → Cloud Server**
2. Look at the "Server URL" field
3. Tell me EXACTLY what it says (including any typos)
4. We'll fix it together!
