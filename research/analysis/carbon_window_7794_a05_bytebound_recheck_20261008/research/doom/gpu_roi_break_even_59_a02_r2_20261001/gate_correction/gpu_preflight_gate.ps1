function Test-GpuLeasePreflight {
    param(
        [AllowNull()][string]$GpuSnapshot,
        [AllowNull()][string[]]$ComputeAppLines,
        [int]$GpuQueryExitCode = 0,
        [int]$AppsQueryExitCode = 0
    )

    if ($GpuQueryExitCode -ne 0 -or $AppsQueryExitCode -ne 0) {
        return 'STOP_NVIDIA_SMI_QUERY_FAILED'
    }
    if ([string]::IsNullOrWhiteSpace($GpuSnapshot) -or
        $GpuSnapshot.Trim() -notmatch '^0\s*%,\s*0\s*MiB$') {
        return 'STOP_GPU_NOT_IDLE_OR_UNPARSEABLE'
    }

    $activeLines = @(
        foreach ($line in @($ComputeAppLines)) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                $line.Trim()
            }
        }
    )
    if ($activeLines.Count -gt 0) {
        return 'STOP_COMPETING_CUDA_PROCESS'
    }
    return 'PREFLIGHT_OK'
}

function Invoke-GpuLeasePreflight {
    $gpuLines = @(& nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>&1)
    $gpuExit = $LASTEXITCODE
    $appLines = @(& nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>&1)
    $appsExit = $LASTEXITCODE
    $gpuText = [string]::Join("`n", @($gpuLines | ForEach-Object { [string]$_ })).Trim()
    $status = Test-GpuLeasePreflight -GpuSnapshot $gpuText -ComputeAppLines $appLines -GpuQueryExitCode $gpuExit -AppsQueryExitCode $appsExit
    [pscustomobject]@{
        status = $status
        gpu_snapshot = $gpuText
        compute_app_count = @($appLines | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }).Count
        gpu_query_exit_code = $gpuExit
        apps_query_exit_code = $appsExit
    }
}
