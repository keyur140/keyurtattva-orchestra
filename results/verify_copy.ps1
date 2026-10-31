# Checks a copied run folder against its own SHA256SUMS file.
# Author: KEYUR SHAILESHKUMAR PATEL (https://orcid.org/0009-0008-5261-043X)
# Usage: powershell -File verify_copy.ps1 <run folder>
param([Parameter(Mandatory = $true)][string]$RunDir)
$sums = Join-Path $RunDir "SHA256SUMS"
if (-not (Test-Path $sums)) { Write-Output "NO SHA256SUMS in $RunDir"; exit 2 }
$ok = 0; $bad = 0; $missing = 0; $badList = @()
foreach ($line in Get-Content $sums) {
    if ($line -match '^\s*$' -or $line.StartsWith('#')) { continue }
    $hash, $rel = $line -split '\s+\*?', 2
    $path = Join-Path $RunDir ($rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $path)) { $missing++; $badList += "MISSING $rel"; continue }
    $h = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
    if ($h -eq $hash.ToLower()) { $ok++ } else { $bad++; $badList += "MISMATCH $rel" }
}
Write-Output "$RunDir : matched $ok, mismatched $bad, missing $missing"
$badList | Select-Object -First 20 | ForEach-Object { Write-Output "  $_" }
if ($bad -or $missing) { exit 1 } else { exit 0 }
