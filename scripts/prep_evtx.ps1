# PowerShell script to convert EVTX files to JSONL format.
#
# Usage:
#   .\scripts\prep_evtx.ps1 -InputPath ".\data\evtx_raw" -OutputPath ".\data\evtx_parsed"
#
# Limitations:
#   - Windows-only (uses Get-WinEvent).
#   - Produces a minimal JSONL envelope, not a full EVTX export.
#   - Overwrites existing JSONL files with the same base name.

param(
    [Parameter(Mandatory = $true)]
    [string] $InputPath,

    [Parameter(Mandatory = $true)]
    [string] $OutputPath
)

if (-not (Test-Path -Path $InputPath)) {
    Write-Error "Input path does not exist: $InputPath"
    exit 1
}

New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null

Get-ChildItem -Path $InputPath -Filter "*.evtx" | ForEach-Object {
    $evtxFile = $_.FullName
    $jsonlFile = Join-Path $OutputPath "$($_.BaseName).jsonl"

    Write-Host "Processing $($_.Name)..."

    Remove-Item -Force -ErrorAction SilentlyContinue $jsonlFile

    Get-WinEvent -Path $evtxFile -Oldest | ForEach-Object {
        $event = @{
            Event = @{
                System = @{
                    EventID     = $_.Id
                    TimeCreated = $_.TimeCreated.ToString("o")
                    Computer    = $_.MachineName
                }
                EventData = @{}
            }
        }

        $_.Properties | ForEach-Object -Begin { $i = 0 } {
            $event.Event.EventData["Data$i"] = $_.Value
            $i++
        }

        $json = $event | ConvertTo-Json -Compress -Depth 10
        Add-Content -Path $jsonlFile -Value $json -Encoding utf8
    }

    Write-Host "Created $jsonlFile"
}

Write-Host "Preprocessing complete. JSONL files in $OutputPath"
