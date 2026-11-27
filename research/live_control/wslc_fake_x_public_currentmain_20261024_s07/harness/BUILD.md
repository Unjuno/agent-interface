S07 native WSLc harness build (final source before run):

- `dotnet restore harness/S07.csproj --ignore-failed-sources` — PASS, local NuGet cache.
- `dotnet build harness/S07.csproj --no-restore --configuration Release --output C:\wslc-s07-a7c41f29\bin` — PASS, 0 warnings, 0 errors.
- Native DLL path: `C:\wslc-s07-a7c41f29\bin\runtimes\win-x64\native\wslcsdk.dll` (60 characters).
- Build output is outside the repository; local `bin/` and `obj/` directories are ignored.
- Two pre-run S07 draft builds caught preparation defects: literal newline escape text, then buffer scope. Both were fixed before any S07 WSLc session; final build passed.
