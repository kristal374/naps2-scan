using System.Text.Json;
using System.Text.Json.Serialization;
using NAPS2.Images;
using NAPS2.Scan;

namespace NAPS2Bridge;

internal static class Converters
{
    internal static JsonSerializerOptions JsonOptions => new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public static NAPS2.Scan.ScanOptions ParseScanOptions(string json)
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

    public static ScanDevice ToScanDevice(ScanDeviceDto dto)
    {
        return new ScanDevice(
            ParseDriver(dto.Driver),
            dto.Id,
            dto.Name,
            dto.IconUri,
            dto.ConnectionUri);
    }

    public static Driver ParseDriver(string? value)
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

    public static BitDepth ParseColorMode(string value)
    {
        return value.ToLowerInvariant() switch
        {
            "color" => BitDepth.Color,
            "gray" => BitDepth.Grayscale,
            "bw" => BitDepth.BlackAndWhite,
            _ => throw new ArgumentException($"Unknown color mode: {value}")
        };
    }

    public static PaperSource ParsePaperSource(string value)
    {
        return value.ToLowerInvariant() switch
        {
            "flatbed" => PaperSource.Flatbed,
            "feeder" => PaperSource.Feeder,
            "duplex" => PaperSource.Duplex,
            _ => throw new ArgumentException($"Unknown paper source: {value}")
        };
    }

    public static PageSize ParsePageSize(string value)
    {
        var trimmed = value.Trim();
        var parsed = PageSize.Parse(trimmed);
        return parsed ?? throw new ArgumentException($"Invalid page size: {value}", nameof(value));
    }

    public static ScannerCapabilitiesDto ToCapabilitiesDto(ScanCaps caps)
    {
        return new ScannerCapabilitiesDto
        {
            Metadata = ToMetadataDto(caps.MetadataCaps),
            Flatbed = ToSourceCapabilitiesDto(caps.FlatbedCaps, "flatbed"),
            Feeder = ToSourceCapabilitiesDto(caps.FeederCaps, "feeder"),
            Duplex = ToSourceCapabilitiesDto(caps.DuplexCaps, "duplex"),
        };
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

    private static CapsMetadataDto? ToMetadataDto(MetadataCaps? metadata)
    {
        if (metadata == null) return null;

        return new CapsMetadataDto
        {
            DriverSubtype = metadata.DriverSubtype,
            IconUri = metadata.IconUri,
            Manufacturer = metadata.Manufacturer,
            Model = metadata.Model,
            SerialNumber = metadata.SerialNumber,
        };
    }

    public static string MapPixelFormat(ImagePixelFormat format) => format switch
    {
        ImagePixelFormat.BW1 => "1",
        ImagePixelFormat.Gray8 => "L",
        ImagePixelFormat.RGB24 => "RGB",
        ImagePixelFormat.ARGB32 => "RGBA",
        _ => throw new NotSupportedException($"Unsupported pixel format: {format}"),
    };

    public static int BytesPerRow(int width, ImagePixelFormat format) => format switch
    {
        ImagePixelFormat.BW1 => (width + 7) / 8,
        ImagePixelFormat.Gray8 => width,
        ImagePixelFormat.RGB24 => width * 3,
        ImagePixelFormat.ARGB32 => width * 4,
        _ => throw new NotSupportedException($"Unsupported pixel format: {format}"),
    };
}
