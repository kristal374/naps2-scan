using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using NAPS2.Images;
using NAPS2.Images.ImageSharp;
using NAPS2.Scan;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.PixelFormats;

namespace NAPS2Bridge;

public static class Bridge
{
    private static ScanningContext? _scanningContext;
    private static ScanController? _controller;

    public static void Initialize()
    {
        if (_scanningContext != null) return;

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
            : new CancellationTokenSource();
        var cancellationToken = cts.Token;

        var driver = ParseDriver(driverName);
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
        return JsonSerializer.Serialize(dtos, JsonOptions);
    }

    public static async Task<string> GetCapabilitiesAsync(string deviceJson)
    {
        EnsureInitialized();
        var deviceDto = JsonSerializer.Deserialize<ScanDeviceDto>(deviceJson, JsonOptions)
                        ?? throw new ArgumentException("Invalid device JSON", nameof(deviceJson));
        var device = ToScanDevice(deviceDto);
        var caps = await _controller!.GetCaps(device);
        var result = ToCapabilitiesDto(caps);
        return JsonSerializer.Serialize(result, JsonOptions);
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
        var options = ParseScanOptions(optionsJson);

        var controller = _controller!;
        var currentPage = 0;

        void OnScanStart(object? sender, EventArgs e) => onScanStart?.Invoke();
        void OnScanEnd(object? sender, ScanEndEventArgs e) => onScanEnd?.Invoke();
        void OnPageStart(object? sender, PageStartEventArgs e)
        {
            currentPage = e.PageNumber;
            onPageStart?.Invoke(e.PageNumber);
        }
        void OnPageProgress(object? sender, PageProgressEventArgs e) => onProgress?.Invoke(e.PageNumber, e.Progress);
        void OnPageEnd(object? sender, PageEndEventArgs e) => onPageEnd?.Invoke(e.PageNumber);

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
        int rowBytes = BytesPerRow(width, pixelFormat);

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

        return (buffer, width, height, MapPixelFormat(pixelFormat));
    }

    private static int BytesPerRow(int width, ImagePixelFormat format) => format switch
    {
        ImagePixelFormat.BW1 => (width + 7) / 8,
        ImagePixelFormat.Gray8 => width,
        ImagePixelFormat.RGB24 => width * 3,
        ImagePixelFormat.ARGB32 => width * 4,
        _ => throw new NotSupportedException($"Unsupported pixel format: {format}"),
    };

    private static string MapPixelFormat(ImagePixelFormat format) => format switch
    {
        ImagePixelFormat.BW1 => "1",
        ImagePixelFormat.Gray8 => "L",
        ImagePixelFormat.RGB24 => "RGB",
        ImagePixelFormat.ARGB32 => "RGBA",
        _ => throw new NotSupportedException($"Unsupported pixel format: {format}"),
    };


    public static string GetImageInfo(object imageHandle)
    {
        var processedImage = (ProcessedImage)imageHandle;
        using var rendered = ((IRenderableImage)processedImage).Render();
        if (rendered is not ImageSharpImage imageSharp)
        {
            throw new InvalidOperationException("Rendered image is not an ImageSharp image.");
        }

        var info = new ImageInfoDto
        {
            Width = imageSharp.Width,
            Height = imageSharp.Height,
            Dpi = (int)Math.Round(imageSharp.HorizontalResolution),
            PixelFormat = imageSharp.PixelFormat.ToString()
        };

        return JsonSerializer.Serialize(info, JsonOptions);
    }

    public static byte[] GetImageBytes(object imageHandle, string pixelFormat)
    {
        var processedImage = (ProcessedImage)imageHandle;
        return pixelFormat.ToLowerInvariant() switch
        {
            "rgb24" => GetPixelBytes<Rgb24>(processedImage),
            "rgba32" => GetPixelBytes<Rgba32>(processedImage),
            "gray8" => GetPixelBytes<L8>(processedImage),
            _ => throw new ArgumentException($"Unsupported pixel format: {pixelFormat}", nameof(pixelFormat))
        };
    }

    public static byte[] GetImagePng(object imageHandle)
    {
        var processedImage = (ProcessedImage)imageHandle;
        using var stream = new MemoryStream();
        processedImage.Save(stream, ImageFileFormat.Png);
        return stream.ToArray();
    }

