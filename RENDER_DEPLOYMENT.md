# 🚀 Render.com Deployment Guide

Complete guide to deploy ZK Attendance Pro to Render.com (Free Tier)

---

## 📋 Prerequisites

- [x] GitHub account
- [x] Render.com account (free) - https://render.com
- [x] Supabase project with credentials
- [x] Git installed locally

---

## 🎯 Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)

```bash
# Navigate to project directory
cd "c:\Users\conwu\Downloads\winsurf projects\time&attendance"

# Initialize git
git init

# Create .gitignore
echo "venv/" > .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".env" >> .gitignore
echo "data/" >> .gitignore
echo ".DS_Store" >> .gitignore
```

### 1.2 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `zk-attendance-pro`
3. Description: `Cloud-native time & attendance system for ZKTeco K60 devices`
4. Visibility: **Private** (recommended) or Public
5. Click **Create repository**

### 1.3 Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Initial commit - Ready for Render deployment"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/zk-attendance-pro.git

# Push to GitHub
git push -u origin main
```

---

## 🌐 Step 2: Deploy to Render

### 2.1 Create Render Account

1. Go to https://render.com
2. Click **Get Started for Free**
3. Sign up with GitHub (recommended for easy integration)

### 2.2 Create New Web Service

1. **Dashboard** → Click **New +** → Select **Web Service**

2. **Connect Repository**:
   - Click **Connect account** (if first time)
   - Authorize Render to access your GitHub
   - Find and select `zk-attendance-pro` repository
   - Click **Connect**

3. **Configure Service**:
   ```
   Name: zk-attendance-pro
   Region: Oregon (or closest to you)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

4. **Advanced Settings** (expand):
   - **Health Check Path**: `/`
   - **Auto-Deploy**: Yes (recommended)

### 2.3 Add Environment Variables

Click **Add Environment Variable** for each:

| Key | Value | Notes |
|-----|-------|-------|
| `SUPABASE_URL` | `https://irffhtkpfdpvvrjcpimk.supabase.co` | From your .env file |
| `SUPABASE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` | Your anon/public key |
| `SECRET_KEY` | Click **Generate** | Auto-generate secure key |
| `ENVIRONMENT` | `production` | Production mode |
| `DEBUG` | `false` | Disable debug in production |
| `ORG_NAME` | `My Company` | Your organization name |
| `ORG_TIMEZONE` | `Africa/Lagos` | Your timezone |
| `WORK_START_TIME` | `09:00` | Work start time |
| `WORK_END_TIME` | `17:00` | Work end time |

### 2.4 Deploy

1. Click **Create Web Service**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Start your application
   - Assign a public URL

**Deployment takes ~2-3 minutes**

---

## ✅ Step 3: Verify Deployment

### 3.1 Check Deployment Status

Watch the **Logs** tab in Render dashboard. Look for:

```
✓ Build successful
✓ Starting service...
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:10000
INFO:     Application startup complete
```

### 3.2 Get Your Public URL

Your app will be available at:
```
https://zk-attendance-pro.onrender.com
```

(Or similar - Render will show exact URL in dashboard)

### 3.3 Test the Endpoints

**Health Check**:
```bash
curl https://zk-attendance-pro.onrender.com/
```

Expected response:
```json
{
  "status": "online",
  "app": "ZK Attendance Pro",
  "version": "1.0.0",
  "devices_connected": 0
}
```

**API Documentation**:
Open in browser: `https://zk-attendance-pro.onrender.com/docs`

---

## 📱 Step 4: Configure K60 Device

### 4.1 Update Device Server URL

On your K60 device:

1. Go to: **Menu** → **Comm** → **Cloud Server**

2. **Server URL**: 
   ```
   https://zk-attendance-pro.onrender.com/iclock/cdata
   ```
   
   ⚠️ **Important**: 
   - Use `https://` (not `http://`)
   - Include full path `/iclock/cdata`
   - No trailing slash

3. **Enable Cloud Server**: `On`

4. **Save** and **Reboot** device

### 4.2 Verify Connection

**Watch Render Logs**:
1. Go to Render dashboard
2. Click on your service
3. Click **Logs** tab
4. Look for device registration:

```
📡 Device Request: SN=TNA82350002, table=options, command=registry
✅ Device TNA82350002 attempting registration
```

**Check Devices API**:
```bash
curl https://zk-attendance-pro.onrender.com/api/devices
```

Should show your device!

---

## 🔧 Step 5: Keep Service Alive (Optional)

Render free tier sleeps after 15 minutes of inactivity. Your K60 device will wake it up automatically, but there's a ~30 second cold start.

### Option A: UptimeRobot (Recommended)

