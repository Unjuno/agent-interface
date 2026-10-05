param([string]$RequestedLanguage = "")

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskDefinition = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object {
        $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and
        $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1
if ($null -eq $asTaskDefinition) {
    throw 'Windows Runtime async bridge is unavailable'
}

function Await-Operation([object]$Operation, [Type]$ResultType) {
    $task = $asTaskDefinition.MakeGenericMethod($ResultType).Invoke(
        $null, @($Operation))
    $null = $task.Wait()
    return $task.Result
}

$storageFileType = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$fileAccessModeType = [Windows.Storage.FileAccessMode, Windows.Storage, ContentType=WindowsRuntime]
$randomAccessStreamType = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$bitmapDecoderType = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType=WindowsRuntime]
$softwareBitmapType = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics, ContentType=WindowsRuntime]
$languageType = [Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime]
$ocrEngineType = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
$ocrResultType = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType=WindowsRuntime]

$languages = @($ocrEngineType::AvailableRecognizerLanguages)
if ($RequestedLanguage) {
    $language = $languages | Where-Object { $_.LanguageTag -eq $RequestedLanguage } |
        Select-Object -First 1
} else {
    $language = $null
    foreach ($preferred in @('en-US', 'en', 'ja')) {
        $language = $languages | Where-Object { $_.LanguageTag -eq $preferred } |
            Select-Object -First 1
        if ($null -ne $language) { break }
    }
    if ($null -eq $language) { $language = $languages | Select-Object -First 1 }
}
if ($null -eq $language) { throw 'No Windows OCR recognizer language is installed' }
$engine = $ocrEngineType::TryCreateFromLanguage($language)
if ($null -eq $engine) { throw 'Windows OCR engine creation failed' }

function Write-Response([hashtable]$Value) {
    [Console]::Out.WriteLine(($Value | ConvertTo-Json -Compress -Depth 4))
    [Console]::Out.Flush()
}

Write-Response @{ status = 'ready'; language = $language.LanguageTag }
while ($null -ne ($line = [Console]::In.ReadLine())) {
    $bitmap = $null
    $stream = $null
    try {
        if ($line.Length -gt 8192) { throw 'request exceeds 8192 characters' }
        $request = ConvertFrom-Json -InputObject $line
        if ($request.operation -ne 'recognize' -or
            [string]::IsNullOrWhiteSpace($request.path)) {
            throw 'recognize operation and image path required'
        }
        $path = [System.IO.Path]::GetFullPath([string]$request.path)
        $file = Await-Operation ($storageFileType::GetFileFromPathAsync($path)) $storageFileType
        $stream = Await-Operation ($file.OpenAsync($fileAccessModeType::Read)) $randomAccessStreamType
        $decoder = Await-Operation ($bitmapDecoderType::CreateAsync($stream)) $bitmapDecoderType
        $bitmap = Await-Operation ($decoder.GetSoftwareBitmapAsync()) $softwareBitmapType
        $recognized = Await-Operation ($engine.RecognizeAsync($bitmap)) $ocrResultType
        Write-Response @{ status = 'ok'; language = $language.LanguageTag;
                          text = [string]$recognized.Text }
    } catch {
        Write-Response @{ status = 'error'; error = $_.Exception.Message }
    } finally {
        if ($null -ne $bitmap) { try { $bitmap.Dispose() } catch {} }
        if ($null -ne $stream) { try { $stream.Dispose() } catch {} }
    }
}
