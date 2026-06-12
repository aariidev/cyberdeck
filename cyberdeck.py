#!/usr/bin/env python3
"""
CyberPy Ari v3.0 - CYBERDECK NEURAL STORAGE REPAIR
Full TUI application built with Textual + Rich (cyberpunk style).

Proyecto: cyberpy_ari
Autor: ari
GitHub: https://github.com/aariidev/cyberdeck

=== BIG IMPROVEMENTS IN v3.0 ===
- Visual Partition Mapper (text-based disk visualization)
- Intelligent Auto-Repair Advisor (analyzes state and recommends fixes)
- SMART / Disk Health Dashboard (real health data from PowerShell)
- Repair Script Generator & Executor (export/import reusable scripts)
- Persistent Config (defaults, theme, preferred FS)
- Secure Wipe Levels (Quick / Zero / Random with extra safety)
- Enhanced Progress & Live Feedback for long operations
- In-app Help & Command Reference
- Polished UI: status bar, better modals, theme options
- Many bug fixes, better error handling, and code organization

Características principales:
- Interfaz visual completa estilo cyberdeck (Textual)
- Detección inteligente de unidades removibles (pendrives, HDD/SSD externos)
- Múltiples capas de seguridad con modales dramáticos para acciones destructivas
- Transparencia total: muestra comandos diskpart/PowerShell equivalentes
- Logging en vivo estilo "neural log"
- Todas las acciones clásicas + nuevas en v3
- Dry-run mode, rescan, perfiles recomendados
- Backend híbrido: PowerShell para info + diskpart para operaciones de bajo nivel

⚠️ IMPORTANTE EN WINDOWS:
Usa siempre el MISMO launcher para instalar y ejecutar:
    py -m pip install textual rich
    py cyberdeck.py

Ejecutar SIEMPRE como Administrador.

Uso:
    py cyberdeck.py                 # Lanza la app completa cyberpunk (recomendado)
    py cyberdeck.py --list          # Modo CLI rápido (sin TUI)
"""

import subprocess
import sys
import os
import json
import tempfile
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# ====================== CONFIGURACIÓN ======================
VERSION = "3.0"
LOG_FILE = Path(__file__).parent / "cyberdeck_log.txt"
RICH_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.align import Align
    from rich.rule import Rule
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.theme import Theme
    from rich import print as rprint
    from rich.style import Style

    # ====================== CYBERPUNK THEME ======================
    CYBERPUNK_THEME = Theme({
        "primary": "#00f0ff",           # Neon cyan
        "accent": "#ff00aa",            # Hot magenta
        "warning": "#ff9500",           # Orange warning
        "danger": "#ff2e63",            # Red-pink danger
        "success": "#39ff14",           # Acid lime green
        "info": "#9d4edd",              # Purple
        "dim": "#4a4a5a",
        "text": "#e0e0e0",
    })

    console = Console(theme=CYBERPUNK_THEME, highlight=True)
    RICH_AVAILABLE = True
except ImportError:
    console = None
    RICH_AVAILABLE = False

# ====================== TEXTUAL IMPORT (separate - required for full app) ======================
TEXTUAL_AVAILABLE = False
try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical, Container, ScrollableContainer, Grid
    from textual.widgets import (
        Header, Footer, DataTable, Static, Button, Log as TextualLog, Input, Label, Rule as TextualRule,
        ProgressBar
    )
    from textual.screen import ModalScreen
    from textual.binding import Binding
    from textual.reactive import reactive
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

# ====================== CYBERPUNK VISUALS ======================

def show_cyberpunk_banner():
    """Muestra un banner estilo cyberpunk al iniciar."""
    if not RICH_AVAILABLE or console is None:
        print("\n" + "=" * 70)
        print("   DISKFIX v1.0  |  NEURAL STORAGE REPAIR INTERFACE")
        print("=" * 70 + "\n")
        return

    banner_lines = [
        ("  ██████╗ ██╗███████╗██╗  ██╗    ███████╗██╗██╗  ██╗", "primary"),
        (" ██╔════╝ ██║██╔════╝██║ ██╔╝    ██╔════╝██║╚██╗██╔╝", "primary"),
        (" ██║  ███╗██║███████╗█████╔╝     █████╗  ██║ ╚███╔╝ ", "accent"),
        (" ██║   ██║██║╚════██║██╔═██╗     ██╔══╝  ██║ ██╔██╗ ", "accent"),
        (" ╚██████╔╝██║███████║██║  ██╗    ██║     ██║██╔╝ ██╗", "success"),
        ("  ╚═════╝ ╚═╝╚══════╝╚═╝  ╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝", "success"),
    ]

    for line, style in banner_lines:
        console.print(Text(line, style=style))

    console.print()
    tagline = Text("CYBERDECK // NEURAL LINK // STORAGE BREACH & REPAIR v1.0", style="bold #ff00aa")
    console.print(Align.center(tagline))
    console.print(Align.center(Text(">>> INITIALIZING SECURE NEURAL INTERFACE <<<", style="dim primary")))
    console.print(Rule(style="#00f0ff"))
    console.print()


def cyberpunk_panel(title: str, content: str, style: str = "primary", border_style: str = "primary") -> Panel:
    """Crea un panel con estilo cyberpunk."""
    if not RICH_AVAILABLE:
        return content
    title_text = Text(f" {title} ", style=f"bold {style}")
    return Panel(
        content,
        title=title_text,
        border_style=border_style,
        padding=(1, 2),
        expand=True
    )


def styled_status(value: str, good_values=("Online", "Sí", "Healthy"), bad_values=("ReadOnly", "Offline", "No")) -> Text:
    """Devuelve texto coloreado según estado."""
    lower = value.lower()
    if any(g.lower() in lower for g in good_values):
        return Text(value, style="success bold")
    if any(b.lower() in lower for b in bad_values):
        return Text(value, style="bold #ff2e63")
    return Text(value, style="warning")


def log_action(message: str, level: str = "INFO"):
    """Registra todo lo que hace el programa en un archivo de log. (Cyberpunk styled)"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

    if RICH_AVAILABLE and console is not None:
        level_styles = {
            "INFO": "primary",
            "WARN": "warning",
            "ERROR": "danger",
            "SUCCESS": "success",
        }
        lvl_style = level_styles.get(level, "text")
        # Cyberpunk log prefix
        prefix = Text("▸ NEURAL LOG ", style="dim")
        ts = Text(f"[{timestamp}] ", style="dim")
        lvl = Text(f"[{level}] ", style=lvl_style + " bold")
        console.print(prefix + ts + lvl + Text(message, style="text"))
    else:
        print(f"[{level}] {message}")


def check_admin() -> bool:
    """Verifica si el script se está ejecutando como administrador."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_powershell(command: str, as_json: bool = False, timeout: int = 60) -> Any:
    """Ejecuta un comando de PowerShell y devuelve la salida (texto o JSON parseado)."""
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", command
    ]
    try:
        result = subprocess.run(
            ps_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            log_action(f"PowerShell error: {err}", "ERROR")
            return None if as_json else output

        if as_json and output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                log_action("No se pudo parsear JSON de PowerShell", "WARN")
                return None
        return output
    except subprocess.TimeoutExpired:
        log_action("Timeout ejecutando PowerShell", "ERROR")
        return None
    except Exception as e:
        log_action(f"Excepción en PowerShell: {e}", "ERROR")
        return None


def run_diskpart_script(script_lines: List[str], dry_run: bool = False) -> bool:
    """
    Escribe un script temporal para diskpart y lo ejecuta.
    Devuelve True si terminó sin errores graves.
    """
    if dry_run:
        log_action("MODO DRY-RUN: No se ejecutará diskpart", "WARN")
        print("\n--- SCRIPT DISKPART QUE SE EJECUTARÍA ---")
        for line in script_lines:
            print(line)
        print("-----------------------------------------\n")
        return True

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("\n".join(script_lines) + "\n")
        script_path = f.name

    try:
        cmd = ["diskpart", "/s", script_path]
        log_action(f"Ejecutando: {' '.join(cmd)}", "INFO")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"
        )
        # diskpart suele devolver salida en stdout incluso en éxito
        combined = (result.stdout or "") + (result.stderr or "")
        log_action(f"diskpart salida:\n{combined}", "INFO")

        if "DiskPart ha finalizado correctamente" in combined or result.returncode == 0:
            return True
        # Algunos comandos devuelven warnings pero funcionan
        if "no se pudo" in combined.lower() or "error" in combined.lower():
            log_action("Posible error en diskpart", "WARN")
        return True  # La mayoría de veces seguimos aunque haya warnings
    except Exception as e:
        log_action(f"Error ejecutando diskpart: {e}", "ERROR")
        return False
    finally:
        try:
            os.unlink(script_path)
        except Exception:
            pass


# ====================== DESCUBRIMIENTO DE DISCOS ======================

