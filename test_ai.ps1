# ConsensusDev — AI smoke test (model + full review)
$ErrorActionPreference = "Stop"

$key = ((Get-Content .env | Where-Object { $_ -match '^OPENROUTER_API_KEY=' }) -replace 'OPENROUTER_API_KEY=','').Trim()
if (-not $key) {
    Write-Output "NO KEY FOUND in .env"
    exit 1
}

# ---- Step 1: verify the model works (1 request) ----
Write-Output "=== STEP 1: model check ==="
$u = "https://openrouter.ai/api/v1/chat/completions"
$body = @{ model = "openai/gpt-oss-20b:free"; messages = @(@{ role = "user"; content = "Reply with exactly: MODEL OK" }) } | ConvertTo-Json -Depth 5
try {
    $r = Invoke-RestMethod -Method Post -Uri $u -Headers @{ Authorization = "Bearer $key" } -ContentType "application/json" -Body $body
    Write-Output ("MODEL RESULT: " + $r.choices[0].message.content)
} catch {
    Write-Output ("MODEL CHECK FAILED: " + $_.ErrorDetails.Message)
    exit 1
}

# ---- Step 2: full review through the pipeline (4 requests) ----
Write-Output ""
Write-Output "=== STEP 2: full review (this takes ~25s, be patient) ==="
$u2 = "http://127.0.0.1:8000/api/reviews/trigger"
$body2 = '{"diff":"diff --git a/calc.py b/calc.py`n+def add(a, b): return a + b","pr_number":903,"pr_title":"test","author":"AhmedAtia","branch":"feature/t"}'
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
