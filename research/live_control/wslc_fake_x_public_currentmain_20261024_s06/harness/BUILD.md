S06 short-path build log (prepared before any S06 WSLc session):

`dotnet restore harness/S06.csproj --ignore-failed-sources` — PASS (0.150 s; package restored from local NuGet cache).

`dotnet build harness/S06.csproj --no-restore --configuration Release --output C:\wslc-s06-5302b011\bin` — PASS, 0 warnings, 0 errors. The native output path is 60 characters, compared with S05's 252-character native DLL path.

No WSLc API call, session, image pull or container run was performed by these build commands.
