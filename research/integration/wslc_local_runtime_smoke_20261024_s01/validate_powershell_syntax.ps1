param([Parameter(Mandatory)][string]$Path)
$tokens=$null
$errors=$null
[System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors) | Out-Null
if ($errors.Count -gt 0) { $errors | Format-List | Out-String | Write-Error; exit 1 }
Write-Output "Windows PowerShell parser PASS: $Path"