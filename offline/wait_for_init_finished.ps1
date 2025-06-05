# Wait for initialization to finish by monitoring port 59789
# This script checks if port 59789 is listening and kills the process when found

$ErrorActionPreference = "Stop"

function Wait-ForInitFinished {
    while ($true) {
        # Check the port 59789 is listening and kill the process if it is
        $portInUse = Get-NetTCPConnection -LocalPort 59789 -ErrorAction SilentlyContinue
        if ($portInUse) {
            Write-Host "Initialization Completed..."
            Stop-Process -Id $portInUse.OwningProcess -Force
            Break
        }        
        Write-Host "Initializing..."
        Start-Sleep -Seconds 1
    }
}

# Run the function
Wait-ForInitFinished
