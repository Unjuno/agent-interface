. (Join-Path $PSScriptRoot 'gpu_preflight_gate.ps1')

if ((Test-ExperimentDiskGate -AvailableBytes 67108863 -RequiredBytes 67108864) -ne 'STOP_INSUFFICIENT_DISK_SPACE') { throw 'disk gate must stop below the required durable-output reserve' }
if ((Test-ExperimentDiskGate -AvailableBytes 67108864 -RequiredBytes 67108864) -ne 'PREFLIGHT_OK') { throw 'disk gate must allow an exact sufficient reserve' }

$cases = @(
    @{ Name = 'null app list and idle GPU'; Gpu = '0 %, 0 MiB'; Apps = $null; GpuExit = 0; AppsExit = 0; Expected = 'PREFLIGHT_OK' },
    @{ Name = 'empty app list and idle GPU'; Gpu = '0 %, 0 MiB'; Apps = @(); GpuExit = 0; AppsExit = 0; Expected = 'PREFLIGHT_OK' },
    @{ Name = 'whitespace app row'; Gpu = '0 %, 0 MiB'; Apps = @('  '); GpuExit = 0; AppsExit = 0; Expected = 'PREFLIGHT_OK' },
    @{ Name = 'active CUDA process'; Gpu = '0 %, 0 MiB'; Apps = @('29332, python.exe, 512 MiB'); GpuExit = 0; AppsExit = 0; Expected = 'STOP_COMPETING_CUDA_PROCESS' },
    @{ Name = 'nonzero utilization'; Gpu = '12 %, 0 MiB'; Apps = $null; GpuExit = 0; AppsExit = 0; Expected = 'STOP_GPU_NOT_IDLE_OR_UNPARSEABLE' },
    @{ Name = 'unparseable GPU output'; Gpu = 'query error'; Apps = $null; GpuExit = 0; AppsExit = 0; Expected = 'STOP_GPU_NOT_IDLE_OR_UNPARSEABLE' },
    @{ Name = 'app inventory command failure'; Gpu = '0 %, 0 MiB'; Apps = $null; GpuExit = 0; AppsExit = 1; Expected = 'STOP_NVIDIA_SMI_QUERY_FAILED' },
    @{ Name = 'GPU query command failure'; Gpu = '0 %, 0 MiB'; Apps = @(); GpuExit = 1; AppsExit = 0; Expected = 'STOP_NVIDIA_SMI_QUERY_FAILED' }
)

$results = @(
    foreach ($case in $cases) {
        $actual = Test-GpuLeasePreflight -GpuSnapshot $case.Gpu -ComputeAppLines $case.Apps -GpuQueryExitCode $case.GpuExit -AppsQueryExitCode $case.AppsExit
        [pscustomobject]@{ name = $case.Name; expected = $case.Expected; actual = $actual; pass = ($actual -eq $case.Expected) }
    }
)
$failed = @($results | Where-Object { -not $_.pass })
[pscustomobject]@{ passed = $results.Count - $failed.Count; total = $results.Count; failures = $failed } | ConvertTo-Json -Depth 6 -Compress
if ($failed.Count -gt 0) { exit 1 }

