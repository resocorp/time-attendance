# Quick Deployment Script for Render
# This script helps prepare your project for deployment

Write-Host "🚀 ZK Attendance Pro - Render Deployment Helper" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git already initialized" -ForegroundColor Green
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env created - Please update with your credentials" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Edit .env file with your Supabase credentials before deploying!" -ForegroundColor Red
    Write-Host ""
}

# Show current status
Write-Host ""
Write-Host "📋 Current Status:" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "📝 Uncommitted changes detected" -ForegroundColor Yellow
} else {
    Write-Host "✅ No uncommitted changes" -ForegroundColor Green
}

# Check for remote
$remote = git remote -v
if ($remote) {
    Write-Host "✅ Git remote configured:" -ForegroundColor Green
    git remote -v
} else {
    Write-Host "⚠️  No git remote configured" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Create a new repository on GitHub" -ForegroundColor White
    Write-Host "2. Run: git remote add origin https://github.com/YOUR_USERNAME/zk-attendance-pro.git" -ForegroundColor White
}

Write-Host ""
Write-Host "📚 Deployment Files Created:" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "✅ render.yaml - Render configuration" -ForegroundColor Green
Write-Host "✅ runtime.txt - Python version" -ForegroundColor Green
Write-Host "✅ Procfile - Start command" -ForegroundColor Green
Write-Host "✅ requirements.txt - Updated with production dependencies" -ForegroundColor Green
Write-Host "✅ RENDER_DEPLOYMENT.md - Complete deployment guide" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT_CHECKLIST.md - Quick checklist" -ForegroundColor Green

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Cyan
Write-Host "1. Review and update .env with your credentials" -ForegroundColor White
Write-Host "2. Create GitHub repository: https://github.com/new" -ForegroundColor White
Write-Host "3. Add remote: git remote add origin <your-repo-url>" -ForegroundColor White
Write-Host "4. Commit changes: git add . && git commit -m 'Ready for deployment'" -ForegroundColor White
Write-Host "5. Push to GitHub: git push -u origin main" -ForegroundColor White
Write-Host "6. Follow RENDER_DEPLOYMENT.md for Render setup" -ForegroundColor White

Write-Host ""
Write-Host "📖 Read the full guide: RENDER_DEPLOYMENT.md" -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to commit now
Write-Host "Would you like to commit the deployment files now? (y/n): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "📦 Staging files..." -ForegroundColor Yellow
    git add .
    
    Write-Host "💾 Committing..." -ForegroundColor Yellow
    git commit -m "Add Render deployment configuration"
    
    Write-Host "✅ Files committed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next: Push to GitHub with 'git push -u origin main'" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Skipped commit. Run manually when ready:" -ForegroundColor Yellow
    Write-Host "  git add ." -ForegroundColor White
    Write-Host "  git commit -m 'Add Render deployment configuration'" -ForegroundColor White
}

Write-Host ""
Write-Host "🎉 Deployment preparation complete!" -ForegroundColor Green
Write-Host ""
