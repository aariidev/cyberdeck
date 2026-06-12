using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace CyberDeck
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            Log("[SYSTEM] CYBERDECK v3.0 INITIALIZED.");
            Log("[SYSTEM] AWAITING COMMAND...");
        }

        private void Log(string message, bool isError = false)
        {
            Dispatcher.Invoke(() =>
            {
                var time = DateTime.Now.ToString("HH:mm:ss");
                var prefix = isError ? "[ERROR]" : "[INFO]";
                LogText.Text += $"[{time}] {prefix} {message}\n";
                LogScroll.ScrollToEnd();
            });
        }

        private async void BtnScanRemovable_Click(object sender, RoutedEventArgs e)
        {
            await ScanDisksAsync(removableOnly: true);
        }

        private async void BtnFullScan_Click(object sender, RoutedEventArgs e)
        {
            var result = MessageBox.Show("Proceed with full system scan? This includes internal drives and is DANGEROUS!", "WARNING", MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (result == MessageBoxResult.Yes)
            {
                await ScanDisksAsync(removableOnly: false);
            }
        }

        private async Task ScanDisksAsync(bool removableOnly)
        {
            Log("SCANNING NEURAL LINKS...");
            DisksDataGrid.ItemsSource = null;
            DisableActionButtons();

            try
            {
                var disks = await Task.Run(() => GetDisks(removableOnly));
                
                if (disks.Count == 0)
                {
                    Log("No units detected.", true);
                }
                else
                {
                    Log($"Found {disks.Count} unit(s).");
                    DisksDataGrid.ItemsSource = disks;
                }
            }
            catch (Exception ex)
            {
                Log($"Scan failed: {ex.Message}", true);
            }
        }

        private void DisksDataGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var selected = DisksDataGrid.SelectedItem as DiskInfo;
            if (selected != null)
            {
                Log($"Target locked: 0x{selected.Number:X2} - {selected.FriendlyName}");
                EnableActionButtons();
            }
            else
            {
                DisableActionButtons();
            }
        }

        private void EnableActionButtons()
        {
            BtnProfile.IsEnabled = true;
            BtnClearRO.IsEnabled = true;
            BtnFormat.IsEnabled = true;
            BtnWipe.IsEnabled = true;
            BtnShowCmds.IsEnabled = true;
        }

        private void DisableActionButtons()
        {
            BtnProfile.IsEnabled = false;
            BtnClearRO.IsEnabled = false;
            BtnFormat.IsEnabled = false;
            BtnWipe.IsEnabled = false;
            BtnShowCmds.IsEnabled = false;
        }

        private DiskInfo GetSelectedDisk() => DisksDataGrid.SelectedItem as DiskInfo;

        private void BtnProfile_Click(object sender, RoutedEventArgs e)
        {
            var disk = GetSelectedDisk();
            if (disk != null) Log($"Neural Profile Dump for disk 0x{disk.Number:X2} (Simulated)");
        }

        private void BtnClearRO_Click(object sender, RoutedEventArgs e)
        {
            var disk = GetSelectedDisk();
            if (disk != null) Log($"Clearing Read-Only flag for disk 0x{disk.Number:X2}... (Simulated)");
        }

        private void BtnFormat_Click(object sender, RoutedEventArgs e)
        {
            var disk = GetSelectedDisk();
            if (disk != null) Log($"Formatting disk 0x{disk.Number:X2}... (Simulated)");
        }

        private void BtnWipe_Click(object sender, RoutedEventArgs e)
        {
            var disk = GetSelectedDisk();
            if (disk != null)
            {
                var result = MessageBox.Show($"Are you sure you want to completely WIPE disk {disk.Number} ({disk.FriendlyName})? ALL DATA WILL BE LOST.", "CRITICAL WARNING", MessageBoxButton.YesNo, MessageBoxImage.Error);
                if (result == MessageBoxResult.Yes)
                {
                    Log($"FULL WIPE INITIATED for disk 0x{disk.Number:X2}... (Simulated)");
                }
            }
        }

        private void BtnShowCmds_Click(object sender, RoutedEventArgs e)
        {
            var disk = GetSelectedDisk();
            if (disk != null)
            {
                Log($"Equivalent diskpart commands for wipe:");
                Log($"  select disk {disk.Number}");
                Log($"  clean");
                Log($"  convert gpt");
                Log($"  create partition primary");
                Log($"  format fs=exfat quick");
            }
        }

        private List<DiskInfo> GetDisks(bool removableOnly)
        {
            var psScript = @"
                $disks = Get-Disk | Select-Object Number, FriendlyName, SerialNumber, Size, 
                    BusType, PartitionStyle, OperationalStatus, IsOffline, IsReadOnly, 
                    IsBoot, IsSystem

                $physical = Get-PhysicalDisk | Select-Object DeviceId, MediaType, BusType

                $result = @()
                foreach ($d in $disks) {
                    $phys = $physical | Where-Object { $_.DeviceId -eq $d.Number.ToString() } | Select-Object -First 1
                    $isRemovable = ($d.BusType -in @('USB','SD','MMC')) -or 
                                   ($phys -and $phys.MediaType -match 'Removable|Unspecified') -or
                                   ($d.FriendlyName -match '(?i)USB|Removable|External|Pendrive|Flash')
                    
                    $obj = [PSCustomObject]@{
                        Number          = $d.Number
                        FriendlyName    = $d.FriendlyName
                        Size            = [math]::Round($d.Size / 1GB, 2)
                        BusType         = $d.BusType
                        PartitionStyle  = $d.PartitionStyle
                        Status          = $d.OperationalStatus
                        IsReadOnly      = $d.IsReadOnly
                        IsRemovable     = $isRemovable
                    }
                    $result += $obj
                }
                $result | ConvertTo-Json -Depth 3
            ";

            var output = RunPowerShell(psScript);
            if (string.IsNullOrWhiteSpace(output)) return new List<DiskInfo>();

            try
            {
                var parsed = JsonSerializer.Deserialize<List<DiskInfo>>(output, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                if (parsed == null) return new List<DiskInfo>();
                return removableOnly ? parsed.Where(d => d.IsRemovable && d.Number != 0).ToList() : parsed;
            }
            catch
            {
                return new List<DiskInfo>();
            }
        }

        private string RunPowerShell(string script)
        {
            var psi = new ProcessStartInfo("powershell.exe", $"-NoProfile -ExecutionPolicy Bypass -Command \"{script}\"")
            {
                RedirectStandardOutput = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            return process?.StandardOutput.ReadToEnd() ?? "";
        }
    }

    public class DiskInfo
    {
        public int Number { get; set; }
        public string NumberStr => $"0x{Number:X2}";
        public string FriendlyName { get; set; }
        public double Size { get; set; }
        public string BusType { get; set; }
        public string PartitionStyle { get; set; }
        public bool IsRemovable { get; set; }
        public string IsRemovableStr => IsRemovable ? "YES" : "NO";
        public bool IsReadOnly { get; set; }
        public string IsReadOnlyStr => IsReadOnly ? "YES" : "NO";
        public string Status { get; set; }
    }
}
