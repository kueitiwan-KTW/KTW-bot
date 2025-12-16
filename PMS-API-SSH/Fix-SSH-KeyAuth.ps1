# Fix-SSH-KeyAuth.ps1
# Fix Windows SSH key authentication for Mac connection

Write-Host ""
Write-Host "========================================"
Write-Host "  Fix SSH Key Authentication"
Write-Host "========================================"
Write-Host ""

# Mac public keys
$MAC_PUBLIC_KEYS = @"
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCfdCAgIwtQj8eaxt6xJiNq8ax7V7zQORFtqWfgICDhb00akigNktuO+YhhqsN1opkvcJ4nMfqdbBLFr4v81hDiDYkdyO0Wuu2OiLipX8S24eJRF7F2jETQOkyAPBzI3cCmhn9wgKmRvqrUZmeAlJUiWLBB9H+10mnfnwAV9rBu/Q1wa8VvDVRxYRy/dUhzbkL0GbHdIbUVpEmbRJCbqBgpXzA2qltQPi4chHBJTLTRmubWzxrqaiCtWPkUWOwVN53UROazHCG9REcXiDDa03g9K7LuPIut8pxTHEiZpMeWe15sNg2eb/i8eSObvMu8lNoPvmTNtkJ8lWVlAOIHSYOGobvwjgyrmaZzmuOEBpvvPlQhCaqGyb95e8SUM6fC12441CmkEWq0hxrBY49xxtgeo3S7C1N4BWJhpkVW5u17eBV5auWn0oYz2cNdIpVnbDnMgRKrz4G/wZnHxmNiMDKXMYuTVIZhz+JzKz6LxnZ3WbB613Z1wSA7cS65/J6NIP7tebfis1jVDoUFuQSJx38WsNJ+e5VzeIsAQUlegj7PMm9U4O9AzZQwSM7Y+RpsKSKSeyrwL6kad8XVAVbfyaVgQUNV0T/4OPxoHsAHcevWIfmPH1YPQ7lTuFxBuZNbXmrix6vy4cFTElz+SwaIcp+7mR529FmIxDYUDfyRFEvRQQ== ktw@mac-to-pms
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINHzmK95JDp00IQlJk1qXMDKAr1KxSgxWeQK87akwz6F kuei.ti.wan@gmail.com
"@

# Step 1: Create .ssh directory
$sshDir = "C:\Users\Administrator\.ssh"
$authKeysPath = "C:\Users\Administrator\.ssh\authorized_keys"

Write-Host "[1/6] Create .ssh directory..." -ForegroundColor Yellow
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "      Created: $sshDir" -ForegroundColor Green
}
else {
    Write-Host "      Already exists" -ForegroundColor Green
}

# Step 2: Write authorized_keys
Write-Host ""
Write-Host "[2/6] Write Mac public keys..." -ForegroundColor Yellow
$MAC_PUBLIC_KEYS | Set-Content -Path $authKeysPath -Encoding ASCII -Force
Write-Host "      Written 2 public keys" -ForegroundColor Green

# Step 3: Fix file permissions
Write-Host ""
Write-Host "[3/6] Fix file permissions..." -ForegroundColor Yellow
icacls $authKeysPath /inheritance:r 2>$null | Out-Null
icacls $authKeysPath /grant "SYSTEM:(F)" 2>$null | Out-Null
icacls $authKeysPath /grant "BUILTIN\Administrators:(F)" 2>$null | Out-Null
Write-Host "      Permissions fixed" -ForegroundColor Green

# Step 4: Fix sshd_config
Write-Host ""
Write-Host "[4/6] Fix sshd_config..." -ForegroundColor Yellow

$sshdConfigPath = "C:\ProgramData\ssh\sshd_config"
if (!(Test-Path $sshdConfigPath)) {
    $sshdConfigPath = "C:\Program Files\OpenSSH-Win64\sshd_config"
}

if (Test-Path $sshdConfigPath) {
    $lines = Get-Content $sshdConfigPath
    $newLines = @()
    $modified = $false
    
    foreach ($line in $lines) {
        if ($line -match "^Match Group administrators") {
            $newLines += "# $line"
            $modified = $true
        }
        elseif ($line -match "^\s+AuthorizedKeysFile.*PROGRAMDATA") {
            $newLines += "# $line"
            $modified = $true
        }
        else {
            $newLines += $line
        }
    }
    
    if ($modified) {
        $newLines | Set-Content $sshdConfigPath
        Write-Host "      Config updated" -ForegroundColor Green
    }
    else {
        Write-Host "      Config OK" -ForegroundColor Green
    }
}
else {
    Write-Host "      sshd_config not found!" -ForegroundColor Red
}

# Step 5: Setup ProgramData backup keys
Write-Host ""
Write-Host "[5/6] Setup ProgramData keys..." -ForegroundColor Yellow
$programDataKeys = "C:\ProgramData\ssh\administrators_authorized_keys"
$MAC_PUBLIC_KEYS | Set-Content -Path $programDataKeys -Encoding ASCII -Force
icacls $programDataKeys /inheritance:r 2>$null | Out-Null
icacls $programDataKeys /grant "SYSTEM:(F)" 2>$null | Out-Null
icacls $programDataKeys /grant "BUILTIN\Administrators:(R)" 2>$null | Out-Null
Write-Host "      Backup keys created" -ForegroundColor Green

# Step 6: Restart SSH
Write-Host ""
Write-Host "[6/6] Restart SSH service..." -ForegroundColor Yellow
Restart-Service sshd -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$sshStatus = Get-Service sshd -ErrorAction SilentlyContinue
if ($sshStatus.Status -eq "Running") {
    Write-Host "      SSH service running" -ForegroundColor Green
}
else {
    Write-Host "      SSH status: $($sshStatus.Status)" -ForegroundColor Yellow
}

# Done
Write-Host ""
Write-Host "========================================"
Write-Host "  Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Test SSH from Mac:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ssh Administrator@192.168.8.3" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
