using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using NAPS2.Images;
using NAPS2.Images.ImageSharp;
using NAPS2.Scan;

namespace NAPS2Bridge;

public static class Bridge
{
    private static ScanningContext? _scanningContext;
    private static ScanController? _controller;

    public static void Initialize()
    {
        if (_controller != null) return;

        _scanningContext = new ScanningContext(new ImageSharpImageContext());

        if (OperatingSystem.IsWindows())
        {
            _scanningContext.SetUpWin32Worker();
        }

        _controller = new ScanController(_scanningContext);
    }

    public static void Shutdown()
    {
        _controller = null;
        _scanningContext?.Dispose();
        _scanningContext = null;
    }

    private static void EnsureInitialized()
    {
        if (_controller == null)
            throw new InvalidOperationException("Bridge is not initialized. Call Initialize() first.");
    }

    public static Task<string> GetDevicesAsync(string driverName) =>
        GetDevicesAsync(driverName, 0);

    public static async Task<string> GetDevicesAsync(
        string driverName,
        int timeoutMilliseconds = 0)
    {
        EnsureInitialized();
        using var cts = timeoutMilliseconds > 0
            ? new CancellationTokenSource(timeoutMilliseconds)
            : null;
        var cancellationToken = timeoutMilliseconds > 0 ? cts!.Token : CancellationToken.None;

        var driver = Converters.ParseDriver(driverName);
        var devices = new List<ScanDevice>();
        await foreach (var device in _controller!.GetDevices(driver, cancellationToken))
        {
            devices.Add(device);
        }
        var dtos = devices.Select(d => new ScanDeviceDto
        {
            Driver = d.Driver.ToString(),
            Id = d.ID,
            Name = d.Name,
            IconUri = d.IconUri,
            ConnectionUri = d.ConnectionUri
        });
        return JsonSerializer.Serialize(dtos, Converters.JsonOptions);
    }

    public static async Task<string> GetCapabilitiesAsync(string deviceJson)
    {
        EnsureInitialized();
        var deviceDto = JsonSerializer.Deserialize<ScanDeviceDto>(deviceJson, Converters.JsonOptions)
                        ?? throw new ArgumentException("Invalid device JSON", nameof(deviceJson));
        var device = Converters.ToScanDevice(deviceDto);
        var caps = await _controller!.GetCaps(device);
        var result = Converters.ToCapabilitiesDto(caps);
        return JsonSerializer.Serialize(result, Converters.JsonOptions);
    }

    public static async Task ScanAsync(
        string optionsJson,
        Action? onScanStart,
        Action? onScanEnd,
        Action<int>? onPageStart,
        Action<int>? onPageEnd,
        Action<byte[], int, int, string>? onPage,
        Action<int, double>? onProgress,
        CancellationToken cancellationToken)
    {
        EnsureInitialized();
        var options = Converters.ParseScanOptions(optionsJson);

        var controller = _controller!;
        var currentPage = 0;
        var reportedPage = 0;

        void OnScanStart(object? sender, EventArgs e) => onScanStart?.Invoke();
        void OnScanEnd(object? sender, ScanEndEventArgs e) => onScanEnd?.Invoke();
        void OnPageStart(object? sender, PageStartEventArgs e)
        {
            currentPage = e.PageNumber;
        }
        void ReportPageStartIfNeeded(int pageNumber)
        {
            if (reportedPage == pageNumber)
                return;
            reportedPage = pageNumber;
            onPageStart?.Invoke(pageNumber);
        }
        void OnPageProgress(object? sender, PageProgressEventArgs e)
        {
            ReportPageStartIfNeeded(e.PageNumber);
            onProgress?.Invoke(e.PageNumber, e.Progress);
        }
        void OnPageEnd(object? sender, PageEndEventArgs e)
        {
            ReportPageStartIfNeeded(e.PageNumber);
            onPageEnd?.Invoke(e.PageNumber);
        }

        controller.ScanStart += OnScanStart;
        controller.ScanEnd += OnScanEnd;
        controller.PageStart += OnPageStart;
        controller.PageProgress += OnPageProgress;
        controller.PageEnd += OnPageEnd;

        try
        {
            await foreach (var image in controller.Scan(options).WithCancellation(cancellationToken))
            {
                if (onPage != null)
                {
                    var (rawBytes, width, height, pixelFormat) = ExtractRawPixels(image);
                    onPage(rawBytes, width, height, pixelFormat);
                }

                image.Dispose();
            }
        }
        finally
        {
            controller.ScanStart -= OnScanStart;
            controller.ScanEnd -= OnScanEnd;
            controller.PageStart -= OnPageStart;
            controller.PageProgress -= OnPageProgress;
            controller.PageEnd -= OnPageEnd;
        }
    }

    private static unsafe (byte[] Bytes, int Width, int Height, string PixelFormat) ExtractRawPixels(
        ProcessedImage processedImage)
    {
        using var image = processedImage.Render();
        using var lockState = image.Lock(LockMode.ReadOnly, out var imageData);

        int width = image.Width;
        int height = image.Height;
        int stride = imageData.stride;
        var pixelFormat = image.PixelFormat;
        int rowBytes = Converters.BytesPerRow(width, pixelFormat);

        byte[] buffer;
        if (rowBytes == stride)
        {
            buffer = new byte[stride * height];
            Marshal.Copy((IntPtr)imageData.ptr, buffer, 0, buffer.Length);
        }
        else
        {
            buffer = new byte[rowBytes * height];
            for (int y = 0; y < height; y++)
            {
                IntPtr srcRow = IntPtr.Add((IntPtr)imageData.ptr, y * stride);
                Marshal.Copy(srcRow, buffer, y * rowBytes, rowBytes);
            }
        }

        return (buffer, width, height, Converters.MapPixelFormat(pixelFormat));
    }
}
