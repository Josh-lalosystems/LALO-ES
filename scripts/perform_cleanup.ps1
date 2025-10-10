<#
Perform cleanup of temporary and large files in the working branch.

This script is intentionally conservative: it only lists files by default
and moves large files into a `backups/cleanup` folder. Use -Remove flag to
actually delete the small temp files.

Examples:
  # Dry run (default)
  .\scripts\perform_cleanup.ps1

  # Actually remove .tmp_ files and move screenshots to backups
  .\scripts\perform_cleanup.ps1 -Remove
#>

param(
    [switch]$Remove
)

Write-Host "Performing repo cleanup (Remove=$Remove)"

$root = Get-Location
$candidates = @(
    "./.tmp_quick_test.py",
    "./.tmp_db_test.py",
    "./.tmp_list_audit.py",
    "./scripts/force_fallback_test.py",
    "./lalo-frontend-backup",
    "./Screenshot 2025-10-02 194133.png",
    "./Screenshot 2025-09-10 153935.png"
)

Write-Host "Candidates to consider:" -ForegroundColor Cyan
foreach ($f in $candidates) { Write-Host "  " $f }

if ($Remove) {
    # Ensure backup folder exists
    $backupDir = Join-Path $root "backups/cleanup"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    foreach ($f in $candidates) {
        if (Test-Path $f) {
            $item = Get-Item $f
            if ($item.PSIsContainer) {
                Write-Host "Moving folder $f to $backupDir"
                Move-Item -Path $f -Destination $backupDir -Force
            } else {
                # for small temp scripts, delete; for large files move
                if ($item.Length -lt 50KB) {
                    Write-Host "Removing file $f"
                    Remove-Item -Path $f -Force
                } else {
                    Write-Host "Moving large file $f to $backupDir"
                    Move-Item -Path $f -Destination $backupDir -Force
                }
            }
        } else {
            Write-Host "Not found: $f"
        }
    }
    Write-Host "Cleanup complete. Backup dir: $backupDir"
} else {
    Write-Host "Dry-run: no files modified. Re-run with -Remove to actually clean up."
}
