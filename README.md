# CyberPy Ari - Cyberdeck Neural Storage Repair

**Versión:** 3.0 (Major Upgrade)  
**Proyecto:** cyberpy_ari  
**Estilo:** Cyberpunk TUI (Terminal User Interface)

Una herramienta avanzada y visual para reparar, formatear y gestionar unidades de almacenamiento removibles (pendrives, HDD/SSD externos) con un interfaz estilo **cyberdeck**.

---

## Características

- Interfaz completa estilo cyberpunk construida con **Textual**
- Detección inteligente de unidades removibles
- Múltiples capas de confirmación dramáticas para operaciones destructivas
- Transparencia total (muestra los comandos equivalentes de `diskpart` y PowerShell)
- Log en vivo estilo "neural log"
- Soporte para los perfiles más comunes de reparación:
  - Limpiar + recrear partición (la más efectiva)
  - Quitar protección contra escritura (readonly)
  - Formateo rápido
  - Asignar letra de unidad
  - chkdsk
  - etc.
- Modo simulación (dry-run)
- Funciona tanto en modo TUI completo como en CLI ligero

---

## Requisitos

- Windows 10/11
- Python 3.10+
- Ejecutar **siempre como Administrador**

### Instalación

```powershell
# Recomendado (usa el mismo launcher)
py -m pip install -r requirements.txt

# O manualmente
py -m pip install textual rich
```

---

## Uso

### Modo Cyberdeck (recomendado)

```powershell
py cyberdeck.py
```

### Modo CLI ligero

```powershell
# Listar solo unidades removibles
py cyberdeck.py --list

# Listar todos los discos (¡cuidado!)
py cyberdeck.py --list-all

# Reparación rápida vía CLI
py cyberdeck.py --disk 2 --clean-recreate --fs exfat --label "MIUSB"
```

---

## Estructura del proyecto

```
cyberpy_ari/
├── cyberdeck.py          # Aplicación principal (TUI + CLI)
├── requirements.txt      # Dependencias
└── README.md             # Este archivo
```

El log se guarda automáticamente en `cyberdeck_log.txt` dentro de la carpeta.

---

## Consejos de seguridad

- Siempre verifica el número de disco antes de ejecutar operaciones destructivas.
- Usa primero el modo `--dry-run` o activa Dry-Run dentro de la interfaz.
- Haz copias de seguridad de datos importantes.
- Esta herramienta puede borrar información de forma **irreversible**.

---

## Novedades v3.0 (Mejoras Muy Grandes)

- **Visual Partition Mapper**: Representación visual de las particiones en la terminal.
- **Auto-Repair Advisor**: Analiza el estado del disco y recomienda las mejores acciones automáticamente.
- **SMART / Health Dashboard**: Datos reales de salud del disco (SMART, predict failure, etc.).
- **Repair Script Export**: Genera scripts .ps1 reutilizables con las acciones elegidas.
- **Persistent Config**: Guarda tus preferencias (FS por defecto, etiquetas, dry-run).
- **Secure Wipe Levels**: Opciones avanzadas de borrado con advertencias extra.
- **Mejor UI**: Más botones, barra de estado, progreso implícito y ayuda integrada.
- Muchas mejoras de estabilidad, manejo de errores y organización interna.

## Créditos

Desarrollado como una versión mejorada y estilizada de `diskpart` enfocada en unidades externas, con vibe cyberpunk.

¡Disfruta tu cyberdeck v3.0! 🕶️🚀

---

**Uso rápido recomendado:**

```powershell
py -m pip install -r requirements.txt
py cyberdeck.py
```