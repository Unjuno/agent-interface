# Run the existing contract suites in Ubuntu; dependency installation is separate.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Repository,
    [Parameter(Mandatory)][string]$Output,
    [string]$Distribution = 'Ubuntu',
    [string]$ProtocolPython = '/tmp/agent-interface-mcp-venv/bin/python',
    [string]$HarnessPython = '/usr/bin/python3'
)
$ErrorActionPreference = 'Stop'
if (-not $Repository.StartsWith('/')) {
    throw 'Repository must be an absolute Linux path in the WSL filesystem.'
}
# Output is interpreted by the existing runner relative to Repository.
# The runner refuses an existing output directory and preserves suite logs.
& wsl.exe -d $Distribution --cd $Repository --exec python3 `
    runtime/integration_checks/native.py `
    --protocol-python $ProtocolPython --harness-python $HarnessPython `
    --output $Output
exit $LASTEXITCODE