1. Go to https://uptimerobot.com (free)
2. Sign up
3. **Add New Monitor**:
   - Monitor Type: `HTTP(s)`
   - Friendly Name: `ZK Attendance Pro`
   - URL: `https://zk-attendance-pro.onrender.com/`
   - Monitoring Interval: `5 minutes`
4. Save

This pings your app every 5 minutes to keep it warm.

### Option B: Cron-job.org

1. Go to https://cron-job.org (free)
2. Sign up
3. Create cronjob:
   - URL: `https://zk-attendance-pro.onrender.com/`
   - Interval: `Every 10 minutes`

---

## 📊 Monitoring & Maintenance

### View Logs

**Real-time logs**:
1. Render Dashboard → Your Service → **Logs** tab
2. See all device requests, attendance logs, errors

**Download logs**:
- Click **Download Logs** button for historical data

### View Metrics

**Render Dashboard** shows:
- CPU usage
- Memory usage
- Request count
- Response times
- Deployment history

### Check Device Status

**API Endpoints**:
- Devices: `https://your-app.onrender.com/api/devices`
- Logs: `https://your-app.onrender.com/api/logs`
- Dashboard: `https://your-app.onrender.com/monitor`

---

## 🔄 Update & Redeploy

### Automatic Deployment

When you push to GitHub, Render auto-deploys:

```bash
# Make changes to your code
git add .
git commit -m "Add new feature"
git push origin main
```

Render automatically:
1. Detects the push
2. Builds new version
3. Deploys with zero downtime

### Manual Deployment

In Render Dashboard:
1. Go to your service
2. Click **Manual Deploy** → **Deploy latest commit**

---

## 🐛 Troubleshooting

### Build Failed

**Check Render Logs** for errors:
- Missing dependencies → Update `requirements.txt`
- Python version → Render uses Python 3.11 by default
- Syntax errors → Fix in code

### Service Won't Start

**Common issues**:

1. **Port binding**: Render provides `$PORT` env var
   - ✅ Correct: `--port $PORT`
   - ❌ Wrong: `--port 8000`

2. **Missing env vars**: Check all required vars are set

3. **Database connection**: Verify Supabase credentials

### Device Won't Connect

1. **Check URL**: Must be exact `https://your-app.onrender.com/iclock/cdata`
2. **Check logs**: See what device is sending
3. **Cold start**: First request after sleep takes ~30 seconds
4. **Firewall**: Ensure device can reach internet

### App Keeps Sleeping

**Solutions**:
1. Set up UptimeRobot (recommended)
2. Upgrade to paid plan ($7/month) for always-on
3. Your K60 polling keeps it alive if interval < 15 min

---

## 💰 Costs & Limits

### Free Tier Includes:
- ✅ 750 hours/month (enough for 24/7 with one service)
- ✅ 512 MB RAM
- ✅ Shared CPU
- ✅ 100 GB bandwidth/month
- ✅ Automatic SSL
- ✅ Custom domains
- ⚠️ Sleeps after 15 min inactivity
- ⚠️ Cold start: ~30 seconds

### When to Upgrade ($7/month):
- Need always-on (no sleep)
- More RAM (512 MB → 2 GB)
- Faster response times
- Multiple services

---

## 🎯 Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render service created
- [ ] Environment variables configured
- [ ] Deployment successful (green status)
- [ ] Health check returns 200 OK
- [ ] API docs accessible at `/docs`
- [ ] K60 device configured with HTTPS URL
- [ ] Device registration appears in logs
- [ ] Attendance punches recorded
- [ ] UptimeRobot monitoring set up (optional)

---

## 📞 Support & Resources

**Render Documentation**:
- https://render.com/docs
- https://render.com/docs/deploy-fastapi

**Your App URLs** (after deployment):
- App: `https://zk-attendance-pro.onrender.com`
- API Docs: `https://zk-attendance-pro.onrender.com/docs`
- Health: `https://zk-attendance-pro.onrender.com/`
- Devices: `https://zk-attendance-pro.onrender.com/api/devices`
- Logs: `https://zk-attendance-pro.onrender.com/api/logs`

**Render Dashboard**:
- https://dashboard.render.com

---

## 🚀 Next Steps

After successful deployment:

1. ✅ **Test device connectivity**
2. ✅ **Monitor logs for 24 hours**
3. 🔄 **Set up Supabase sync** (if not already)
4. 🔄 **Build admin dashboard**
5. 🔄 **Add user authentication**
6. 🔄 **Configure RBAC policies**
7. 🔄 **Set up automated reports**

---

**Deployment complete! Your ZK Attendance Pro is now running in the cloud! 🎉**
