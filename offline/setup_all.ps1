param(
    [string]$installdir,
    [string]$envs,
    [string]$windowhandle
)


$ErrorActionPreference = "Stop"

# Add Windows API functions for sending messages
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class Win32 {
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    
    [DllImport("user32.dll", CharSet = CharSet.Ansi)]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, string lParam);
    
    public const uint WM_USER = 0x0400;
    public const uint WM_INSTALL_PROGRESS = WM_USER + 100;
}
"@

# Function to send progress update to the window
function Send-ProgressUpdate {
    param(
        [int]$BeginValue,
        [int]$EndValue
    )
    
    if ($windowhandle -and $windowhandle -ne "") {
        try {
            $hwnd = [IntPtr][long]$windowhandle
            [Win32]::SendMessage($hwnd, [Win32]::WM_INSTALL_PROGRESS, [IntPtr]$BeginValue, [IntPtr]$EndValue) | Out-Null

        }
        catch {
            Write-Host "Error sending message to window: $_"
        }
        Write-Host "Progress update sent: $BeginValue to $EndValue"
    }
}



# arguments:
# - installdir: The directory where the AI Playground is installed
# - envs: A space-separated list of environments to set up (e.g., "ai-backend ov comfyui llamacpp")
# -       If no envs are specified, all environments will be set up
# example usage:
#   .\setup_all.ps1 installdir="C:\path\to\install" envs="ai-backend comfyui"

# Get the directory of the current script file
$envList = $envs -split ' ' | Where-Object { $_ -ne '' }
$totalEnvs = $envList.Count
$currentEnv = 0
if (-not $installdir) {
    $installdir = "$HOME\AppData\Local\Programs\AI Playground"
}


Write-Host "Install directory: $installDir"
Write-Host "Environments to set up: $($envList -join ', ')"

# Check if the install directory exists
if (-not (Test-Path $installDir)) {
    Write-Host "Install directory does not exist: $installDir"
    exit 1
}

# Map environment names to their setup script names
$envScriptMap = @{
    "ai-backend" = "setup_ai-backend-env.ps1"
    "ov" = "setup_ov-env.ps1"
    "comfyui" = "setup_comfyui-env.ps1"
    "llamacpp" = "setup_llamacpp-env.ps1"
}


# Run the required setup scripts
foreach ($env in $envList) {
    $currentEnv++
    $baseProgress = [math]::Round(($currentEnv - 1) * 500 / $totalEnvs)
    $maxProgress = [math]::Round($currentEnv * 500 / $totalEnvs)

    Send-ProgressUpdate -BeginValue $baseProgress -EndValue $maxProgress

    $scriptName = $envScriptMap[$env]
    if ($scriptName) {
        Write-Host "Setting up $env environment..."
        

        $scriptPath = Join-Path $PSScriptRoot $scriptName
        
        Write-Host "Running script: $scriptPath"
        & $scriptPath "$installDir"
        # check if the script ran successfully
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Failed to set up $env environment."
            exit 1
        }
        Write-Host "$env environment setup completed."

        if ($env -eq "ai-backend") {
            # If the environment is ai-backend, we need to set the envDir and webApiScript variables
            $pythonExe = Join-Path $installDir "resources\ai-backend-env\python.exe"
            $workDir = Join-Path $installDir "resources\service"

            # run the web_api_lite.py script and don't wait for it to finish
            Start-Process -FilePath "$pythonExe" -ArgumentList "web_api_lite.py --port 59789" -WorkingDirectory "$workDir" -WindowStyle Hidden -RedirectStandardOutput "NUL"
            Write-Host "Started web_api_lite.py in the background."
        }

    }
    else {
        Write-Host "Warning: Unknown environment '$env', skipping"
    }

}

function Kill-Git-Process {
    # kill git.exe process$gitProcess = Get-Process -Name git -ErrorAction SilentlyContinue
    $gitProcess = Get-Process -Name git -ErrorAction SilentlyContinue
    if ($gitProcess) {
        $gitProcess | Stop-Process -Force
    }   
}

Send-ProgressUpdate -BeginValue 500 -EndValue 500
Kill-Git-Process

# Start the wait for initialization script in the background without waiting for it to finish
$waitScriptPath = Join-Path $PSScriptRoot "wait_for_init_finished.ps1"
Start-Process -FilePath "powershell.exe" -ArgumentList "-ExecutionPolicy Bypass -File `"$waitScriptPath`"" -WindowStyle Hidden

Send-ProgressUpdate -BeginValue 2000 -EndValue 2000