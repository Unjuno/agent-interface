param([Parameter(Mandatory=$true)][long]$Hwnd,[Parameter(Mandatory=$true)][string]$OutPath,[Parameter(Mandatory=$true)][string]$StopPath,[ValidateRange(5,100)][int]$PollMs=10)
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$freq=[System.Diagnostics.Stopwatch]::Frequency
$encoding=New-Object System.Text.UTF8Encoding($false)
$sample=0
while(-not(Test-Path -LiteralPath $StopPath)){
 $sample++;$start=[System.Diagnostics.Stopwatch]::GetTimestamp();$rootName=$null;$resultName=$null;$digits=$null;$err=$null
 try{
  $root=[System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Hwnd)
  if($null -eq $root){throw 'UIA root unavailable'}
  $rootName=$root.Current.Name
  $all=$root.FindAll([System.Windows.Automation.TreeScope]::Descendants,[System.Windows.Automation.Condition]::TrueCondition)
  for($i=0;$i -lt $all.Count;$i++){ $element=$all.Item($i);if($element.Current.AutomationId -eq 'CalculatorResults'){$resultName=$element.Current.Name;break} }
  if($null -eq $resultName){throw 'CalculatorResults UIA element unavailable'}
  $digits=[regex]::Match($resultName,'[0-9][0-9,]*').Value.Replace(',','')
 }catch{$err=$_.Exception.Message}
 $end=[System.Diagnostics.Stopwatch]::GetTimestamp()
 $row=[ordered]@{sample=$sample;qpc_start=$start;qpc_end=$end;qpc_frequency=$freq;display_digits=$digits;root_name=$rootName;result_name=$resultName;error=$err;utc_after_read=[DateTime]::UtcNow.ToString('o')}
 [System.IO.File]::AppendAllText($OutPath,(($row|ConvertTo-Json -Compress)+[Environment]::NewLine),$encoding)
 Start-Sleep -Milliseconds $PollMs
}
exit 0