    public static byte[] GetImageJpeg(object imageHandle, int quality)
    {
        var processedImage = (ProcessedImage)imageHandle;
        using var stream = new MemoryStream();
        processedImage.Save(stream, ImageFileFormat.Jpeg, new ImageSaveOptions { Quality = quality });
        return stream.ToArray();
    }

    public static object CloneImage(object imageHandle)
    {
        var processedImage = (ProcessedImage)imageHandle;
        return processedImage.Clone();
    }

    public static void ReleaseImage(object imageHandle)
    {
        if (imageHandle is ProcessedImage image)
        {
            image.Dispose();
        }
    }

    private static byte[] GetPixelBytes<TPixel>(ProcessedImage processedImage)
        where TPixel : unmanaged, IPixel<TPixel>
    {
        using var rendered = ((IRenderableImage)processedImage).Render();
        if (rendered is not ImageSharpImage imageSharp)
        {
            throw new InvalidOperationException("Rendered image is not an ImageSharp image.");
        }

        Image<TPixel> typedImage;
        bool ownsImage;
        if (imageSharp.Image is Image<TPixel> exact)
        {
            typedImage = exact;
            ownsImage = false;
        }
        else
        {
            typedImage = imageSharp.Image.CloneAs<TPixel>();
            ownsImage = true;
        }

        try
        {
            if (!typedImage.DangerousTryGetSinglePixelMemory(out var memory))
            {
                throw new InvalidOperationException("Could not get contiguous pixel memory from ImageSharp image.");
            }

            return MemoryMarshal.AsBytes(memory.Span).ToArray();
        }
        finally
        {
            if (ownsImage)
            {
                typedImage.Dispose();
            }
        }
    }

    private static NAPS2.Scan.ScanOptions ParseScanOptions(string json)
    {
        var dto = JsonSerializer.Deserialize<ScanOptionsDto>(json, JsonOptions)
                  ?? throw new ArgumentException("Invalid scan options JSON", nameof(json));

        var options = new NAPS2.Scan.ScanOptions();

        if (dto.Dpi.HasValue) options.Dpi = dto.Dpi.Value;
        if (dto.ColorMode != null) options.BitDepth = ParseColorMode(dto.ColorMode);
        if (dto.PaperSource != null) options.PaperSource = ParsePaperSource(dto.PaperSource);
        if (dto.PageSize != null) options.PageSize = ParsePageSize(dto.PageSize);
        if (dto.Brightness.HasValue) options.Brightness = dto.Brightness.Value;
        if (dto.Contrast.HasValue) options.Contrast = dto.Contrast.Value;
        if (dto.BrightnessContrastAfterScan.HasValue) options.BrightnessContrastAfterScan = dto.BrightnessContrastAfterScan.Value;
        if (dto.UseNativeUI.HasValue) options.UseNativeUI = dto.UseNativeUI.Value;

        if (dto.Device != null)
        {
            options.Device = ToScanDevice(dto.Device);
        }

        return options;
    }

    private static ScanDevice ToScanDevice(ScanDeviceDto dto)
    {
        return new ScanDevice(
            ParseDriver(dto.Driver),
            dto.Id,
            dto.Name,
            dto.IconUri,
            dto.ConnectionUri);
    }

    private static Driver ParseDriver(string? value)
    {
        return value?.ToLowerInvariant() switch
        {
            null or "default" => Driver.Default,
            "wia" => Driver.Wia,
            "twain" => Driver.Twain,
            "sane" => Driver.Sane,
            "escl" => Driver.Escl,
            "apple" => Driver.Apple,
            _ => throw new ArgumentException($"Unknown driver: {value}")
        };
    }

    private static BitDepth ParseColorMode(string value)
    {
        return value.ToLowerInvariant() switch
        {
            "color" => BitDepth.Color,
            "gray" => BitDepth.Grayscale,
            "bw" => BitDepth.BlackAndWhite,
            _ => throw new ArgumentException($"Unknown color mode: {value}")
        };
    }

    private static PaperSource ParsePaperSource(string value)
    {
        return value.ToLowerInvariant() switch
        {
            "flatbed" => PaperSource.Flatbed,
            "feeder" => PaperSource.Feeder,
            "duplex" => PaperSource.Duplex,
            _ => throw new ArgumentException($"Unknown paper source: {value}")
        };
    }

