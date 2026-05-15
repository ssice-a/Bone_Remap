$ErrorActionPreference = "Stop"

gh auth status
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run `gh auth login` or set GH_TOKEN before publishing issues."
}

$issueDir = Join-Path $PSScriptRoot "mvp-live-retargeting-workbench-issues"

Get-ChildItem -LiteralPath $issueDir -Filter "*.md" |
    Sort-Object Name |
    ForEach-Object {
        $titleLine = Get-Content -LiteralPath $_.FullName -First 1
        $title = $titleLine.TrimStart("#").Trim()

        Write-Host "Creating issue: $title"
        gh issue create --title $title --body-file $_.FullName --label "ready-for-agent"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create issue: $title"
        }
    }
