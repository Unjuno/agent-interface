using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public sealed class EmiChannelSample
{
    public string name { get; set; }
    public uint unit_code { get; set; }
    public string unit { get; set; }
    public string absolute_energy { get; set; }
    public string absolute_time_100ns { get; set; }
}

public sealed class EmiDeviceSample
{
    public int device_index { get; set; }
    public ushort version { get; set; }
    public string hardware_oem { get; set; }
    public string hardware_model { get; set; }
    public string metered_hardware_name { get; set; }
    public string error { get; set; }
    public List<EmiChannelSample> channels { get; set; }
}

public static class EmiProbe
{
    private const int DigcfPresent = 0x2;
    private const int DigcfDeviceInterface = 0x10;
    private const uint FileDeviceUnknown = 0x22;
    private const uint FileReadAccess = 0x1;
    private const uint MethodBuffered = 0;
    private const uint IoctlGetVersion = (FileDeviceUnknown << 16) | (FileReadAccess << 14) | (0u << 2) | MethodBuffered;
    private const uint IoctlGetMetadataSize = (FileDeviceUnknown << 16) | (FileReadAccess << 14) | (1u << 2) | MethodBuffered;
    private const uint IoctlGetMetadata = (FileDeviceUnknown << 16) | (FileReadAccess << 14) | (2u << 2) | MethodBuffered;
    private const uint IoctlGetMeasurement = (FileDeviceUnknown << 16) | (FileReadAccess << 14) | (3u << 2) | MethodBuffered;
    private static readonly Guid DeviceEnergyMeter = new Guid("45bd8344-7ed6-49cf-a440-c276c933b053");

    [StructLayout(LayoutKind.Sequential)]
    private struct DeviceInterfaceData
    {
        public int cbSize;
        public Guid InterfaceClassGuid;
        public int Flags;
        public IntPtr Reserved;
    }

