# PowerShell One-Click Commit, Push & Live Deploy Script
param (
    [string]$msg = "Update codebase and deploy to live server"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 Starting Deployment Process..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Git Add & Commit
Write-Host "`n[1/3] Committing changes..." -ForegroundColor Yellow
git add .
try {
    git commit -m "$msg"
} catch {
    Write-Host "No changes to commit, proceeding..." -ForegroundColor Gray
}

# 2. Git Push
Write-Host "`n[2/3] Pushing to GitHub (main branch)..." -ForegroundColor Yellow
git push origin main

# 3. Live Server Deployment
Write-Host "`n[3/3] Deploying to Live Server (157.151.152.144)..." -ForegroundColor Yellow
ssh -o StrictHostKeyChecking=no -i "C:\Users\pagup\Desktop\Code\Django\ssh-key-2026-07-15.key" ubuntu@157.151.152.144 "cd /home/ubuntu/digital_library && git pull origin main && venv/bin/pip install -r requirements.txt && venv/bin/python manage.py migrate && venv/bin/python manage.py collectstatic --noinput && sudo systemctl restart gunicorn-digital_library"

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "✅ Deployment Completed Successfully!" -ForegroundColor Green
Write-Host "🌐 Live Site: http://157.151.152.144/" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
