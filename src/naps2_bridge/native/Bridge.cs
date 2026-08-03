namespace NAPS2Bridge;

public static class Bridge
{
    public static void Initialize()
    {
        Console.WriteLine("NAPS2Bridge initialized");
    }

    public static string[] GetDevices(string driver)
    {
        return Array.Empty<string>();
    }

    public static void Shutdown()
    {
    }
}
