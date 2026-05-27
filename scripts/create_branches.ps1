# Create the standard DAOS remediation branches
# Run from the repository root in PowerShell

$ErrorActionPreference = 'Stop'

# Branches to create (local only). Push explicitly after review if desired.
$branches = @(
  'feature/core-ingestion-depth',
  'feature/metadata-core',
  'feature/backend-observability',
  'feature/frontend-refactor',
  'feature/ai-workflow-intelligence',
  'feature/testing-suite',
  'feature/operational-hardening',
  'docs/blueprint'
)

# Ensure we're in a git repo
try {
  git rev-parse --git-dir > $null 2>&1
} catch {
  Write-Host "Not a git repository. Initialize the repo first or run this script from the repository root." -ForegroundColor Yellow
  exit 1
}

foreach ($b in $branches) {
  $exists = git show-ref --verify --quiet "refs/heads/$b"; $status = $LASTEXITCODE
  if ($status -eq 0) {
    Write-Host "Branch '$b' already exists locally." -ForegroundColor Cyan
  } else {
    git branch $b
    if ($LASTEXITCODE -eq 0) {
      Write-Host "Created branch '$b'." -ForegroundColor Green
    } else {
      Write-Host "Failed to create branch '$b'." -ForegroundColor Red
    }
  }
}

Write-Host "All requested branches processed. Review with 'git branch' and push as needed." -ForegroundColor Green
