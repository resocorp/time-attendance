# ✅ Render Deployment Checklist

Quick checklist for deploying to Render.com

---

## 📋 Pre-Deployment

- [ ] All code tested locally
- [ ] Device connectivity confirmed
- [ ] Supabase credentials ready
- [ ] GitHub account created
- [ ] Render account created (https://render.com)

---

## 🚀 Deployment Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit - Ready for Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/zk-attendance-pro.git
git push -u origin main
```

- [ ] Repository created on GitHub
- [ ] Code pushed successfully

### 2. Create Render Service

- [ ] Logged into Render dashboard
- [ ] Connected GitHub repository
- [ ] Service name: `zk-attendance-pro`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Plan: Free

### 3. Environment Variables

Add these in Render dashboard:

- [ ] `SUPABASE_URL` = `https://irffhtkpfdpvvrjcpimk.supabase.co`
- [ ] `SUPABASE_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (your anon key)
- [ ] `SECRET_KEY` = (Click "Generate" button)
- [ ] `ENVIRONMENT` = `production`
- [ ] `DEBUG` = `false`
- [ ] `ORG_NAME` = `My Company` (or your org name)
- [ ] `ORG_TIMEZONE` = `Africa/Lagos` (or your timezone)
- [ ] `WORK_START_TIME` = `09:00`
- [ ] `WORK_END_TIME` = `17:00`

### 4. Deploy

- [ ] Clicked "Create Web Service"
- [ ] Build completed successfully
- [ ] Service is live (green status)
- [ ] Got public URL (e.g., `https://zk-attendance-pro.onrender.com`)

---

## ✅ Post-Deployment Verification

### Test Endpoints

- [ ] Health check: `https://your-app.onrender.com/` returns 200 OK
- [ ] API docs accessible: `https://your-app.onrender.com/docs`
- [ ] Devices endpoint: `https://your-app.onrender.com/api/devices`

### Configure K60 Device

- [ ] Updated Server URL to: `https://your-app.onrender.com/iclock/cdata`
- [ ] Cloud Server enabled on device
- [ ] Device rebooted

### Verify Connection

- [ ] Device registration appears in Render logs
- [ ] Device shows in `/api/devices` endpoint
- [ ] Test punch creates attendance log
- [ ] Log appears in `/api/logs` endpoint

---

## 🔧 Optional: Keep Service Alive

- [ ] UptimeRobot account created
- [ ] Monitor added for your Render URL
- [ ] Monitoring interval: 5 minutes
- [ ] Monitor is active

---

## 📊 Monitoring

- [ ] Bookmarked Render dashboard
- [ ] Logs tab accessible
- [ ] Metrics visible
- [ ] No errors in logs

---

## 🎯 Success Criteria

✅ All checks above completed
✅ Device connecting successfully
✅ Attendance logs being recorded
✅ No errors in production logs
✅ Service responding within acceptable time

---

## 📞 Your Deployment Info

**Fill this in after deployment:**

- **Render URL**: `https://_____________________.onrender.com`
- **GitHub Repo**: `https://github.com/_____/_____`
- **Deployment Date**: `___________`
- **Device Serial**: `TNA82350002`
- **Supabase Project**: `zk-attendance`

---

## 🐛 Common Issues

**Build fails**:
- Check `requirements.txt` syntax
- Verify Python version compatibility

**Service won't start**:
- Check environment variables are set
- Verify start command uses `$PORT`

**Device won't connect**:
- Verify HTTPS URL (not HTTP)
- Check `/iclock/cdata` path is included
- Wait for cold start (~30 seconds)

**App keeps sleeping**:
- Set up UptimeRobot
- Or upgrade to paid plan ($7/month)

---

## 📚 Reference Documents

- **Full Guide**: See `RENDER_DEPLOYMENT.md`
- **Render Docs**: https://render.com/docs/deploy-fastapi
- **Support**: https://render.com/docs

---

**Ready to deploy? Start with Step 1! 🚀**