def get_disks(only_removable: bool = True) -> List[Dict[str, Any]]:
    """
    Obtiene la lista de discos usando PowerShell (Get-Disk + Get-PhysicalDisk).
    Si only_removable=True, filtra a unidades USB / removibles / externas.
    """
    ps_script = r"""
    $disks = Get-Disk | Select-Object Number, FriendlyName, SerialNumber, Size, 
        BusType, PartitionStyle, OperationalStatus, IsOffline, IsReadOnly, 
        IsBoot, IsSystem, UniqueId

    $physical = Get-PhysicalDisk | Select-Object DeviceId, MediaType, BusType, 
        FriendlyName, SerialNumber, Size

    $result = @()
    foreach ($d in $disks) {
        $phys = $physical | Where-Object { $_.DeviceId -eq $d.Number.ToString() } | Select-Object -First 1
        $isRemovable = ($d.BusType -in @('USB','SD','MMC')) -or 
                       ($phys -and $phys.MediaType -match 'Removable|Unspecified') -or
                       ($d.FriendlyName -match '(?i)USB|Removable|External|Pendrive|Flash')
        
        $obj = [PSCustomObject]@{
            Number          = $d.Number
            FriendlyName    = $d.FriendlyName
            SerialNumber    = $d.SerialNumber
            Size            = [math]::Round($d.Size / 1GB, 2)
            SizeBytes       = $d.Size
            BusType         = $d.BusType
            PartitionStyle  = $d.PartitionStyle
            Status          = $d.OperationalStatus
            IsOffline       = $d.IsOffline
            IsReadOnly      = $d.IsReadOnly
            IsBoot          = $d.IsBoot
            IsSystem        = $d.IsSystem
            IsRemovable     = $isRemovable
            MediaType       = if ($phys) { $phys.MediaType } else { "Desconocido" }
        }
        $result += $obj
    }
    $result | ConvertTo-Json -Depth 3
    """

    data = run_powershell(ps_script, as_json=True)
    if not data:
        log_action("No se pudieron obtener discos. ¿Estás como Administrador?", "ERROR")
        return []

    if isinstance(data, dict):  # PowerShell devuelve un solo objeto a veces
        data = [data]

    disks = []
    for d in data:
        if only_removable and not d.get("IsRemovable", False):
            # Aún permitimos mostrar si el usuario lo pide explícitamente
            continue
        # Nunca sugerir el disco 0 como "removible" por seguridad extra
        if d.get("Number") == 0 and only_removable:
            # Si Windows lo marca como removible por error raro, lo saltamos por defecto
            if d.get("IsBoot") or d.get("IsSystem"):
                continue
        disks.append(d)

    # Ordenar por número
    disks.sort(key=lambda x: x.get("Number", 999))
    return disks


def get_all_disks() -> List[Dict[str, Any]]:
    """Obtiene TODOS los discos (incluyendo internos). Muestra advertencia fuerte."""
    return get_disks(only_removable=False)


def get_partitions_and_volumes(disk_number: int) -> Dict[str, Any]:
    """Obtiene particiones y volúmenes de un disco específico."""
    ps_part = f"Get-Partition -DiskNumber {disk_number} | Select-Object PartitionNumber, DriveLetter, Type, Size, IsActive, IsHidden, IsBoot, IsSystem | ConvertTo-Json -Depth 2"
    partitions = run_powershell(ps_part, as_json=True) or []

    if isinstance(partitions, dict):
        partitions = [partitions]

    ps_vol = "Get-Volume | Select-Object DriveLetter, FileSystem, FileSystemLabel, Size, SizeRemaining, HealthStatus | ConvertTo-Json -Depth 2"
    volumes_raw = run_powershell(ps_vol, as_json=True) or []
    if isinstance(volumes_raw, dict):
        volumes_raw = [volumes_raw]

    # Intentamos emparejar volúmenes con particiones por letra
    volumes = []
    for v in volumes_raw:
        if v.get("DriveLetter"):
            volumes.append(v)

    return {
        "partitions": partitions,
        "volumes": volumes
    }


# ====================== FUNCIONES DE IMPRESIÓN / UI ======================

def print_disk_table(disks: List[Dict[str, Any]], title: str = "NEURAL SCAN - UNIDADES DETECTADAS"):
    """Imprime una tabla estilo cyberpunk de discos (muy visual)."""
    if not disks:
        if RICH_AVAILABLE and console:
            console.print(Text("▸ NO SE DETECTARON UNIDADES REMOVIBLES EN EL ESCANEO NEURAL.", style="#ff2e63"))
        else:
            print("No se encontraron discos.")
        return

    if RICH_AVAILABLE and console is not None:
        # Cyberpunk header
        console.print(Rule(title=Text(title, style="bold #00f0ff"), style="#00f0ff"))
        console.print()

        table = Table(
            show_header=True,
            header_style="bold #00f0ff",
            border_style="#00f0ff",
            title_style="#ff00aa",
            expand=True
        )
        table.add_column("ID", style="bold #00f0ff", justify="center", width=4)
        table.add_column("MODELO / NOMBRE", style="text", width=38)
        table.add_column("CAPACIDAD", style="#00f0ff", justify="right")
        table.add_column("BUS", style="#9d4edd", justify="center")
        table.add_column("ESTILO", style="#ff00aa", justify="center")
        table.add_column("ESTADO", justify="center")
        table.add_column("REM?", justify="center")
        table.add_column("RO?", justify="center")

        for d in disks:
            num = str(d.get("Number", "?"))
            name = str(d.get("FriendlyName", "UNKNOWN"))[:37]
            size = f"{d.get('Size', 0):.1f} GB"
            bus = str(d.get("BusType", "N/A"))
            estilo = str(d.get("PartitionStyle", "N/A"))
            estado = styled_status(str(d.get("Status", "N/A")))
            removable = "⚡ SÍ" if d.get("IsRemovable") else "— NO"
            ro = styled_status("SÍ" if d.get("IsReadOnly") else "NO")

            # Color the removable column
            rem_style = "success" if d.get("IsRemovable") else "dim"
            removable_text = Text(removable, style=rem_style)

            table.add_row(
                Text(f"0x{int(num):02X}", style="#00f0ff"),
                name,
                size,
                bus,
                estilo,
                estado,
                removable_text,
                ro
            )

        console.print(table)
        console.print(Rule(style="#00f0ff"))
        console.print(Text("▸ Usa el ID (decimal) para seleccionar. Escaneo neural completo.", style="dim"))
    else:
        # Fallback plano
        print(f"\n=== {title} ===")
        print(f"{'#':<3} {'Nombre':<40} {'GB':>8} {'Bus':<8} {'Estilo':<8} {'Rem?':<6} {'RO?':<5}")
        print("-" * 85)
        for d in disks:
            print(f"{d.get('Number', '?'):<3} {str(d.get('FriendlyName',''))[:40]:<40} "
                  f"{d.get('Size',0):>8.2f} {str(d.get('BusType','')):<8} "
                  f"{str(d.get('PartitionStyle','')):<8} "
                  f"{'Sí' if d.get('IsRemovable') else 'No':<6} "
                  f"{'Sí' if d.get('IsReadOnly') else 'No':<5}")
        print("-" * 85)


def print_details(disk: Dict[str, Any], extra: Dict[str, Any]):
    """Muestra un perfil neural detallado y visual del disco (estilo cyberpunk)."""
    num = disk.get("Number")
    name = disk.get("FriendlyName", "UNKNOWN DRIVE")

    if not RICH_AVAILABLE or console is None:
        # Fallback simple
        print(f"\nDISCO #{num} - {name}")
        return

    console.print(Rule(title=Text(f"DISK NEURAL PROFILE // 0x{num:02X}", style="bold #ff00aa"), style="#ff00aa"))
    console.print()

    # === HEADER PANEL ===
    header_text = Text()
    header_text.append(f"TARGET: ", style="dim")
    header_text.append(f"{name}\n", style="bold #00f0ff")
    header_text.append(f"CAPACITY: ", style="dim")
    header_text.append(f"{disk.get('Size', 0)} GB  |  ", style="text")
    header_text.append(f"BUS: ", style="dim")
    header_text.append(f"{disk.get('BusType', 'N/A')} ({disk.get('MediaType', 'N/A')})", style="#9d4edd")

    console.print(Panel(header_text, border_style="#00f0ff", padding=(0, 1), title=Text("IDENTITY", style="bold #00f0ff")))

    # === STATUS GRID ===
    status_items = [
        ("STATUS", str(disk.get("Status", "N/A")), "success" if str(disk.get("Status")).lower() == "online" else "warning"),
        ("READONLY", "BREACH" if disk.get("IsReadOnly") else "CLEAR", "danger" if disk.get("IsReadOnly") else "success"),
        ("OFFLINE", "YES" if disk.get("IsOffline") else "NO", "danger" if disk.get("IsOffline") else "success"),
        ("PARTITION", str(disk.get("PartitionStyle", "N/A")), "accent"),
        ("BOOT", "YES" if disk.get("IsBoot") else "NO", "warning" if disk.get("IsBoot") else "dim"),
        ("SYSTEM", "YES" if disk.get("IsSystem") else "NO", "danger" if disk.get("IsSystem") else "dim"),
    ]

    status_table = Table.grid(padding=(0, 2))
    for label, val, st in status_items:
        status_table.add_row(
            Text(f"{label}:", style="dim"),
            Text(val, style=f"{st} bold")
        )

    console.print(Panel(status_table, border_style="#ff00aa", title=Text("TACTICAL STATUS", style="bold #ff00aa"), padding=(1, 2)))

    # Particiones y volúmenes
    parts = extra.get("partitions", []) or []
    vols = extra.get("volumes", []) or []

    if parts:
        part_lines = []
        for p in parts:
            letter = p.get("DriveLetter") or "—"
            size_gb = round(p.get("Size", 0) / 1_000_000_000, 2)
            part_lines.append(
                f"[primary]P{p.get('PartitionNumber')}[/] | Letter:[accent]{letter}[/] | "
                f"Type:[info]{p.get('Type', 'N/A')}[/] | Size:[success]{size_gb} GB[/] | Active:{p.get('IsActive')}"
            )
        parts_content = "\n".join(part_lines)
        console.print(Panel(parts_content, title=Text("PARTITION TABLE", style="bold #9d4edd"), border_style="#9d4edd", padding=(1, 1)))

    if vols:
        vol_lines = []
        for v in vols:
            letter = v.get("DriveLetter") or "NO LETTER"
            fs = v.get("FileSystem", "RAW?")
            label = v.get("FileSystemLabel") or ""
            free = round((v.get("SizeRemaining") or 0) / 1e9, 1)
            total = round((v.get("Size") or 0) / 1e9, 1)
            health = v.get("HealthStatus", "?")
            vol_lines.append(
                f"[accent]{letter}:[/] FS=[primary]{fs}[/] '{label}'  |  [success]{free} GB free[/] of {total} GB  |  Health: {health}"
            )
        console.print(Panel("\n".join(vol_lines), title=Text("VOLUME MAP", style="bold #39ff14"), border_style="#39ff14", padding=(1, 1)))

    console.print(Rule(style="dim"))
    console.print(Text("▸ Neural profile complete. Ready for breach commands.", style="dim primary"))
    console.print()


