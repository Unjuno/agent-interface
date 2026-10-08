using Microsoft.WSL.Containers;

if (args.Length != 2)
{
    Console.Error.WriteLine("usage: harness <session-name> <storage-path>");
    return 2;
}
var name = args[0];
var storage = Path.GetFullPath(args[1]);
Directory.CreateDirectory(storage);
var settings = new SessionSettings(name, storage)
{
    CpuCount = 1,
    MemorySizeInMB = 1024
};
var session = new Session(settings);
try
{
    session.Start();
    Console.WriteLine($"SESSION_READY name={name} memoryMB=1024 cpuCount=1 storage={storage}");
    Console.Out.Flush();
    Console.ReadLine();
    session.Terminate();
    Console.WriteLine("SESSION_TERMINATED");
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine(error);
    return 1;
}
