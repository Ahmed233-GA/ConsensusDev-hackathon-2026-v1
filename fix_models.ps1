# ConsensusDev - fix dead free model + test (automatic)
$ErrorActionPreference = "Stop"

$NEWMODEL = "nvidia/nemotron-3-super-120b-a12b:free"

Write-Output "=== STEP 0: update .env (replace dead model) ==="
$envPath = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envPath)) { Write-Output "NO .env found next to script"; exit 1 }

$lines = Get-Content $envPath
$changed = $false
for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "gpt-oss-20b:free") {
        $lines[$i] = $lines[$i] -replace "gpt-oss-20b:free", $NEWMODEL
        $changed = $true
        Write-Output ("  replaced in: " + $lines[$i])
    }
}
if ($changed) { $lines | Set-Content $envPath; Write-Output "  .env updated." }
else { Write-Output "  No dead model found - .env already fine." }

$key = ((Get-Content $envPath | Where-Object { $_ -match '^OPENROUTER_API_KEY=' }) -replace 'OPENROUTER_API_KEY=','').Trim()
if (-not $key) { Write-Output "NO KEY FOUND"; exit 1 }

# ---- Step 1: model check (1 request) ----
Write-Output ""
Write-Output ("=== STEP 1: model check (" + $NEWMODEL + ") ===")
$u = "https://openrouter.ai/api/v1/chat/completions"
$body = @{ model = $NEWMODEL; messages = @(@{ role = "user"; content = "Reply with exactly: MODEL OK" }) } | ConvertTo-Json -Depth 5
try {
    $r = Invoke-RestMethod -Method Post -Uri $u -Headers @{ Authorization = "Bearer $key" } -ContentType "application/json" -Body $body
    Write-Output ("MODEL RESULT: " + $r.choices[0].message.content)
} catch {
    Write-Output ("MODEL CHECK FAILED: " + $_.ErrorDetails.Message)
    exit 1
}

# ---- Step 2: full review (4 requests, ~25s) ----
Write-Output ""
Write-Output "=== STEP 2: full review (~25s, be patient) ==="
$u2 = "http://127.0.0.1:8000/api/reviews/trigger"
$body2 = '{"diff":"diff --git a/calc.py b/calc.py`n+def add(a, b): return a + b","pr_number":904,"pr_title":"test","author":"AhmedAtia","branch":"feature/t"}'
try {
    $r2 = Invoke-RestMethod -Method Post -Uri $u2 -ContentType "application/json" -Body $body2
    Write-Output "--- agents ---"
    $r2.review.agents | Select-Object id, score, summary | Format-Table -AutoSize
    Write-Output ("DECISION: " + $r2.review.consensus.decision + "  SCORE: " + $r2.review.consensus.score)
} catch {
    Write-Output ("REVIEW FAILED: " + $_.ErrorDetails.Message)
}

Write-Output ""
Write-Output "=== DONE ==="
Write-Output "If story_match score = 2.0 (critical text) -> REAL AI ACTIVE"
Write-Output "If story_match score = 9.0 (fixed phrase) -> still fallback, restart AI engine"