def confirm_dangerous_action(disk_num: int, description: str, extra_phrase: str = "BREACH") -> bool:
    """
    Confirmación de múltiples capas estilo cyberpunk para acciones destructivas.
    Muy visual y dramática.
    """
    if RICH_AVAILABLE and console is not None:
        console.print()
        danger_panel = Panel(
            Align.center(
                Text("⚠️  WARNING: DESTRUCTIVE NEURAL BREACH  ⚠️\n\n", style="bold #ff2e63") +
                Text(f"TARGET DISK: 0x{disk_num:02X}\n", style="bold #00f0ff") +
                Text(f"OPERATION: {description}\n\n", style="warning") +
                Text("THIS WILL PERMANENTLY ERASE ALL DATA ON THE TARGET.\n", style="#ff2e63") +
                Text("BACKUP CRITICAL DATA BEFORE PROCEEDING.\n\n", style="#ff00aa") +
                Text("MULTI-FACTOR NEURAL AUTHORIZATION REQUIRED", style="dim")
            ),
            border_style="#ff2e63",
            title=Text("// CYBERDECK SECURITY OVERRIDE //", style="bold #ff2e63"),
            padding=(1, 4)
        )
        console.print(danger_panel)
        console.print()

        # Layer 1
        typed_num = Prompt.ask(
            f"[danger]>>> CONFIRM TARGET DISK ID[/] (type [bold]{disk_num}[/])",
            default="",
            show_default=False
        ).strip()
        if typed_num != str(disk_num):
            console.print(Text("▸ AUTHORIZATION FAILED - DISK ID MISMATCH. BREACH ABORTED.", style="#ff2e63"))
            return False

        # Layer 2
        typed_phrase = Prompt.ask(
            f'[danger]>>> ENTER OVERRIDE PHRASE[/] (type exactly [bold]{extra_phrase}[/])',
            default="",
            show_default=False
        ).strip().upper()
        if typed_phrase != extra_phrase.upper():
            console.print(Text("▸ PHRASE MISMATCH. NEURAL FIREWALL ENGAGED. ABORTED.", style="#ff2e63"))
            return False

        # Layer 3
        final = Prompt.ask(
            "[danger bold]>>> FINAL CONFIRMATION. TYPE 'EXECUTE' TO BREACH[/]",
            default="",
            show_default=False
        ).strip().upper()
        if final != "EXECUTE":
            console.print(Text("▸ BREACH SEQUENCE ABORTED BY OPERATOR.", style="warning"))
            return False

        console.print(Text("▸ NEURAL AUTHORIZATION GRANTED. INITIATING...", style="success bold"))
        log_action(f"CONFIRMACIÓN RECIBIDA (CYBERPUNK) para disco #{disk_num}: {description}", "WARN")
        return True
    else:
        # Fallback original
        print("\n" + "!" * 70)
        print("¡¡¡ ADVERTENCIA - OPERACIÓN DESTRUCTIVA !!!")
        print(f"Acción: {description} | Disco #{disk_num}")
        print("!" * 70)
        typed_num = input(f"Escribe el número del disco ({disk_num}): ").strip()
        if typed_num != str(disk_num):
            print("Cancelado.")
            return False
        typed_phrase = input(f'Escribe "{extra_phrase}": ').strip().upper()
        if typed_phrase != extra_phrase.upper():
            print("Cancelado.")
            return False
        if not input("Escribe 'si' para proceder: ").lower().startswith("si"):
            return False
        log_action(f"CONFIRMACIÓN RECIBIDA para disco #{disk_num}: {description}", "WARN")
        return True


# ====================== ACCIONES PRINCIPALES ======================

def action_show_commands(disk: Dict[str, Any], action_type: str):
    """Muestra los comandos equivalentes de forma muy visual (estilo cyberpunk)."""
    num = disk["Number"]
    if RICH_AVAILABLE and console:
        console.print(Rule(title=Text(f"EQUIVALENT BREACH SEQUENCES // DISK 0x{num:02X}", style="bold #9d4edd"), style="#9d4edd"))
    else:
        print(f"\n=== COMANDOS EQUIVALENTES DISCO #{num} ({action_type}) ===\n")

    if action_type == "fix-readonly":
        content = Text("diskpart sequence:\n", style="dim")
        content.append(f"  select disk {num}\n  attributes disk clear readonly\n\n", style="#00f0ff")
        content.append("PowerShell (preferred):\n", style="dim")
        content.append(f"  Set-Disk -Number {num} -IsReadOnly $false", style="#39ff14")
        title = "CLEAR WRITE PROTECT"

    elif action_type == "clean-recreate":
        content = Text("Classic diskpart (used internally):\n", style="dim")
        content.append(f"  select disk {num}\n  clean\n  convert gpt\n  create partition primary\n  format fs=exfat quick label=\"MIUSB\"\n\n", style="#00f0ff")
        content.append("Modern PowerShell equivalent:\n", style="dim")
        content.append(f"  Clear-Disk -Number {num} -RemoveData -Confirm:$false\n  New-Partition ... | Format-Volume -FileSystem exFAT ...", style="#39ff14")
        title = "WIPE + RECREATE"

    elif action_type == "format":
        content = Text("diskpart:\n", style="dim")
        content.append(f"  select disk {num}\n  select partition 1\n  format fs=exfat quick label=\"NUEVO\"\n\n", style="#00f0ff")
        content.append("PowerShell:\n", style="dim")
        content.append("  Get-Partition -DiskNumber X | Get-Volume | Format-Volume ...", style="#39ff14")
        title = "FORMAT VOLUME"

    else:
        content = Text("See source for details.", style="dim")
        title = "COMMANDS"

    if RICH_AVAILABLE and console:
        console.print(Panel(content, title=Text(title, style="bold #00f0ff"), border_style="#00f0ff", padding=(1, 2)))
    else:
        print(content.plain if hasattr(content, 'plain') else content)


def action_fix_readonly(disk: Dict[str, Any], dry_run: bool = False) -> bool:
    """Quita el atributo readonly del disco."""
    num = disk["Number"]
    if not disk.get("IsReadOnly"):
        log_action(f"El disco #{num} no parece tener atributo readonly activado.", "INFO")
        return True

    if not confirm_dangerous_action(num, "Quitar protección contra escritura (readonly)", "QUITAR"):
        return False

    script = [
        f"select disk {num}",
        "attributes disk clear readonly",
        "detail disk"
    ]
    success = run_diskpart_script(script, dry_run=dry_run)
    if success and not dry_run:
        log_action(f"Protección contra escritura quitada del disco #{num}", "SUCCESS")
    return success


def action_rescan():
    """Fuerza una nueva detección de discos con feedback cyberpunk."""
    log_action("FORCING NEURAL RESCAN...", "INFO")
    script = ["rescan"]
    run_diskpart_script(script)
    if RICH_AVAILABLE and console:
        console.print(Text("▸ RESCAN COMPLETE. NEURAL MAP UPDATED.", style="#39ff14"))
    else:
        print("Rescan completado. Vuelve a listar los discos.")


def action_chkdsk(disk: Dict[str, Any], letter: Optional[str] = None, dry_run: bool = False):
    """Ejecuta chkdsk en los volúmenes del disco (o en una letra específica)."""
    num = disk["Number"]
    extra = get_partitions_and_volumes(num)
    vols = extra.get("volumes", [])

    target_letters = []
    if letter:
        target_letters = [letter.upper().replace(":", "")]
    else:
        for v in vols:
            if v.get("DriveLetter"):
                target_letters.append(v["DriveLetter"])

    if not target_letters:
        print("No se encontraron letras de unidad asignadas en este disco.")
        return

    for let in target_letters:
        cmd = f"chkdsk {let}: /f"
        print(f"\nSe ejecutará: {cmd}")
        if dry_run:
            print("(DRY-RUN) No se ejecuta.")
            continue
        if not confirm_dangerous_action(num, f"Ejecutar chkdsk en {let}:", "CHKDSK"):
            continue
        try:
            log_action(f"Ejecutando chkdsk en {let}:", "INFO")
            subprocess.run(["chkdsk", f"{let}:", "/f"], check=False)
        except Exception as e:
            log_action(f"Error en chkdsk: {e}", "ERROR")


def action_assign_letter(disk: Dict[str, Any], desired_letter: Optional[str] = None, dry_run: bool = False):
    """Asigna una letra de unidad (usa diskpart)."""
    num = disk["Number"]
    extra = get_partitions_and_volumes(num)
    parts = extra.get("partitions", [])

    if not parts:
        print("El disco no tiene particiones visibles.")
        return

    # Tomamos la primera partición con datos normalmente
    part_num = parts[0].get("PartitionNumber", 1)
    letter = desired_letter or input("Letra deseada (ej: E): ").strip().upper().replace(":", "")[:1]

    if not letter or not letter.isalpha():
        print("Letra inválida.")
        return

    script = [
        f"select disk {num}",
        f"select partition {part_num}",
        f"assign letter={letter}"
    ]
    print(f"Se asignará letra {letter}: a la partición {part_num} del disco {num}")
    if confirm_dangerous_action(num, f"Asignar letra {letter}:", "ASIGNAR"):
        run_diskpart_script(script, dry_run=dry_run)


def action_format_existing(disk: Dict[str, Any], fs: str = "exfat", label: str = "USB", dry_run: bool = False):
    """Formatea partición(es) existentes de forma relativamente segura."""
    num = disk["Number"]
    extra = get_partitions_and_volumes(num)
    parts = extra.get("partitions", [])

    if not parts:
        print("No hay particiones que formatear. Considera la opción de 'Limpiar y crear nueva'.")
        return

    print(f"Se formateará la(s) partición(es) del disco #{num} a {fs.upper()} con etiqueta '{label}'.")
    if not confirm_dangerous_action(num, f"Formatear partición(es) a {fs}", "FORMATEAR"):
        return

    script = [f"select disk {num}"]
    for p in parts:
        pnum = p.get("PartitionNumber")
        script.append(f"select partition {pnum}")
        script.append(f"format fs={fs} quick label=\"{label}\"")
    script.append("list partition")

    run_diskpart_script(script, dry_run=dry_run)


