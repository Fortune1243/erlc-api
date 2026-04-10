param(
    [string]$SourceDir = "docs/wiki",
    [string]$WikiDir = ".wiki-worktree",
    [string]$RepoUrl = "",
    [string]$CommitMessage = "",
    [switch]$Push
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
    $CommitMessage = if ($env:WIKI_COMMIT_MESSAGE) { $env:WIKI_COMMIT_MESSAGE } else { "docs(wiki): sync from docs/wiki" }
}

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    throw "Source directory does not exist: $SourceDir"
}

if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
    $RepoUrl = (git remote get-url origin).Trim()
}

$baseRepoUrl = if ($RepoUrl.EndsWith(".git")) { $RepoUrl.Substring(0, $RepoUrl.Length - 4) } else { $RepoUrl }
$wikiRepoUrl = "$baseRepoUrl.wiki.git"

Write-Host "Using wiki repo: $wikiRepoUrl"

if (Test-Path -LiteralPath (Join-Path $WikiDir ".git") -PathType Container) {
    git -C $WikiDir fetch origin
} else {
    if (Test-Path -LiteralPath $WikiDir) {
        Remove-Item -LiteralPath $WikiDir -Recurse -Force
    }
    git clone $wikiRepoUrl $WikiDir
}

git -C $WikiDir show-ref --verify --quiet refs/heads/master | Out-Null
$hasMaster = $LASTEXITCODE -eq 0

if ($hasMaster) {
    git -C $WikiDir checkout master
} else {
    git -C $WikiDir checkout -B master
}

git -C $WikiDir rev-parse --verify origin/master | Out-Null
$hasOriginMaster = $LASTEXITCODE -eq 0

if ($hasOriginMaster) {
    git -C $WikiDir reset --hard origin/master
}

Get-ChildItem -LiteralPath $WikiDir -Force |
    Where-Object { $_.Name -ne ".git" } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }

Copy-Item -Path (Join-Path $SourceDir "*") -Destination $WikiDir -Recurse -Force

git -C $WikiDir add -A

git -C $WikiDir diff --cached --quiet --exit-code | Out-Null
$hasChanges = $LASTEXITCODE -ne 0

if (-not $hasChanges) {
    Write-Host "No wiki changes detected."
    exit 0
}

git -C $WikiDir commit -m $CommitMessage

if ($Push) {
    git -C $WikiDir push origin master
    Write-Host "Wiki changes pushed."
} else {
    Write-Host "Wiki changes committed locally in $WikiDir. Re-run with -Push to publish."
}
