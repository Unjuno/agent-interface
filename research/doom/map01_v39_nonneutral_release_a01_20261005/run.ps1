$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$test = Join-Path $here 'test_non_neutral_release.py'
$cases = @(
  @{ name='PARENT-RED'; source='baseline_input_owner_v13.py'; selector='T.test_non_neutral_successful_aggregate_must_fail_closed'; expected='red' },
  @{ name='PUBLISHED-CANDIDATE-RED'; source='published_input_owner_v13.py'; selector=$null; expected='red' },
  @{ name='CANDIDATE-GREEN'; source='input_owner_v14_candidate.py'; selector=$null; expected='green' }
)
foreach ($case in $cases) {
  $env:OWNER_SOURCE_PATH = Join-Path $here $case.source
  if ($case.selector) { $out = python -B $test $case.selector 2>&1 }
  else { $out = python -B $test 2>&1 }
  $exit = $LASTEXITCODE
  [IO.File]::WriteAllLines((Join-Path $here ($case.name + '.log')),[string[]]$out,[Text.UTF8Encoding]::new($false))
  Write-Output "$($case.name) exit=$exit"
  $out
  if ($case.expected -eq 'red' -and $exit -eq 0) { throw "$($case.name) unexpectedly passed" }
  if ($case.expected -eq 'green' -and $exit -ne 0) { throw "$($case.name) did not pass" }
}