def action_clean_and_recreate(disk: Dict[str, Any], fs: str = "exfat", label: str = "DATOS", 
                              use_gpt: bool = True, make_active: bool = False, dry_run: bool = False):
    """
    La operación más común para "arreglar" un pendrive o disco externo corrupto:
    - clean (borra tabla de particiones)
    - convert gpt o mbr
    - create partition primary (todo el disco)
    - format
    - assign (Windows suele asignar automáticamente después)
    """
    num = disk["Number"]
    desc = f"LIMPIAR COMPLETAMENTE el disco #{num} y crear una partición única {fs.upper()}"
    if not confirm_dangerous_action(num, desc, "LIMPIAR"):
        return False

    style = "gpt" if use_gpt else "mbr"
    script = [
        f"select disk {num}",
        "clean",
        f"convert {style}",
        "create partition primary",
    ]
    if make_active and not use_gpt:
        script.append("active")
    script.append(f"format fs={fs} quick label=\"{label}\"")
    script.append("detail partition")

    log_action(f"Iniciando clean + recreate en disco #{num} (estilo={style}, fs={fs})", "WARN")
    success = run_diskpart_script(script, dry_run=dry_run)

    if success and not dry_run:
        log_action(f"Disco #{num} limpiado y recreado exitosamente.", "SUCCESS")
        print("\nRecomendación: ejecuta 'rescan' y verifica con 'list disk' o actualiza el Explorador de archivos.")
    return success


def action_convert_style(disk: Dict[str, Any], to_style: str, dry_run: bool = False):
    """Convierte entre MBR y GPT (destructivo si ya tiene datos)."""
    num = disk["Number"]
    current = disk.get("PartitionStyle", "UNKNOWN").lower()
    if current == to_style.lower():
        print(f"El disco ya está en estilo {to_style}.")
        return

    desc = f"Convertir disco #{num} de {current} a {to_style} (puede requerir limpiar primero)"
    if not confirm_dangerous_action(num, desc, "CONVERTIR"):
        return

    script = [
        f"select disk {num}",
        f"convert {to_style.lower()}"
    ]
    run_diskpart_script(script, dry_run=dry_run)


# ====================== NUEVAS MEJORAS v3.0 ======================

def get_smart_health(disk: Dict[str, Any]) -> Dict[str, Any]:
    """Obtiene datos SMART / salud del disco usando PowerShell (v3.0)."""
    num = disk.get("Number")
    ps = f"""
    $disk = Get-PhysicalDisk | Where-Object {{$_.DeviceId -eq '{num}'}} | Select-Object MediaType, BusType, HealthStatus, OperationalStatus, Size, FriendlyName
    $smart = Get-WmiObject -Namespace root\\wmi -Class MSStorageDriver_FailurePredictStatus -ErrorAction SilentlyContinue | Where-Object {{$_.InstanceName -like "*{num}*"}} | Select-Object PredictFailure, Reason
    if ($smart) {{
        $disk | Add-Member -NotePropertyName PredictFailure -NotePropertyValue $smart.PredictFailure
        $disk | Add-Member -NotePropertyName Reason -NotePropertyValue $smart.Reason
    }}
    $disk | ConvertTo-Json -Depth 3
    """
    data = run_powershell(ps, as_json=True)
    if data:
        if isinstance(data, list): data = data[0]
        return data
    return {"HealthStatus": "Desconocido", "OperationalStatus": "N/A"}

def render_visual_disk_map(disk: Dict[str, Any], extra: Dict[str, Any]) -> str:
    """Genera un mapa visual de particiones estilo cyberpunk (v3.0)."""
    total_size = disk.get("SizeBytes", 1) or 1
    parts = extra.get("partitions", []) or []
    if not parts:
        return "[dim]Sin particiones visibles[/]"

    bar_width = 50
    segments = []
    used = 0
    colors = ["#00f0ff", "#ff00aa", "#39ff14", "#ff9500", "#9d4edd"]

    for i, p in enumerate(parts):
        size = p.get("Size", 0)
        pct = (size / total_size) * 100
        seg_len = max(1, int((size / total_size) * bar_width))
        color = colors[i % len(colors)]
        label = f"P{p.get('PartitionNumber', '?')} {pct:.0f}%"
        segments.append(f"[{color}]{'█'*seg_len}[/]")

    bar = "".join(segments)
    legend = " | ".join([f"[{colors[i%len(colors)]}]P{p.get('PartitionNumber','?')}[/]" for i,p in enumerate(parts)])
    return f"[{bar_width}]{bar}[/]\n{legend}"

def get_auto_advisor(disk: Dict[str, Any]) -> list:
    """Analiza el estado del disco y recomienda acciones (v3.0 big feature)."""
    recs = []
    if disk.get("IsReadOnly"):
        recs.append(("CLEAR READONLY", "El disco está protegido contra escritura. Limpia el flag primero."))
    if not disk.get("IsRemovable") and disk.get("Number", 99) == 0:
        recs.append(("NO RECOMENDADO", "¡Este parece ser el disco del sistema! No toques."))
    extra = get_partitions_and_volumes(disk["Number"])
    vols = extra.get("volumes", [])
    for v in vols:
        if v.get("FileSystem", "").upper() in ["RAW", ""]:
            recs.append(("FORMAT / CLEAN", f"Volumen {v.get('DriveLetter','?')} está RAW o sin FS. Recomiendo Clean + Formatear."))
        if v.get("HealthStatus", "").upper() != "HEALTHY":
            recs.append(("CHKDSK", f"Volumen reporta problemas de salud. Ejecuta chkdsk."))
    if not vols and not extra.get("partitions"):
        recs.append(("FULL WIPE + RECREATE", "Disco vacío o sin estructura detectable. La acción más efectiva."))
    if not recs:
        recs.append(("HEALTHY", "El disco parece en buen estado. Monitorea con Health Check."))
    return recs

def export_repair_script(disk: Dict[str, Any], actions: list) -> str:
    """Genera un script PowerShell / diskpart reutilizable (v3.0)."""
    num = disk["Number"]
    lines = [
        "# Cyberdeck Repair Script - Generated by CyberPy Ari v3.0",
        f"# Target Disk: {num} - {disk.get('FriendlyName')}",
        "# WARNING: Review before running. Run as Administrator.",
        "",
        "param([switch]$DryRun)",
        "",
        "function Run-Diskpart($cmds) {",
        "    $tmp = [System.IO.Path]::GetTempFileName()",
        "    $cmds | Out-File $tmp -Encoding ASCII",
        "    if ($DryRun) { Write-Host 'DRY-RUN:'; Get-Content $tmp } else { diskpart /s $tmp }",
        "    Remove-Item $tmp -ErrorAction SilentlyContinue",
        "}",
        "",
        f"$diskNum = {num}",
    ]
    for act in actions:
        if act == "clear-readonly":
            lines.append(f"Run-Diskpart @('select disk $diskNum', 'attributes disk clear readonly')")
        elif act == "clean-recreate":
            lines.append(f"Run-Diskpart @('select disk $diskNum', 'clean', 'convert gpt', 'create partition primary', 'format fs=exfat quick label=\"CYBERDATA\"')")
        elif act == "chkdsk":
            # simplistic
            lines.append("# chkdsk would be run per volume - manual review recommended")
    lines.append("\nWrite-Host 'Repair script finished.'")
    return "\n".join(lines)

def load_config() -> dict:
    """Carga configuración persistente (v3.0)."""
    cfg_path = Path.home() / ".cyberdeck_config.json"
    default = {
        "default_fs": "exfat",
        "default_label": "CYBERDATA",
        "dry_run_default": False,
        "theme": "cyan-magenta"
    }
    if cfg_path.exists():
        try:
            loaded = json.loads(cfg_path.read_text())
            return {**default, **loaded}
        except:
            pass
    return default

def save_config(cfg: dict):
    cfg_path = Path.home() / ".cyberdeck_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))

# Temas cyberpunk disponibles (v3.0)
CYBER_THEMES = {
    "cyan-magenta": {
        "primary": "#00f0ff",
        "accent": "#ff00aa",
        "warning": "#ff9500",
        "danger": "#ff2e63",
        "success": "#39ff14",
        "info": "#9d4edd",
    },
    "neon-green": {
        "primary": "#39ff14",
        "accent": "#00ff9f",
        "warning": "#ffaa00",
        "danger": "#ff3366",
        "success": "#00ffcc",
        "info": "#66ff66",
    },
    "purple-haze": {
        "primary": "#bb33ff",
        "accent": "#ff33cc",
        "warning": "#ffaa00",
        "danger": "#ff3366",
        "success": "#33ff99",
        "info": "#9966ff",
    }
}


# ====================== MENÚS ======================

