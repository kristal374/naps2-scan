namespace NAPS2Bridge;

internal class ScanDeviceDto
{
    public string Driver { get; set; } = string.Empty;
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? IconUri { get; set; }
    public string? ConnectionUri { get; set; }
}

internal class ScanOptionsDto
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

internal class ScannerCapabilitiesDto
{
    public CapsMetadataDto? Metadata { get; set; }
    public SourceCapabilitiesDto? Flatbed { get; set; }
    public SourceCapabilitiesDto? Feeder { get; set; }
    public SourceCapabilitiesDto? Duplex { get; set; }
}

internal class SourceCapabilitiesDto
{
    public string Type { get; set; } = string.Empty;
    public List<int> Resolutions { get; set; } = new();
    public List<string> ColorModes { get; set; } = new();
    public ScanAreaSizeDto? MaxScanArea { get; set; }
}

internal class ScanAreaSizeDto
{
    public decimal Width { get; set; }
    public decimal Height { get; set; }
    public string Unit { get; set; } = string.Empty;
}

internal class CapsMetadataDto
{
    public string? DriverSubtype { get; set; }
    public string? IconUri { get; set; }
    public string? Manufacturer { get; set; }
    public string? Model { get; set; }
    public string? SerialNumber { get; set; }
}
