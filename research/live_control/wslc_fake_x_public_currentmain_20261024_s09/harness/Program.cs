using Microsoft.WSL.Containers;
using System.Text;
using System.Text.Json;

static void Emit(string stage, object details)
{
    Console.WriteLine(JsonSerializer.Serialize(new { utc = DateTimeOffset.UtcNow, stage, details }));
    Console.Out.Flush();
}

if (args.Length != 8)
{
    Console.Error.WriteLine("usage: S09 <session-name> <storage-path> <image> <runtime-dir> <attempt-dir> <deps-dir> <output-dir> <container-name>");
    return 64;
}
var sessionName = args[0];
var storagePath = Path.GetFullPath(args[1]);
var image = args[2];
var runtimePath = Path.GetFullPath(args[3]);
var attemptPath = Path.GetFullPath(args[4]);
var depsPath = Path.GetFullPath(args[5]);
var outputPath = Path.GetFullPath(args[6]);
var containerName = args[7];
var missing = WslcService.GetMissingComponents();
Emit("prerequisites", new { missing = missing.Select(x => x.ToString()).ToArray() });
if (missing.Count != 0) return 65;
var ver = WslcService.GetVersion();
Emit("version", new { ver.Major, ver.Minor, ver.Revision });
Session? session = null;
Container? container = null;
string? containerId = null;
string? outputText = null;
string? errorText = null;
var output = new StringBuilder();
var errorOutput = new StringBuilder();
int? processExit = null;
Exception? failure = null;
bool sessionStarted = false;
bool imagePulled = false;
bool containerDeleted = false;
bool imageDeleted = false;
bool sessionTerminated = false;
try
{
    var settings = new SessionSettings(sessionName, storagePath)
    {
        CpuCount = 1,
        MemorySizeInMB = 1024,
        Timeout = TimeSpan.FromMinutes(12),
        EnableGpu = false
    };
    session = new Session(settings);
    session.Start();
    sessionStarted = true;
    Emit("session_started", new { sessionName, storagePath, cpuCount = 1, memorySizeInMB = 1024 });

    var pull = session.PullImageAsync(new PullImageOptions(image));
    pull.Progress = (_, progress) => Emit("pull_progress", new { progress.Status, progress.Id, progress.CurrentBytes, progress.TotalBytes });
    var pullTask = Task.Run(async () => await pull);
    if (await Task.WhenAny(pullTask, Task.Delay(TimeSpan.FromMinutes(10))) != pullTask)
    {
        try { pull.Cancel(); } catch { }
        throw new TimeoutException("Pinned image pull exceeded 10 minutes; outcome unknown.");
    }
    await pullTask;
    imagePulled = true;
    Emit("image_pull_complete", new { image });

    var init = new ProcessSettings
    {
        CommandLine = new List<string> { "python", "-B", "/src/research/live_control/wslc_fake_x_public_currentmain_20261024_s09/runner.py" },
        OutputMode = ProcessOutputMode.Event
    };
    var containerSettings = new ContainerSettings(image)
    {
        Name = containerName,
        InitProcess = init,
        NetworkingMode = ContainerNetworkingMode.None,
        EnableAutoRemove = false,
        EnableGpu = false,
        Privileged = false,
        Volumes = new List<ContainerVolume>
        {
            new(runtimePath, "/src/runtime", readOnly: true),
            new(attemptPath, "/src/research/live_control/wslc_fake_x_public_currentmain_20261024_s09", readOnly: true),
            new(depsPath, "/deps", readOnly: true),
            new(outputPath, "/out", readOnly: false)
        }
    };
    container = session.CreateContainer(containerSettings);
    containerId = container.Id;
    var exited = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
    container.InitProcess.OutputReceived += data =>
    {
        var chunk = Encoding.UTF8.GetString(data);
        lock (output) output.Append(chunk);
        Emit("container_stdout", new { text = chunk });
    };
    container.InitProcess.ErrorReceived += data =>
    {
        var chunk = Encoding.UTF8.GetString(data);
        lock (errorOutput) errorOutput.Append(chunk);
        Emit("container_stderr", new { text = chunk });
    };
    container.InitProcess.Exited += code => exited.TrySetResult(code);
    Emit("container_created", new { containerId, containerName, networkingMode = ContainerNetworkingMode.None.ToString(), sourceReadOnly = true, dependenciesReadOnly = true });
    container.Start();
    var done = await Task.WhenAny(exited.Task, Task.Delay(TimeSpan.FromSeconds(180)));
    if (done != exited.Task) throw new TimeoutException("Fake X probe container exceeded 180 seconds; outcome unknown.");
    processExit = await exited.Task;
    lock (output) outputText = output.ToString();
    File.WriteAllText(Path.Combine(outputPath, "api-container.stdout.txt"), outputText ?? "", Encoding.UTF8);
    lock (errorOutput) errorText = errorOutput.ToString();
    File.WriteAllText(Path.Combine(outputPath, "api-container.stderr.txt"), errorText ?? "", Encoding.UTF8);
    Emit("container_exited", new { containerId, processExit, outputText });
    if (processExit != 0) throw new InvalidOperationException("Container runner exited nonzero.");
    using var summary = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(outputPath, "runner-summary.json")));
    if (summary.RootElement.GetProperty("status").GetString() != "PASS_PORTABILITY_SCOPED")
        throw new InvalidOperationException("Container runner summary is not PASS_PORTABILITY_SCOPED.");
}
catch (Exception ex)
{
    failure = ex;
    Emit("failure", new { type = ex.GetType().FullName, message = ex.Message, hresult = ex.HResult, containerId });
}
finally
{
    if (container is not null)
    {
        try
        {
            if (container.State == ContainerState.Running) container.Stop(Signal.SIGTERM, TimeSpan.FromSeconds(10));
            container.Delete(DeleteContainerOption.Force);
            containerDeleted = true;
            Emit("container_deleted", new { containerId });
        }
        catch (Exception ex)
        {
            failure ??= ex;
            Emit("container_cleanup_failure", new { type = ex.GetType().FullName, message = ex.Message, containerId });
        }
        finally { try { container.Dispose(); } catch { } }
    }
    lock (output) outputText ??= output.ToString();
    lock (errorOutput) errorText ??= errorOutput.ToString();
    try
    {
        File.WriteAllText(Path.Combine(outputPath, "api-container.stdout.txt"), outputText ?? "", Encoding.UTF8);
        File.WriteAllText(Path.Combine(outputPath, "api-container.stderr.txt"), errorText ?? "", Encoding.UTF8);
    }
    catch (Exception ex)
    {
        failure ??= ex;
        Emit("output_capture_failure", new { type = ex.GetType().FullName, message = ex.Message });
    }
    if (session is not null)
    {
        if (imagePulled && (container is null || containerDeleted))
        {
            try
            {
                session.DeleteImage(image);
                imageDeleted = true;
                Emit("image_deleted", new { image });
            }
            catch (Exception ex)
            {
                failure ??= ex;
                Emit("image_cleanup_failure", new { type = ex.GetType().FullName, message = ex.Message, image });
            }
        }
        try
        {
            if (sessionStarted)
            {
                session.Terminate();
                sessionTerminated = true;
                Emit("session_terminated", new { sessionName });
            }
        }
        catch (Exception ex)
        {
            failure ??= ex;
            Emit("session_termination_failure", new { type = ex.GetType().FullName, message = ex.Message, sessionName });
        }
        finally { try { session.Dispose(); } catch { } }
    }
    File.WriteAllText(Path.Combine(outputPath, "resource-cleanup.json"), JsonSerializer.Serialize(new
    {
        sessionName,
        storagePath,
        sessionStarted,
        sessionTerminated,
        image,
        imagePulled,
        imageDeleted,
        containerName,
        containerId,
        containerDeleted,
        processExit,
        failure = failure is null ? null : new { type = failure.GetType().FullName, message = failure.Message }
    }, new JsonSerializerOptions { WriteIndented = true }) + "\n", Encoding.UTF8);
}
return failure is null ? 0 : 1;