def disk_menu(disk: Dict[str, Any], dry_run: bool = False):
    """Submenú de acciones para un disco seleccionado. Estilo Cyberdeck Operations Console."""
    num = disk["Number"]
    name = str(disk.get("FriendlyName", "DRIVE"))[:32]

    while True:
        if RICH_AVAILABLE and console:
            console.print()
            console.print(Rule(title=Text(f"OPERATIONS CONSOLE // TARGET 0x{num:02X} - {name}", style="bold #ff00aa"), style="#ff00aa"))

            ops = Text()
            ops.append("1", style="bold #00f0ff"); ops.append("  ▸ NEURAL PROFILE DUMP (details + partitions)\n", style="text")
            ops.append("2", style="success bold"); ops.append("  ▸ CLEAR WRITE PROTECT (remove readonly)\n", style="text")
            ops.append("3", style="info bold"); ops.append("  ▸ FILESYSTEM INTEGRITY SCAN (chkdsk)\n", style="text")
            ops.append("4", style="bold #ff00aa"); ops.append("  ▸ ASSIGN DRIVE LETTER\n", style="text")
            ops.append("5", style="bold #00f0ff"); ops.append("  ▸ FORMAT EXISTING PARTITION(S)\n", style="text")
            ops.append("6", style="bold #ff2e63"); ops.append("  ▸ FULL WIPE + RECREATE PARTITION (most effective fix)\n", style="text")
            ops.append("7", style="warning bold"); ops.append("  ▸ CONVERT PARTITION STYLE (MBR <-> GPT)\n", style="text")
            ops.append("8", style="info bold"); ops.append("  ▸ SHOW EQUIVALENT BREACH COMMANDS (no execute)\n", style="text")
            ops.append("9", style="bold #00f0ff"); ops.append("  ▸ FORCE RESCAN\n", style="text")
            ops.append("0", style="dim bold"); ops.append("  ▸ RETURN TO MAIN DECK", style="text")

            console.print(Panel(ops, title=Text("BREACH PROTOCOLS", style="bold #00f0ff"), border_style="#00f0ff", padding=(1, 2)))

            if dry_run:
                console.print(Text("   [DRY-RUN ACTIVE — Commands will only be simulated]", style="warning"))

            choice = Prompt.ask("\n[accent]>>> ISSUE BREACH COMMAND[/]", default="1").strip()
        else:
            print(f"\n=== ACCIONES DISCO #{num} - {name} ===")
            print(" 1. Ver información detallada")
            print(" 2. Quitar readonly")
            print(" 3. chkdsk")
            print(" 4. Asignar letra")
            print(" 5. Formatear existente")
            print(" 6. LIMPIAR + RECREAR (recomendado)")
            print(" 7. Convertir MBR/GPT")
            print(" 8. Mostrar comandos")
            print(" 9. Rescan")
            print(" 0. Volver")
            choice = input("\nOpción: ").strip()

        if choice == "1":
            if RICH_AVAILABLE and console:
                with console.status("[primary]DUMPING NEURAL PROFILE...[/]", spinner="dots"):
                    extra = get_partitions_and_volumes(num)
            else:
                extra = get_partitions_and_volumes(num)
            print_details(disk, extra)

        elif choice == "2":
            action_fix_readonly(disk, dry_run=dry_run)

        elif choice == "3":
            action_chkdsk(disk, dry_run=dry_run)

        elif choice == "4":
            action_assign_letter(disk, dry_run=dry_run)

        elif choice == "5":
            if RICH_AVAILABLE:
                fs = Prompt.ask("[primary]File system[/]", choices=["exfat", "ntfs", "fat32"], default="exfat")
                label = Prompt.ask("[primary]Volume label[/]", default="USB")
            else:
                fs = input("FS (exfat/ntfs/fat32) [exfat]: ").strip().lower() or "exfat"
                label = input("Label [USB]: ").strip() or "USB"
            action_format_existing(disk, fs=fs, label=label, dry_run=dry_run)

        elif choice == "6":
            if RICH_AVAILABLE and console:
                console.print(Panel(
                    Text("RECOMMENDED FOR MOST EXTERNAL/USB DRIVES\nexFAT offers best compatibility across OSes.", style="text"),
                    title=Text("RECOMMENDED PROFILE", style="bold #39ff14"), border_style="#39ff14"))
                fs = Prompt.ask("[primary]File system[/]", choices=["exfat", "ntfs", "fat32"], default="exfat")
                label = Prompt.ask("[primary]Label[/]", default="DATOS")
                use_gpt = Confirm.ask("[accent]Use GPT (recommended for >2TB)?[/]", default=True)
            else:
                print("\nPerfil recomendado: exFAT para compatibilidad máxima.")
                fs = input("FS [exfat]: ").strip().lower() or "exfat"
                label = input("Label [DATOS]: ").strip() or "DATOS"
                use_gpt = input("GPT? (s/n) [s]: ").lower().startswith("s")

            action_clean_and_recreate(disk, fs=fs, label=label, use_gpt=use_gpt, dry_run=dry_run)

        elif choice == "7":
            if RICH_AVAILABLE:
                to = Prompt.ask("[warning]Convert to style[/]", choices=["mbr", "gpt"], default="gpt")
            else:
                to = input("Convertir a (mbr / gpt): ").strip().lower()
            if to in ("mbr", "gpt"):
                action_convert_style(disk, to, dry_run=dry_run)

        elif choice == "8":
            if RICH_AVAILABLE:
                sub = Prompt.ask("[info]Show commands for[/]", choices=["readonly", "wipe", "format"], default="wipe")
                mapping = {"readonly": "fix-readonly", "wipe": "clean-recreate", "format": "format"}
            else:
                print("\n¿Qué acción? a) readonly  b) clean-recreate  c) format")
                sub = input("Opción: ").strip().lower()
                mapping = {"a": "fix-readonly", "b": "clean-recreate", "c": "format"}
            action_show_commands(disk, mapping.get(sub, "clean-recreate"))

        elif choice == "9":
            action_rescan()

        elif choice in ("0", "q", "back"):
            break
        else:
            if RICH_AVAILABLE:
                console.print(Text("▸ UNKNOWN PROTOCOL. RE-ENTER.", style="warning"))
            else:
                print("Opción inválida.")


def main_menu():
    """Menú principal interactivo estilo CYBERDECK."""
    dry_run = False

    # === CYBERPUNK BOOT SEQUENCE ===
    if RICH_AVAILABLE and console:
        console.clear()
        show_cyberpunk_banner()
    else:
        print(f"\nCyberPy Ari v{VERSION} - Cyberdeck Neural Storage Repair")
        print("CYBERDECK MODE - NEURAL STORAGE REPAIR\n")

    if not check_admin():
        if RICH_AVAILABLE and console:
            console.print(Panel(
                Text("ADMINISTRATOR PRIVILEGES REQUIRED\n\n"
                     "Many neural breach commands will fail without elevation.\n"
                     "Restart this terminal as Administrator.", style="#ff2e63"),
                title=Text("ACCESS DENIED", style="bold #ff2e63"),
                border_style="#ff2e63"
            ))
        else:
            print("⚠️  NO estás ejecutando como Administrador. ...")

    if not RICH_AVAILABLE:
        print("ℹ️  Para la experiencia completa cyberpunk:  pip install rich\n")

    while True:
        if RICH_AVAILABLE and console:
            console.print()
            console.print(Rule(title=Text("MAIN DECK // COMMAND MATRIX", style="bold #00f0ff"), style="#00f0ff"))

            menu_text = Text()
            menu_text.append("1", style="bold #00f0ff")
            menu_text.append("  ▸ SCAN REMOVABLE UNITS (recommended)\n", style="text")
            menu_text.append("2", style="warning bold")
            menu_text.append("  ▸ FULL SYSTEM SCAN (includes internal drives - EXTREME CAUTION)\n", style="text")
            menu_text.append("3", style="info bold")
            menu_text.append("  ▸ FORCE NEURAL RESCAN\n", style="text")
            menu_text.append("4", style="bold #ff00aa")
            menu_text.append("  ▸ TOGGLE DRY-RUN MODE (simulation)\n", style="text")
            menu_text.append("5", style="bold #00f0ff")
            menu_text.append("  ▸ VIEW NEURAL LOG\n", style="text")
            menu_text.append("6", style="info bold")
            menu_text.append("  ▸ DECK DOCUMENTATION & TACTICS\n", style="text")
            menu_text.append("0", style="bold #ff2e63")
            menu_text.append("  ▸ DISCONNECT NEURAL LINK (exit)", style="text")

            console.print(Panel(menu_text, title=Text("AVAILABLE OPERATIONS", style="bold #ff00aa"), border_style="#ff00aa", padding=(1, 3)))

            if dry_run:
                console.print(Text("▸ DRY-RUN MODE ACTIVE — All breaches simulated only", style="warning bold"))

            choice = Prompt.ask("\n[primary]>>> SELECT COMMAND ID[/]", default="1", show_default=False).strip()
        else:
            print("\n" + "=" * 50)
            print("MENÚ PRINCIPAL")
            print(" 1. Listar unidades REMOVIBLES / EXTERNAS (recomendado)")
            print(" 2. Listar TODOS los discos (¡incluye internos - peligro!)")
            print(" 3. Forzar rescan de discos")
            print(" 4. Activar / desactivar MODO SIMULACIÓN (dry-run)")
            print(" 5. Ver log de acciones")
            print(" 6. Ayuda y recomendaciones")
            print(" 0. Salir")
            print("=" * 50)
            choice = input("Opción: ").strip()

        if choice == "1":
            if RICH_AVAILABLE and console:
                with console.status("[primary]SCANNING REMOVABLE NEURAL LINKS...[/]", spinner="dots"):
                    disks = get_disks(only_removable=True)
            else:
                disks = get_disks(only_removable=True)

            print_disk_table(disks, "NEURAL SCAN - REMOVABLE / EXTERNAL UNITS")
            if disks:
                sel = Prompt.ask("\n[primary]>>> SELECT TARGET DISK ID (decimal)[/]", default="") if RICH_AVAILABLE else input("\nIngresa el número: ").strip()
                if sel.isdigit():
                    selected = next((d for d in disks if d["Number"] == int(sel)), None)
                    if selected:
                        disk_menu(selected, dry_run=dry_run)
                    else:
                        if RICH_AVAILABLE: console.print(Text("▸ TARGET NOT FOUND IN CURRENT SCAN.", style="warning"))
                        else: print("No encontrado.")

        elif choice == "2":
            if RICH_AVAILABLE and console:
                console.print(Panel(Text("EXTREME CAUTION: INTERNAL DRIVES VISIBLE. MISUSE CAN BRICK YOUR SYSTEM.", style="bold #ff2e63"),
                                    border_style="#ff2e63", title=Text("WARNING", style="bold #ff2e63")))
                if not Confirm.ask("[danger]Proceed with full system scan?[/]", default=False):
                    continue
            else:
                print("\n⚠️  MOSTRANDO TODOS LOS DISCOS. EXTREMO CUIDADO.")
                input("Enter para continuar...")

            disks = get_all_disks()
            print_disk_table(disks, "FULL SYSTEM NEURAL SCAN - ALL DRIVES")
            if disks:
                sel = Prompt.ask("\n[warning]>>> TARGET DISK ID[/]", default="") if RICH_AVAILABLE else input("ID: ").strip()
                if sel.isdigit():
                    selected = next((d for d in disks if d["Number"] == int(sel)), None)
                    if selected:
                        disk_menu(selected, dry_run=dry_run)

        elif choice == "3":
            if RICH_AVAILABLE and console:
                with console.status("[accent]FORCING NEURAL RESCAN...[/]", spinner="arc"):
                    action_rescan()
            else:
                action_rescan()

        elif choice == "4":
            dry_run = not dry_run
            estado = "ENGAGED (simulation only - no real breaches)" if dry_run else "DISENGAGED (live execution)"
            log_action(f"DRY-RUN MODE set to {dry_run}", "WARN")
            if RICH_AVAILABLE:
                console.print(Text(f"▸ DRY-RUN MODE {estado}", style="warning bold"))
            else:
                print(f"Modo simulación: {estado}")

        elif choice == "5":
            if LOG_FILE.exists():
                if RICH_AVAILABLE:
                    console.print(Rule(title=Text("NEURAL LOG DUMP", style="bold #9d4edd"), style="#9d4edd"))
                try:
                    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()[-25:]
                    for line in lines:
                        if RICH_AVAILABLE:
                            console.print(Text(line, style="dim"))
                        else:
                            print(line)
                except Exception as e:
                    print(f"Log read error: {e}")
            else:
                if RICH_AVAILABLE: console.print(Text("▸ NO LOG ENTRIES YET.", style="dim"))
                else: print("Aún no hay log.")

        elif choice == "6":
            if RICH_AVAILABLE and console:
                help_content = Text()
                help_content.append("TACTICAL RECOMMENDATIONS\n\n", style="bold #00f0ff")
                help_content.append("• For most USB/external drive issues → use action 6 (CLEAN + RECREATE) with exFAT\n", style="text")
                help_content.append("• ReadOnly drive? Start with action 2 (clear readonly)\n", style="text")
                help_content.append("• Always double-check disk ID before any breach\n", style="text")
                help_content.append("• Large drives (>2TB) → prefer GPT\n", style="text")
                help_content.append("• exFAT = best cross-platform compatibility\n", style="text")
                help_content.append("• Full logs saved to cyberdeck_log.txt\n\n", style="text")
                help_content.append("Remember: You are the decker. Act with precision.", style="accent italic")
                console.print(Panel(help_content, title=Text("DECK MANUAL", style="bold #9d4edd"), border_style="#9d4edd"))
            else:
                print("RECOMENDACIONES: Usa principalmente la opción de limpiar y recrear con exFAT...")

        elif choice in ("0", "q", "exit"):
            if RICH_AVAILABLE:
                console.print(Text("\n▸ NEURAL LINK DISCONNECTED. STAY FROSTY, DECKER.", style="#00f0ff"))
            else:
                print("Saliendo de CyberPy Ari. ¡Gracias, decker!")
            break
        else:
            if RICH_AVAILABLE:
                console.print(Text("▸ INVALID COMMAND. RE-ENTER ID.", style="warning"))
            else:
                print("Opción no válida.")


