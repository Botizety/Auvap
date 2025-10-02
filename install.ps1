# AUVAP Installation Script for Windows PowerShell
# This script automates the installation process

Write-Host "=== AUVAP Installation Script ===" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check if in virtual environment
$inVenv = $env:VIRTUAL_ENV
if (-not $inVenv) {
    Write-Host ""
    Write-Host "WARNING: Not in a virtual environment." -ForegroundColor Yellow
    $response = Read-Host "Create and activate virtual environment? (Y/n)"
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        
        Write-Host "Activating virtual environment..." -ForegroundColor Yellow
        & ".\venv\Scripts\Activate.ps1"
        
        Write-Host "Virtual environment activated!" -ForegroundColor Green
    }
}

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null
Write-Host "Pip upgraded successfully!" -ForegroundColor Green

# Install standard dependencies
Write-Host ""
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "(This may take 5-10 minutes)" -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed successfully!" -ForegroundColor Green

# Install CyberBattleSim from GitHub
Write-Host ""
Write-Host "Installing CyberBattleSim from GitHub..." -ForegroundColor Yellow
Write-Host "(This may take 2-3 minutes)" -ForegroundColor Cyan
pip install git+https://github.com/microsoft/CyberBattleSim.git
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: CyberBattleSim installation failed." -ForegroundColor Yellow
    Write-Host "You can still use AUVAP in mock mode without CyberBattleSim." -ForegroundColor Cyan
    $cbsInstalled = $false
} else {
    Write-Host "CyberBattleSim installed successfully!" -ForegroundColor Green
    $cbsInstalled = $true
}

# Create .env file if it doesn't exist
Write-Host ""
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env configuration file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created! Edit it to configure Neo4j and other settings." -ForegroundColor Green
} else {
    Write-Host ".env file already exists." -ForegroundColor Cyan
}

# Run verification tests
Write-Host ""
Write-Host "Running installation verification tests..." -ForegroundColor Yellow
python tests/test_setup.py
$testResult = $LASTEXITCODE

# Summary
Write-Host ""
Write-Host "=== Installation Summary ===" -ForegroundColor Cyan
Write-Host "✓ Python dependencies installed" -ForegroundColor Green
if ($cbsInstalled) {
    Write-Host "✓ CyberBattleSim installed" -ForegroundColor Green
} else {
    Write-Host "✗ CyberBattleSim not installed (optional)" -ForegroundColor Yellow
}
Write-Host "✓ Configuration file created" -ForegroundColor Green

if ($testResult -eq 0) {
    Write-Host "✓ All verification tests passed" -ForegroundColor Green
} else {
    Write-Host "⚠ Some verification tests failed" -ForegroundColor Yellow
}

# Next steps
Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. (Optional) Start Neo4j database:" -ForegroundColor White
Write-Host "   docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/auvap_password neo4j:5.12" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run a quick test:" -ForegroundColor White
Write-Host "   python scripts/train_auvap.py --episodes 5" -ForegroundColor Gray
Write-Host ""
Write-Host "3. For full training with CyberBattleSim:" -ForegroundColor White
Write-Host "   python scripts/train_auvap.py --env CyberBattleChain-v0 --episodes 100" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Read the documentation:" -ForegroundColor White
Write-Host "   - README.md (framework overview)" -ForegroundColor Gray
Write-Host "   - QUICKSTART.md (5-minute guide)" -ForegroundColor Gray
Write-Host "   - INSTALL.md (detailed installation)" -ForegroundColor Gray
Write-Host ""
Write-Host "Installation complete! Happy hacking! 🎩🔐" -ForegroundColor Green
