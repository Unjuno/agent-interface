using Microsoft.WSL.Containers;
using System.Text;
using System.Text.Json;

static void Emit(string stage, object details)
{
    Console.WriteLine(JsonSerializer.Serialize(new { utc = DateTimeOffset.UtcNow, stage, details }));
    Console.Out.Flush();
}

if (args.Length != 5)
{
    Console.Error.WriteLine("usage: S04 <session-name> <storage-path> <image> <host-probe-dir> <container-name>");
    return 64;
}
var sessionName = args[0];
var storagePath = Path.GetFullPath(args[1]);
var image = args[2];
var hostProbeDir = Path.GetFullPath(args[3]);
var containerName = args[4];
var missing = WslcService.GetMissingComponents();
Emit("prerequisites", new { missing = missing.Select(x => x.ToString()).ToArray() });
if (missing.Count != 0) return 65;
var ver = WslcService.GetVersion();
Emit("version", new { ver.Major, ver.Minor, ver.Revision });
Session? session = null;
Container? container = null;
string? containerId = null;
string? outputText = null;
int? processExit = null;
Exception? failure = null;
bool imagePulled = false;
bool containerCleanupSucceeded = false;
bool sessionStarted = false;
try
{
    var settings = new SessionSettings(sessionName, storagePath)
    {
        CpuCount = 1,
        MemorySizeInMB = 1024,
        Timeout = TimeSpan.FromMinutes(10),
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

    const string probeCode = "import errno,hashlib,json,os;from pathlib import Path;p=Path('/probe/sentinel.bin');b=p.read_bytes();assert b==b'wslc-readonly-probe';\ntry:p.write_bytes(b'must-not-write')\nexcept OSError as e:assert e.errno==errno.EROFS;w=False\nelse:w=True\nassert not w;print(json.dumps({'probe':'PASS','python':os.sys.version.split()[0],'bytes_sha256':hashlib.sha256(b).hexdigest(),'write_rejected_errno':'EROFS'},sort_keys=True))";
    var init = new ProcessSettings
    {
        CommandLine = new List<string> { "python", "-B", "-c", probeCode },
        OutputMode = ProcessOutputMode.Event
    };
    var settingsForContainer = new ContainerSettings(image)
    {
        Name = containerName,
        InitProcess = init,
        NetworkingMode = ContainerNetworkingMode.None,
        EnableAutoRemove = false,
        EnableGpu = false,
        Privileged = false,
        Volumes = new List<ContainerVolume> { new(hostProbeDir, "/probe", readOnly: true) }
    };
    container = session.CreateContainer(settingsForContainer);
    containerId = container.Id;
    var exited = new TaskCompletionSource<int>(TaskCreationOptions.RunContinuationsAsynchronously);
    var output = new StringBuilder();
    container.InitProcess.OutputReceived += data =>
    {
        var chunk = Encoding.UTF8.GetString(data);
        lock (output) output.Append(chunk);
        Emit("container_stdout", new { text = chunk });
    };
    container.InitProcess.Exited += code => exited.TrySetResult(code);
    Emit("container_created", new { containerId, containerName, networkingMode = ContainerNetworkingMode.None.ToString(), volumeReadOnly = true });
    container.Start();
    var done = await Task.WhenAny(exited.Task, Task.Delay(TimeSpan.FromSeconds(90)));
    if (done != exited.Task) throw new TimeoutException("Container init process did not exit within 90 seconds; outcome unknown.");
    processExit = await exited.Task;
    lock (output) outputText = output.ToString();
    Emit("container_exited", new { containerId, processExit, outputText });
    if (processExit != 0 || outputText?.Contains("\"probe\":\"PASS\"", StringComparison.Ordinal) != true)
        throw new InvalidOperationException("Probe did not produce the expected PASS marker and zero exit code.");
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
            containerCleanupSucceeded = true;
            Emit("container_deleted", new { containerId });
        }
        catch (Exception ex)
        {
            failure ??= ex;
            Emit("container_cleanup_failure", new { type = ex.GetType().FullName, message = ex.Message, containerId });
        }
        finally
        {
            try { container.Dispose(); } catch { }
        }
    }
    if (session is not null)
    {
        if (imagePulled && containerCleanupSucceeded)
        {
            try
            {
                session.DeleteImage(image);
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
                Emit("session_terminated", new { sessionName });
            }
        }
        catch (Exception ex)
        {
            failure ??= ex;
            Emit("session_termination_failure", new { type = ex.GetType().FullName, message = ex.Message, sessionName });
        }
        finally
        {
            try { session.Dispose(); } catch { }
        }
    }
}
return failure is null ? 0 : 1;