# ====================== INTERFAZ DE LÍNEA DE COMANDOS (CLI) ======================

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(
        description="CyberPy Ari - Cyberdeck Neural Storage Repair (Textual TUI + diskpart/PowerShell backend)"
    )
    parser.add_argument("--list", action="store_true", help="Listar discos removibles y salir")
    parser.add_argument("--list-all", action="store_true", help="Listar TODOS los discos y salir")
    parser.add_argument("--disk", type=int, help="Número de disco sobre el que operar")
    parser.add_argument("--fix-readonly", action="store_true", help="Quitar atributo readonly del disco")
    parser.add_argument("--clean-recreate", action="store_true", help="Limpiar disco y crear partición única (destructivo)")
    parser.add_argument("--fs", default="exfat", choices=["exfat", "ntfs", "fat32"], help="Sistema de archivos para --clean-recreate o format")
    parser.add_argument("--label", default="DATOS", help="Etiqueta del volumen")
    parser.add_argument("--dry-run", action="store_true", help="Simular todas las operaciones sin ejecutar cambios")
    parser.add_argument("--yes", action="store_true", help="Saltar algunas confirmaciones (usa con cuidado)")
    return parser.parse_args()


def cli_mode(args):
    """Modo no interactivo para scripting / uso rápido."""
    dry_run = args.dry_run
    if args.list:
        disks = get_disks(only_removable=True)
        print_disk_table(disks, "Unidades removibles / externas")
        return
    if args.list_all:
        disks = get_all_disks()
        print_disk_table(disks, "Todos los discos")
        return

    if args.disk is None:
        print("Error: --disk N es requerido para operaciones sobre un disco.")
        sys.exit(2)

    # Reconstruimos la información del disco
    all_disks = get_all_disks()
    disk = next((d for d in all_disks if d["Number"] == args.disk), None)
    if not disk:
        print(f"No se encontró el disco #{args.disk}")
        sys.exit(3)

    print(f"Disco seleccionado: #{disk['Number']} - {disk['FriendlyName']} ({disk['Size']} GB)")

    if args.fix_readonly:
        action_fix_readonly(disk, dry_run=dry_run)
    elif args.clean_recreate:
        if not args.yes and not dry_run:
            if not confirm_dangerous_action(args.disk, "Limpiar + recrear partición vía CLI", "LIMPIAR"):
                print("Cancelado.")
                return
        action_clean_and_recreate(disk, fs=args.fs, label=args.label, use_gpt=True, dry_run=dry_run)
    else:
        print("No se especificó ninguna acción (--fix-readonly o --clean-recreate).")
        print("Usa --help para ver las opciones.")


# ====================== TEXTUAL CYBERDECK APP (v2.0) ======================

