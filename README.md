# CyberPy Ari - Cyberdeck Neural Storage Repair

**Versión:** 2.0  
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

## Créditos

Desarrollado como una versión mejorada y estilizada de `diskpart` enfocada en unidades externas, con vibe cyberpunk.

¡Disfruta tu cyberdeck! 🕶️

---

**Uso rápido recomendado:**

```powershell
py -m pip install -r requirements.txt
py cyberdeck.py
```