    [DllImport("setupapi.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr SetupDiGetClassDevsW(ref Guid classGuid, string enumerator, IntPtr hwndParent, int flags);

    [DllImport("setupapi.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiEnumDeviceInterfaces(IntPtr deviceInfoSet, IntPtr deviceInfoData, ref Guid interfaceClassGuid, uint memberIndex, ref DeviceInterfaceData deviceInterfaceData);

    [DllImport("setupapi.dll", EntryPoint = "SetupDiGetDeviceInterfaceDetailW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiGetDeviceInterfaceDetail(IntPtr deviceInfoSet, ref DeviceInterfaceData deviceInterfaceData, IntPtr deviceInterfaceDetailData, uint deviceInterfaceDetailDataSize, out uint requiredSize, IntPtr deviceInfoData);

    [DllImport("setupapi.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiDestroyDeviceInfoList(IntPtr deviceInfoSet);

    [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFile(string fileName, uint desiredAccess, uint shareMode, IntPtr securityAttributes, uint creationDisposition, uint flagsAndAttributes, IntPtr templateFile);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool DeviceIoControl(SafeFileHandle device, uint controlCode, IntPtr inputBuffer, uint inputBufferSize, IntPtr outputBuffer, uint outputBufferSize, out uint bytesReturned, IntPtr overlapped);

    private static bool Ioctl(SafeFileHandle handle, uint code, IntPtr output, uint outputSize, out uint bytes, out string error)
    {
        bool ok = DeviceIoControl(handle, code, IntPtr.Zero, 0, output, outputSize, out bytes, IntPtr.Zero);
        error = ok ? null : new Win32Exception(Marshal.GetLastWin32Error()).Message;
        return ok;
    }

    private static string ReadWide(IntPtr ptr, int chars)
    {
        if (chars <= 0) return "";
        string value = Marshal.PtrToStringUni(ptr, chars) ?? "";
        return value.TrimEnd('\0');
    }

    private static string UnitName(uint code)
    {
        return code == 0 ? "picowatt-hours" : "unsupported-unit-code-" + code.ToString();
    }

    private static List<EmiDeviceSample> ReadDevice(IntPtr set, ref DeviceInterfaceData iface, int index)
    {
        var result = new List<EmiDeviceSample>();
        uint required;
        SetupDiGetDeviceInterfaceDetail(set, ref iface, IntPtr.Zero, 0, out required, IntPtr.Zero);
        int firstError = Marshal.GetLastWin32Error();
        if (required == 0 || (firstError != 122 && firstError != 0))
        {
            result.Add(new EmiDeviceSample { device_index = index, error = "DETAIL_SIZE:" + firstError.ToString(), channels = new List<EmiChannelSample>() });
            return result;
        }

        IntPtr detail = Marshal.AllocHGlobal((int)required);
        try
        {
            Marshal.WriteInt32(detail, IntPtr.Size == 8 ? 8 : 6);
            uint secondRequired;
            if (!SetupDiGetDeviceInterfaceDetail(set, ref iface, detail, required, out secondRequired, IntPtr.Zero))
            {
                result.Add(new EmiDeviceSample { device_index = index, error = "DETAIL_PATH:" + Marshal.GetLastWin32Error().ToString(), channels = new List<EmiChannelSample>() });
                return result;
            }

            string path = Marshal.PtrToStringUni(IntPtr.Add(detail, 4));
            using (SafeFileHandle handle = CreateFile(path, 0x80000000u, 0x3u, IntPtr.Zero, 3u, 0u, IntPtr.Zero))
            {
                if (handle == null || handle.IsInvalid)
                {
                    result.Add(new EmiDeviceSample { device_index = index, error = "OPEN_DEVICE:" + Marshal.GetLastWin32Error().ToString(), channels = new List<EmiChannelSample>() });
                    return result;
                }

                IntPtr versionBuffer = Marshal.AllocHGlobal(2);
                try
                {
                    uint returned;
                    string error;
                    if (!Ioctl(handle, IoctlGetVersion, versionBuffer, 2, out returned, out error))
                    {
                        result.Add(new EmiDeviceSample { device_index = index, error = "GET_VERSION:" + error, channels = new List<EmiChannelSample>() });
                        return result;
                    }
                    ushort version = unchecked((ushort)Marshal.ReadInt16(versionBuffer));

                    IntPtr sizeBuffer = Marshal.AllocHGlobal(4);
                    try
                    {
                        if (!Ioctl(handle, IoctlGetMetadataSize, sizeBuffer, 4, out returned, out error))
                        {
                            result.Add(new EmiDeviceSample { device_index = index, version = version, error = "GET_METADATA_SIZE:" + error, channels = new List<EmiChannelSample>() });
                            return result;
                        }
                        int metadataSize = Marshal.ReadInt32(sizeBuffer);
                        if (metadataSize < 4 || metadataSize > 65536)
                        {
                            result.Add(new EmiDeviceSample { device_index = index, version = version, error = "INVALID_METADATA_SIZE:" + metadataSize.ToString(), channels = new List<EmiChannelSample>() });
                            return result;
                        }

                        IntPtr metadata = Marshal.AllocHGlobal(metadataSize);
                        try
                        {
                            if (!Ioctl(handle, IoctlGetMetadata, metadata, (uint)metadataSize, out returned, out error))
                            {
                                result.Add(new EmiDeviceSample { device_index = index, version = version, error = "GET_METADATA:" + error, channels = new List<EmiChannelSample>() });
                                return result;
                            }

                            var device = new EmiDeviceSample { device_index = index, version = version, channels = new List<EmiChannelSample>() };
                            int channelCount;
                            if (version == 1)
                            {
                                uint unit = unchecked((uint)Marshal.ReadInt32(metadata, 0));
                                device.hardware_oem = ReadWide(IntPtr.Add(metadata, 4), 16);
                                device.hardware_model = ReadWide(IntPtr.Add(metadata, 36), 16);
                                ushort nameBytes = unchecked((ushort)Marshal.ReadInt16(metadata, 70));
                                device.metered_hardware_name = nameBytes >= 2 ? ReadWide(IntPtr.Add(metadata, 72), nameBytes / 2 - 1) : "";
                                channelCount = 1;
                                device.channels.Add(new EmiChannelSample { name = device.metered_hardware_name, unit_code = unit, unit = UnitName(unit) });
                            }
                            else if (version == 2)
                            {
                                device.hardware_oem = ReadWide(metadata, 16);
                                device.hardware_model = ReadWide(IntPtr.Add(metadata, 32), 16);
                                channelCount = Marshal.ReadInt16(metadata, 66);
                                int offset = 68;
                                for (int i = 0; i < channelCount; i++)
                                {
                                    if (offset + 6 > metadataSize) throw new InvalidOperationException("V2_METADATA_TRUNCATED");
                                    uint unit = unchecked((uint)Marshal.ReadInt32(metadata, offset));
                                    ushort nameBytes = unchecked((ushort)Marshal.ReadInt16(metadata, offset + 4));
                                    int nameChars = nameBytes / 2;
                                    if (nameBytes < 2 || offset + 6 + nameBytes > metadataSize) throw new InvalidOperationException("V2_CHANNEL_NAME_TRUNCATED");
                                    string channelName = ReadWide(IntPtr.Add(metadata, offset + 6), nameChars - 1);
                                    device.channels.Add(new EmiChannelSample { name = channelName, unit_code = unit, unit = UnitName(unit) });
                                    offset += 6 + nameBytes;
                                }
                            }
                            else
                            {
                                device.error = "UNSUPPORTED_EMI_VERSION:" + version.ToString();
                                result.Add(device);
                                return result;
                            }

                            int measurementSize = Math.Max(16, channelCount * 16);
                            IntPtr measurement = Marshal.AllocHGlobal(measurementSize);
                            try
                            {
                                if (!Ioctl(handle, IoctlGetMeasurement, measurement, (uint)measurementSize, out returned, out error))
                                {
                                    device.error = "GET_MEASUREMENT:" + error;
                                    result.Add(device);
                                    return result;
                                }
                                for (int i = 0; i < channelCount; i++)
                                {
                                    int offset = i * 16;
                                    device.channels[i].absolute_energy = unchecked((ulong)Marshal.ReadInt64(measurement, offset)).ToString(System.Globalization.CultureInfo.InvariantCulture);
                                    device.channels[i].absolute_time_100ns = unchecked((ulong)Marshal.ReadInt64(measurement, offset + 8)).ToString(System.Globalization.CultureInfo.InvariantCulture);
                                }
                            }
                            finally { Marshal.FreeHGlobal(measurement); }

                            result.Add(device);
                        }
                        finally { Marshal.FreeHGlobal(metadata); }
                    }
                    finally { Marshal.FreeHGlobal(sizeBuffer); }
                }
                finally { Marshal.FreeHGlobal(versionBuffer); }
            }
        }
        finally { Marshal.FreeHGlobal(detail); }
        return result;
    }

    public static List<EmiDeviceSample> ReadOnce()
    {
        Guid guid = DeviceEnergyMeter;
        IntPtr set = SetupDiGetClassDevsW(ref guid, null, IntPtr.Zero, DigcfPresent | DigcfDeviceInterface);
        if (set == new IntPtr(-1)) throw new Win32Exception(Marshal.GetLastWin32Error(), "SETUP_DI_ENUMERATION_FAILED");
        var all = new List<EmiDeviceSample>();
        try
        {
            for (uint i = 0; i < 64; i++)
            {
                var iface = new DeviceInterfaceData();
                iface.cbSize = Marshal.SizeOf(typeof(DeviceInterfaceData));
                if (!SetupDiEnumDeviceInterfaces(set, IntPtr.Zero, ref guid, i, ref iface))
                {
                    int error = Marshal.GetLastWin32Error();
                    if (error == 259) break;
                    throw new Win32Exception(error, "SETUP_DI_ENUMERATION_FAILED");
                }
                all.AddRange(ReadDevice(set, ref iface, (int)i));
            }
        }
        finally { SetupDiDestroyDeviceInfoList(set); }
        return all;
    }
}