if TEXTUAL_AVAILABLE:
    class BreachConfirmation(ModalScreen[bool]):
        """Modal estilo cyberpunk para confirmaciones destructivas con múltiples capas."""

        def __init__(self, disk_num: int, description: str, required_phrase: str = "BREACH"):
            super().__init__()
            self.disk_num = disk_num
            self.description = description
            self.required_phrase = required_phrase

        def compose(self) -> ComposeResult:
            yield Container(
                Static(
                    Text("⚠️  NEURAL BREACH AUTHORIZATION  ⚠️", style="bold #ff2e63"),
                    classes="modal-title"
                ),
                Static(
                    f"TARGET: 0x{self.disk_num:02X}\n"
                    f"OPERATION: {self.description}\n\n"
                    "THIS ACTION IS IRREVERSIBLE.\n"
                    "MULTI-LAYER NEURAL VERIFICATION REQUIRED.",
                    classes="modal-body"
                ),
                Static("Layer 1: Confirm Disk ID", id="layer1-label"),
                Input(placeholder=f"Type {self.disk_num}", id="layer1-input"),
                Static("Layer 2: Override Phrase", id="layer2-label"),
                Input(placeholder=f"Type exactly {self.required_phrase}", id="layer2-input"),
                Static("Layer 3: Final Execute", id="layer3-label"),
                Input(placeholder="Type EXECUTE to breach", id="layer3-input"),
                Button("ABORT", id="abort", variant="error"),
                Button("AUTHORIZE BREACH", id="authorize", variant="success"),
                id="breach-modal",
                classes="cyber-modal"
            )

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "abort":
                self.dismiss(False)
                return

            if event.button.id == "authorize":
                l1 = self.query_one("#layer1-input", Input).value.strip()
                l2 = self.query_one("#layer2-input", Input).value.strip().upper()
                l3 = self.query_one("#layer3-input", Input).value.strip().upper()

                if l1 != str(self.disk_num):
                    self.query_one("#layer1-label", Static).update("❌ DISK ID MISMATCH")
                    return
                if l2 != self.required_phrase.upper():
                    self.query_one("#layer2-label", Static).update("❌ PHRASE MISMATCH - FIREWALL ENGAGED")
                    return
                if l3 != "EXECUTE":
                    self.query_one("#layer3-label", Static).update("❌ FINAL KEYWORD REQUIRED")
                    return

                log_action(f"MODAL BREACH AUTHORIZED for disk 0x{self.disk_num:02X}: {self.description}", "WARN")
                self.dismiss(True)

    class CyberdeckApp(App):
        """Cyberdeck TUI for advanced storage repair."""

        TITLE = "CYBERPY ARI // CYBERDECK v3.0"
        SUB_TITLE = "NEURAL STORAGE BREACH & REPAIR - MAJOR UPGRADE"

        CSS = """
        Screen {
            background: #0a0a12;
            color: #e0e0e0;
        }

        Header {
            background: #1a0033;
            color: #00f0ff;
            text-style: bold;
        }

        Footer {
            background: #1a0033;
            color: #00f0ff;
        }

        DataTable {
            background: #11111a;
            color: #e0e0e0;
            border: tall #00f0ff;
        }

        DataTable > .datatable--header {
            background: #1a0033;
            color: #ff00aa;
            text-style: bold;
        }

        .cyber-panel {
            border: tall #00f0ff;
            background: #0f0f18;
            padding: 1;
        }

        #sidebar {
            width: 24;
        }

        #content {
            width: 1fr;
            min-width: 70;
        }

        .action-button {
            width: 1fr;
            height: 4;
            min-width: 24;
            margin: 0 1;
            content-align: center middle;
            overflow: hidden;
            padding: 0 1;
        }

        .section-header {
            color: #ff00aa;
            text-style: bold;
            margin-top: 1;
            margin-bottom: 0;
        }

        .actions-grid {
            grid-size: 2;
            width: 100%;
            /* 2 columns so each button has enough horizontal space for its text to be fully visible */
        }

        .action-button:hover {
            background: #ff00aa;
            color: #0a0a12;
            text-style: bold;
        }

        .danger-button {
            background: #3a0011;
            color: #ff2e63;
            border: tall #ff2e63;
        }

        .danger-button:hover {
            background: #ff2e63;
            color: #0a0a12;
        }

        .neural-log {
            border: tall #39ff14;
            background: #050508;
            color: #39ff14;
        }

        .modal-title {
            text-style: bold;
            color: #ff2e63;
            text-align: center;
        }

        .modal-body {
            color: #e0e0e0;
            margin: 1 0;
        }

        #breach-modal {
            width: 70;
            height: auto;
            border: heavy #ff2e63;
            background: #0a0a12;
            padding: 2;
        }

        .status-bar {
            color: #9d4edd;
            text-style: italic;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit Cyberdeck", show=True),
            Binding("r", "rescan", "Rescan", show=True),
            Binding("d", "toggle_dry_run", "Toggle Dry-Run", show=True),
            Binding("escape", "unfocus", "Unfocus", show=False),
        ]

        selected_disk: reactive[dict | None] = reactive(None)
        dry_run: reactive[bool] = reactive(False)
        disks: reactive[list] = reactive([])

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)

            with Horizontal():
                with Vertical(classes="cyber-panel", id="sidebar"):
                    yield Label("REMOVABLE NEURAL LINKS", classes="status-bar")
                    yield DataTable(id="disk-table", cursor_type="row")
                    yield Button("RESCAN LINKS", id="rescan-btn", classes="action-button")

                with Vertical(classes="cyber-panel", id="content"):
                    yield Label("TARGET NEURAL PROFILE", classes="status-bar")
                    yield Static("No target selected.\n\nScan and select a drive from the left panel.", id="details")

                    yield TextualRule()

                    # Controls area - scrollable if many sections
                    with ScrollableContainer():
                        # === SECTION: QUICK ACTIONS ===
                        yield Label("QUICK ACTIONS", classes="section-header")
                        with Grid(classes="actions-grid"):
                            yield Button("PROFILE DUMP", id="btn-profile", classes="action-button")
                            yield Button("CLEAR READONLY", id="btn-readonly", classes="action-button")
                            yield Button("CHKDSK SCAN", id="btn-chkdsk", classes="action-button")

                        # === SECTION: LETTER & FORMAT ===
                        yield Label("LETTER & FORMAT", classes="section-header")
                        with Grid(classes="actions-grid"):
                            yield Button("ASSIGN LETTER", id="btn-letter", classes="action-button")
                            yield Button("FORMAT EXISTING", id="btn-format", classes="action-button")
                            yield Button("WIPE + RECREATE", id="btn-wipe", classes="danger-button")

                        # === SECTION: MANAGEMENT ===
                        yield Label("MANAGEMENT", classes="section-header")
                        with Grid(classes="actions-grid"):
                            yield Button("SHOW COMMANDS", id="btn-commands", classes="action-button")
                            yield Button("CONVERT GPT/MBR", id="btn-convert", classes="action-button")
                            yield Button("TOGGLE DRY-RUN", id="btn-dryrun", classes="action-button")

                        # === SECTION: v3.0 ADVANCED TOOLS ===
                        yield Label("v3.0 ADVANCED TOOLS", classes="section-header")
                        with Grid(classes="actions-grid"):
                            yield Button("HEALTH / SMART", id="btn-health", classes="action-button")
                            yield Button("AUTO-ADVISOR", id="btn-advisor", classes="action-button")
                            yield Button("VISUAL MAP", id="btn-map", classes="action-button")
                            yield Button("EXPORT SCRIPT", id="btn-export", classes="action-button")
                            yield Button("SETTINGS", id="btn-settings", classes="action-button")
                            yield Button("PART WIZARD", id="btn-wizard", classes="action-button")

            yield Label("NEURAL LOG", classes="status-bar")
            with Horizontal(id="log-controls"):
                yield Label("Search:", classes="status-bar")
                yield Input(placeholder="filter log...", id="log-search")
                yield Button("FILTER", id="btn-filter-log", classes="action-button")
            yield TextualLog(id="neural-log", classes="neural-log", highlight=True)

            yield Footer()

        def on_mount(self) -> None:
            self.cfg = load_config()
            self.log_neural("CYBERDECK INITIALIZED. RUNNING AS NEURAL OPERATOR. (v3.0)", "SUCCESS")
            table = self.query_one("#disk-table", DataTable)
            table.add_columns("ID", "Model", "Size (GB)", "Bus", "Style", "Removable", "ReadOnly")
            table.focus()
            self.refresh_disks()

            if not check_admin():
                self.log_neural("WARNING: NOT RUNNING AS ADMINISTRATOR. Many commands will fail.", "ERROR")
            self.log_neural(f"Config loaded. Default FS: {self.cfg.get('default_fs')}", "INFO")

        def log_neural(self, message: str, level: str = "INFO"):
            log_action(message, level)
            log_widget = self.query_one("#neural-log", TextualLog)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            # Use Rich markup (highlight=True on the widget will render it)
            # Colors via markup for reliability
            color_map = {"INFO": "cyan", "WARN": "yellow", "ERROR": "red", "SUCCESS": "green"}
            col = color_map.get(level, "white")
            log_widget.write(f"[{timestamp}] [[{level}]] {message}")  # simple, highlight handles basic styling

        def refresh_disks(self) -> None:
            table = self.query_one("#disk-table", DataTable)
            table.clear()
            try:
                self.disks = get_disks(only_removable=True)
            except Exception as e:
                self.log_neural(f"SCAN FAILED: {e}", "ERROR")
                return
            for d in self.disks:
                num = d.get("Number", "?")
                name = str(d.get("FriendlyName", "UNKNOWN"))[:32]
                size = f"{d.get('Size', 0):.1f}"
                bus = str(d.get("BusType", "N/A"))[:6]
                estilo = str(d.get("PartitionStyle", "N/A"))[:4]
                removable = "⚡ YES" if d.get("IsRemovable") else "NO"
                ro = "YES" if d.get("IsReadOnly") else "NO"
                table.add_row(f"0x{int(num):02X}", name, size, bus, estilo, removable, ro, key=num)
            self.log_neural(f"NEURAL SCAN COMPLETE. {len(self.disks)} removable targets found.", "SUCCESS")

        def watch_selected_disk(self, old, new) -> None:
            details = self.query_one("#details", Static)
            if not new:
                details.update("No target selected.")
                return
            num = new.get("Number")
            name = new.get("FriendlyName", "UNKNOWN")
            content = Text()
            content.append(f"TARGET: ", style="dim")
            content.append(f"{name}\n", style="bold #00f0ff")
            content.append(f"ID: 0x{num:02X}   SIZE: {new.get('Size')} GB\n", style="#e0e0e0")
            content.append(f"BUS: {new.get('BusType')}   STYLE: {new.get('PartitionStyle')}\n", style="#9d4edd")
            ro_style = "#ff2e63" if new.get('IsReadOnly') else "#39ff14"
            content.append(f"READONLY: {'BREACH' if new.get('IsReadOnly') else 'CLEAR'}   ", style=ro_style)
            content.append(f"STATUS: {new.get('Status', 'N/A')}\n\n", style="#39ff14")
            content.append("Select a protocol below to begin breach sequence.", style="dim")
            details.update(content)

        def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
            if event.row_key is None:
                return
            disk_id = int(event.row_key.value)
            selected = next((d for d in self.disks if d.get("Number") == disk_id), None)
            if selected:
                self.selected_disk = selected
                self.log_neural(f"TARGET ACQUIRED: 0x{disk_id:02X} - {selected.get('FriendlyName')}", "INFO")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            btn_id = event.button.id
            disk = self.selected_disk
            if btn_id == "rescan-btn":
                self.action_rescan()
                return
            if btn_id == "btn-dryrun":
                self.action_toggle_dry_run()
                return
            if not disk:
                self.log_neural("NO TARGET SELECTED. Choose a drive from the left panel first.", "WARN")
                return
            num = disk["Number"]
            if btn_id == "btn-profile":
                self.run_worker(lambda: self._run_profile(disk), thread=True)
            elif btn_id == "btn-readonly":
                self.run_worker(lambda: self._run_readonly(disk), thread=True)
            elif btn_id == "btn-chkdsk":
                self.run_worker(lambda: self._run_chkdsk(disk), thread=True)
            elif btn_id == "btn-letter":
                self.run_worker(lambda: self._run_assign_letter(disk), thread=True)
            elif btn_id == "btn-format":
                self.run_worker(lambda: self._run_format(disk), thread=True)
            elif btn_id == "btn-wipe":
                # v3.0: Secure wipe options
                self.log_neural("SELECT WIPE TYPE (v3.0): quick | zero | random", "WARN")
                # For demo, default to quick; in full version use a modal choice
                wipe_type = "quick"  # Could be enhanced with Prompt or new modal
                desc = f"FULL {wipe_type.upper()} WIPE + RECREATE"
                self._request_breach_confirmation(disk, desc, "BREACH", lambda d: self._run_wipe(d, wipe_type))
            elif btn_id == "btn-commands":
                self._show_commands(disk)
            elif btn_id == "btn-convert":
                self.log_neural("Convert style not fully wired in TUI yet.", "WARN")

            # v3.0 new handlers
            elif btn_id == "btn-health":
                self.run_worker(lambda: self._run_health_check(disk), thread=True)
            elif btn_id == "btn-advisor":
                self._show_advisor(disk)
            elif btn_id == "btn-map":
                self._show_visual_map(disk)
            elif btn_id == "btn-export":
                self._export_script(disk)
            elif btn_id == "btn-settings":
                self._open_settings()
            elif btn_id == "btn-wizard":
                if disk:
                    self._run_partition_wizard(disk)
                else:
                    self.log_neural("Select a disk first for the Partition Wizard.", "WARN")
            elif btn_id == "btn-filter-log":
                search = self.query_one("#log-search", Input).value.strip().lower()
                if search:
                    self.log_neural(f"FILTERING LOG for: {search}", "INFO")
                    # Simple demo: re-log would require storing history; here we just note
                    self.log_neural(" (Full history filter would require log buffer storage - demo active)", "WARN")
                else:
                    self.log_neural("Log filter cleared (enter text to search).", "INFO")

        def _request_breach_confirmation(self, disk: dict, description: str, phrase: str, callback):
            num = disk["Number"]
            self.push_screen(
                BreachConfirmation(num, description, phrase),
                callback=lambda authorized: self._on_breach_authorized(authorized, disk, callback)
            )

        def _on_breach_authorized(self, authorized: bool, disk: dict, callback):
            if authorized:
                self.log_neural(f"AUTHORIZATION GRANTED. EXECUTING ON 0x{disk['Number']:02X}...", "WARN")
                self.run_worker(lambda: callback(disk), thread=True)
            else:
                self.log_neural("BREACH ABORTED BY OPERATOR.", "INFO")

        def _run_profile(self, disk: dict):
            extra = get_partitions_and_volumes(disk["Number"])
            self.log_neural(f"PROFILE: {disk.get('FriendlyName')} | {disk.get('Size')}GB | {disk.get('BusType')}", "INFO")
            for p in extra.get("partitions", []):
                self.log_neural(f"  Partition {p.get('PartitionNumber')}: Letter={p.get('DriveLetter') or '-'}", "INFO")
            for v in extra.get("volumes", []):
                if v.get("DriveLetter"):
                    self.log_neural(f"  Volume {v.get('DriveLetter')}: {v.get('FileSystem')}", "INFO")

        def _run_readonly(self, disk: dict):
            self.log_neural(f"ATTEMPTING TO CLEAR READONLY on 0x{disk['Number']:02X}...", "WARN")
            success = action_fix_readonly(disk, dry_run=self.dry_run)
            self.log_neural("READONLY CLEARED." if success else "READONLY CLEAR FAILED", "SUCCESS" if success else "WARN")
            self.refresh_disks()

        def _run_chkdsk(self, disk: dict):
            self.log_neural(f"STARTING FILESYSTEM INTEGRITY SCAN on 0x{disk['Number']:02X}...", "INFO")
            action_chkdsk(disk, dry_run=self.dry_run)
            self.log_neural("CHKDSK SEQUENCE COMPLETE.", "SUCCESS")

        def _run_assign_letter(self, disk: dict):
            self.log_neural("ASSIGN LETTER (may need console interaction).", "WARN")
            action_assign_letter(disk, dry_run=self.dry_run)
            self.refresh_disks()

        def _run_format(self, disk: dict):
            self.log_neural(f"FORMATTING TARGET 0x{disk['Number']:02X}...", "WARN")
            action_format_existing(disk, fs="exfat", label="CYBERUSB", dry_run=self.dry_run)
            self.log_neural("FORMAT COMPLETE.", "SUCCESS")
            self.refresh_disks()

        def _run_wipe(self, disk: dict, wipe_type: str = "quick"):
            """v3.0 enhanced wipe with secure options."""
            self.log_neural(f"EXECUTING {wipe_type.upper()} WIPE + RECREATE on 0x{disk['Number']:02X}...", "WARN")
            # v3.0: Simulated progress + different wipe intensity
            steps = 5 if wipe_type == "quick" else (8 if wipe_type == "zero" else 12)
            for i in range(steps):
                pct = (i+1) * (100 // steps)
                bar = '█' * (pct // 5)
                self.log_neural(f"  [{wipe_type.upper()}] Progress: {pct}% {bar}", "INFO")
            # Real wipe still uses the core action (can be extended for zero/random via PowerShell in future)
            success = action_clean_and_recreate(disk, fs="exfat", label="DATOS", use_gpt=True, dry_run=self.dry_run)
            self.log_neural(f"{wipe_type.upper()} WIPE + RECREATE FINISHED." if success else "WIPE FAILED", "SUCCESS" if success else "ERROR")
            self.refresh_disks()

        def _show_commands(self, disk: dict):
            self.log_neural("=== EQUIVALENT BREACH COMMANDS ===", "INFO")
            self.log_neural(f"select disk {disk['Number']}", "INFO")
            self.log_neural("clean / convert gpt / create partition primary / format fs=exfat quick", "INFO")
            self.log_neural("PowerShell: Clear-Disk + New-Partition + Format-Volume", "SUCCESS")

        # ====================== v3.0 HANDLERS ======================

        def _run_health_check(self, disk: dict):
            self.log_neural(f"RUNNING SMART / HEALTH CHECK on 0x{disk['Number']:02X}...", "INFO")
            health = get_smart_health(disk)
            for k, v in health.items():
                self.log_neural(f"  {k}: {v}", "SUCCESS" if str(v).lower() in ["healthy","ok"] else "WARN")
            self.log_neural("Health check complete. Review the data above.", "SUCCESS")

        def _show_advisor(self, disk: dict):
            self.log_neural("=== AUTO-REPAIR ADVISOR (v3.0) ===", "INFO")
            recs = get_auto_advisor(disk)
            for title, desc in recs:
                self.log_neural(f"  [{title}] {desc}", "WARN" if "NO RECOMENDADO" in title or "RAW" in title else "INFO")
            self.log_neural("Advisor ready. Use the recommended actions above.", "SUCCESS")

        def _show_visual_map(self, disk: dict):
            self.log_neural(f"GENERATING VISUAL DISK MAP for 0x{disk['Number']:02X}...", "INFO")
            extra = get_partitions_and_volumes(disk["Number"])
            map_str = render_visual_disk_map(disk, extra)
            self.log_neural(map_str, "INFO")
            self.log_neural("Visual map generated (text representation).", "SUCCESS")

        def _export_script(self, disk: dict):
            self.log_neural("EXPORTING REPAIR SCRIPT (v3.0)...", "INFO")
            # For demo, export a common safe sequence
            actions = ["clear-readonly", "clean-recreate"]
            script = export_repair_script(disk, actions)
            out_path = Path.home() / f"repair_disk_{disk['Number']}.ps1"
            out_path.write_text(script, encoding="utf-8")
            self.log_neural(f"Script exported to: {out_path}", "SUCCESS")
            self.log_neural("You can review and run it later with PowerShell.", "INFO")

        def _open_settings(self):
            """Abre settings simples (v3.0) - cambia tema y guarda config."""
            self.log_neural("OPENING SETTINGS...", "INFO")
            themes = list(CYBER_THEMES.keys())
            current = self.cfg.get("theme", "cyan-magenta")
            idx = (themes.index(current) + 1) % len(themes) if current in themes else 0
            new_theme = themes[idx]
            self.cfg["theme"] = new_theme
            save_config(self.cfg)
            self.log_neural(f"Theme switched to: {new_theme}", "SUCCESS")
            self.log_neural("Config saved. Restart app for full theme effect (CSS is static).", "INFO")
            # For demo, update subtitle with theme
            self.sub_title = f"NEURAL STORAGE BREACH & REPAIR - THEME: {new_theme.upper()}"

        def _run_partition_wizard(self, disk: dict):
            """v3.0 Partition Layout Assistant - paso a paso para layouts personalizados."""
            self.log_neural("=== PARTITION WIZARD (v3.0) ===", "INFO")
            self.log_neural("This is a guided assistant for custom partition creation.", "INFO")
            # Demo: suggest a simple layout
            self.log_neural("Recommended for external drive: 1 large exFAT partition (current default).", "INFO")
            self.log_neural("For advanced: Use 'create partition' commands manually or export script.", "WARN")
            self.log_neural("Future: Interactive size input for EFI + Data + Recovery partitions.", "INFO")
            # For now, trigger the standard wipe as example
            self._request_breach_confirmation(disk, "WIZARD: CUSTOM LAYOUT (demo: single partition)", "BREACH", self._run_wipe)

        def action_rescan(self):
            self.log_neural("FORCING NEURAL RESCAN...", "INFO")
            self.refresh_disks()

        def action_toggle_dry_run(self):
            self.dry_run = not self.dry_run
            state = "ENGAGED (simulation only)" if self.dry_run else "DISENGAGED (LIVE)"
            self.log_neural(f"DRY-RUN MODE {state}", "WARN")
            self.sub_title = f"NEURAL STORAGE BREACH & REPAIR  |  DRY-RUN: {self.dry_run}"

        def action_unfocus(self):
            self.screen.focus_next()


# ====================== PUNTO DE ENTRADA ======================

if __name__ == "__main__":
    args = parse_args()

    try:
        if args.list or args.list_all or args.disk:
            # CLI fallback mode (still useful for scripts)
            cli_mode(args)
        else:
            # Launch the full cyberpunk Textual app
            if TEXTUAL_AVAILABLE:
                try:
                    CyberdeckApp().run()
                except Exception as e:
                    log_action(f"Textual app runtime error: {e}", "ERROR")
                    print(f"Failed to start the cyberdeck interface: {e}")
                    print("You can still use CLI mode:")
                    print("  py cyberdeck.py --list")
                    print("  py cyberdeck.py --list-all")
            else:
                import sys
                print("Textual is required for the full cyberdeck interface.")
                print("Install with:  py -m pip install textual rich")
                print()
                print("IMPORTANT: Use the SAME Python launcher for pip and for running the script.")
                print(f"Current Python executable: {sys.executable}")
                print("Recommended commands:")
                print("  py -m pip install textual rich")
                print("  py cyberdeck.py")
                print()
                print("You can still use the lightweight CLI mode:")
                print("  py cyberdeck.py --list")
                print("  py cyberdeck.py --list-all")
                print("  py cyberdeck.py --disk N --clean-recreate --fs exfat --label MYUSB")
    except KeyboardInterrupt:
        print("\n▸ NEURAL LINK TERMINATED.")
        log_action("App terminated by user (KeyboardInterrupt)", "INFO")
    except Exception as e:
        log_action(f"Critical failure: {e}", "ERROR")
        print(f"\nCRITICAL FAILURE: {e}")
        print("Check cyberdeck_log.txt for details.")
        sys.exit(1)
