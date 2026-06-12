# CyberDeck (WPF Edition) 💻

**CyberDeck** es una herramienta visual con estética *cyberpunk* diseñada para la gestión, diagnóstico y reparación de unidades de almacenamiento (especialmente unidades extraíbles como USBs, SDs y discos externos).

Este ejecutable (`CyberDeck.exe`) es la **versión gráfica nativa para Windows** (basada en .NET 10 y WPF), portada a partir de la versión original en Python (CyberPy Ari).

## ⚠️ Advertencia de Seguridad
**EJECUTA ESTE PROGRAMA CON PRECAUCIÓN.**
La herramienta cuenta con opciones destructivas (`WIPE`, `FORMAT`) que **borrarán permanentemente** los datos de la unidad seleccionada. Asegúrate siempre de haber seleccionado el disco correcto antes de proceder. Se recomienda ejecutar la aplicación como **Administrador** para que todas las funciones de PowerShell y DiskPart operen correctamente.

## 🚀 Características Principales

- **Interfaz Gráfica Cyberpunk**: Diseño inmersivo estilo terminal con esquema de colores neón (magenta y cian).
- **Escaneo Inteligente**:
  - `Scan Removable Units`: Detecta de forma segura únicamente pendrives y discos externos.
  - `Full System Scan`: Escanea todos los discos (incluyendo los internos). ¡Usar con extremo cuidado!
- **Diagnóstico y Reparación**:
  - `Profile`: Muestra un volcado simulado del perfil del disco seleccionado.
  - `Clear RO`: Quita la protección contra escritura (Read-Only) de la unidad.
  - `Format`: Formatea la unidad seleccionada de forma rápida.
  - `Wipe`: Limpieza profunda y destructiva (Clean + Recreate).
  - `Show Cmds`: Transparencia total. Te muestra los comandos exactos de `diskpart` que se ejecutarían por debajo.

## 🛠️ Requisitos
- Windows 10 / 11
- .NET 10.0 Desktop Runtime (si se ejecuta en otra máquina que no lo tenga integrado)

## 📖 Instrucciones de Uso
1. Haz doble clic en `CyberDeck.exe`.
2. Presiona **Scan Removable** para listar tus pendrives.
3. Selecciona la unidad afectada en la cuadrícula de datos (DataGrid).
4. Elige la acción de recuperación o formateo en el Panel de Comandos de la derecha.
5. Observa el registro del sistema (Log) en la parte superior para ver el feedback de las operaciones.

---
*Desarrollado para el proyecto CyberPy Ari.*
