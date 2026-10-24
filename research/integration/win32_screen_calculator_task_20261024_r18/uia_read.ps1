param(
    [Parameter(Mandatory=$true)][long]$Hwnd,
    [string]$ExpectedDisplay = '',
    [ValidateRange(0,1500)][int]$TimeoutMs = 0,
    [ValidateRange(1,100)][int]$PollIntervalMs = 25
)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$readStart = [DateTime]::UtcNow.ToString('o')
$watch = [System.Diagnostics.Stopwatch]::StartNew()
$expectedDigits = [regex]::Match($ExpectedDisplay, '[0-9][0-9,]*').Value.Replace(',', '')
$pollCount = 0
$resultName = $null
$expressionName = $null
$rootName = $null
while ($true) {
    $pollCount++
    $root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Hwnd)
    if ($null -eq $root) { throw 'UIA root unavailable' }
    $rootName = $root.Current.Name
    $all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    $resultName = $null
    $expressionName = $null
    for ($i = 0; $i -lt $all.Count; $i++) {
        $element = $all.Item($i)
        if ($element.Current.AutomationId -eq 'CalculatorResults') {
            $resultName = $element.Current.Name
        }
        if ($element.Current.AutomationId -eq 'CalculatorExpression') {
            $expressionName = $element.Current.Name
        }
    }
    if ($null -eq $resultName) { throw 'CalculatorResults UIA element unavailable' }
    $digits = [regex]::Match($resultName, '[0-9][0-9,]*').Value.Replace(',', '')
    if (-not $expectedDigits -or $digits -eq $expectedDigits) { break }
    if ($watch.ElapsedMilliseconds -ge $TimeoutMs) { break }
    Start-Sleep -Milliseconds $PollIntervalMs
}
$watch.Stop()
$digits = [regex]::Match($resultName, '[0-9][0-9,]*').Value.Replace(',', '')
[pscustomobject]@{
    hwnd = $Hwnd
    root_name = $rootName
    result_name = $resultName
    expression_name = $expressionName
    display_digits = $digits
    expected_display_seen = (-not $expectedDigits -or $digits -eq $expectedDigits)
    poll_count = $pollCount
    read_started_utc = $readStart
    read_completed_utc = [DateTime]::UtcNow.ToString('o')
    elapsed_ms = $watch.Elapsed.TotalMilliseconds
} | ConvertTo-Json -Compress