    private static NAPS2.Images.PageSize ParsePageSize(string value)
    {
        var trimmed = value.Trim();
        var parsed = NAPS2.Images.PageSize.Parse(trimmed);
        if (parsed != null) return parsed;

        throw new ArgumentException($"Invalid page size: {value}");
    }

    private static ScannerCapabilitiesDto ToCapabilitiesDto(ScanCaps caps)
    {
        var dto = new ScannerCapabilitiesDto();

        if (caps.PaperSourceCaps != null)
        {
            var sources = new List<string>();
            if (caps.PaperSourceCaps.SupportsFlatbed) sources.Add("flatbed");
            if (caps.PaperSourceCaps.SupportsFeeder) sources.Add("feeder");
            if (caps.PaperSourceCaps.SupportsDuplex) sources.Add("duplex");
        }

        dto.Flatbed = ToSourceCapabilitiesDto(caps.FlatbedCaps, "flatbed");
        dto.Feeder = ToSourceCapabilitiesDto(caps.FeederCaps, "feeder");
        dto.Duplex = ToSourceCapabilitiesDto(caps.DuplexCaps, "duplex");

        return dto;
    }

    private static SourceCapabilitiesDto? ToSourceCapabilitiesDto(PerSourceCaps? caps, string sourceType)
    {
        if (caps == null) return null;

        var dpiValues = caps.DpiCaps?.Values;
        var resolutions = caps.DpiCaps?.CommonValues?.ToList()
                          ?? dpiValues?.ToList()
                          ?? new List<int>();
        var colorModes = new List<string>();
        if (caps.BitDepthCaps?.SupportsColor ?? false) colorModes.Add("color");
        if (caps.BitDepthCaps?.SupportsGrayscale ?? false) colorModes.Add("gray");
        if (caps.BitDepthCaps?.SupportsBlackAndWhite ?? false) colorModes.Add("bw");

        var maxArea = caps.PageSizeCaps?.ScanArea;

        return new SourceCapabilitiesDto
        {
            Type = sourceType,
            Resolutions = resolutions,
            ColorModes = colorModes,
            MaxScanArea = maxArea == null ? null : new ScanAreaSizeDto
            {
                Width = maxArea.Width,
                Height = maxArea.Height,
                Unit = maxArea.Unit switch
                {
                    PageSizeUnit.Millimetre => "mm",
                    PageSizeUnit.Centimetre => "cm",
                    PageSizeUnit.Inch => "in",
                    _ => maxArea.Unit.ToString().ToLowerInvariant()
                }
            }
        };
    }

    private static JsonSerializerOptions JsonOptions => new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    private class ScanDeviceDto
    {
        public string Driver { get; set; } = string.Empty;
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string? IconUri { get; set; }
        public string? ConnectionUri { get; set; }
    }

    private class ScanOptionsDto
    {
        public int? Dpi { get; set; }
        public string? ColorMode { get; set; }
        public string? PaperSource { get; set; }
        public string? PageSize { get; set; }
        public int? Brightness { get; set; }
        public int? Contrast { get; set; }
        public bool? BrightnessContrastAfterScan { get; set; }
        public bool? UseNativeUI { get; set; }
        public ScanDeviceDto? Device { get; set; }
    }

    private class ImageInfoDto
    {
        public int Width { get; set; }
        public int Height { get; set; }
        public int Dpi { get; set; }
        public string PixelFormat { get; set; } = string.Empty;
    }

    private class ScannerCapabilitiesDto
    {
        public SourceCapabilitiesDto? Flatbed { get; set; }
        public SourceCapabilitiesDto? Feeder { get; set; }
        public SourceCapabilitiesDto? Duplex { get; set; }
    }

    private class SourceCapabilitiesDto
    {
        public string Type { get; set; } = string.Empty;
        public List<int> Resolutions { get; set; } = new();
        public List<string> ColorModes { get; set; } = new();
        public ScanAreaSizeDto? MaxScanArea { get; set; }
    }

    private class ScanAreaSizeDto
    {
        public decimal Width { get; set; }
        public decimal Height { get; set; }
        public string Unit { get; set; } = string.Empty;
    }
}
