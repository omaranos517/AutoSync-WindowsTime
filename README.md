<p align="right">
    <img height="65" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" />
</p>

# 🕒 TimeSync – Windows Time Auto Synchronizer

A lightweight command-line utility that automatically fixes Windows time desynchronization issues — especially common on dual-boot systems (Windows + Linux).

<p align="center">
  <a href="https://github.com/omaranos517/AutoSync-WindowsTime/releases/latest">
    <img src="https://img.shields.io/badge/⬇%20Download-Latest%20Release-blue?style=for-the-badge">
  </a>
</p>

---

## ❗ The Problem

If you use:

- Windows + Linux (Ubuntu / Arch / Fedora)
- Dual boot with GRUB
- Or frequently switch between operating systems
- Damaged CMOS battery
- Broken Windows Time service

You may notice:

- Windows clock becomes incorrect after reboot
- Time shifts by ±1–3 hours
- Manual sync works only temporarily

---

## ⚠️ Why Does This Happen?

Linux and Windows store system time differently:

| System | Hardware Clock (RTC) |
|------|------|
| Linux | UTC |
| Windows | Local Time |

When switching systems:

- Linux writes UTC time to BIOS
- Windows reads it as local time

➡️ Result: incorrect Windows clock every boot.

---

## ✅ What TimeSync Does

TimeSync automatically repairs Windows time synchronization using the official Windows Time Service.

It:

- Fixes incorrect clock after reboot
- Restores broken Windows Time service
- Forces immediate resynchronization
- Can run automatically at Windows startup
- Works silently in the background

No system hacks.  
No scheduled tasks.  
No permanent registry changes.

---

## ✨ Features

### 🔐 Automatic Administrator Elevation
Requests administrator permission only when required.

---

### ⚙️ Windows Time Service Repair
- Enables `w32time` service
- Restarts the service safely
- Reconfigures synchronization providers

---

### 🌍 Trusted NTP Servers
Uses reliable public time servers:

- `time.google.com`
- `pool.ntp.org`
- `time.windows.com`

---

### 🧩 CLI Command Support
After installation:

```bash
timesync now
```

Works from any CMD or PowerShell window.

### 🚀 Startup Auto-Sync

Optional automatic synchronization when Windows starts.

- No tray icons
- No background services
- No scheduled tasks

---

## 🚀 Installation
Run the EXE installer: ```TimeSync.exe```


On first launch, you will see an installer menu:

```
1) Install
2) Sync time once (no installation)
3) Exit
```

*If installed:*

Files are copied to: ```C:\Program Files\TimeSync```


```timesync``` command becomes available system-wide.

Same behavior — installer will appear automatically.

---

## 🧪 Usage
Sync time immediately
```
timesync now
```

Enable auto-sync at startup
```
timesync startup enable
```

Disable startup sync
```
timesync startup disable
```

Check system status
```
timesync status
```

*Output example:*

```
Admin: True
In PATH: True
Startup: Enabled
```

Uninstall completely
```
timesync uninstall
```

---

## 💻 System Requirements

- Windows 10 / Windows 11

- Administrator permission (requested automatically)

---

## 🔒 Safety & Transparency

**TimeSync:**

- ❌ Does NOT modify system time manually

- ❌ Does NOT edit BIOS or RTC

- ❌ Does NOT create Windows services

- ❌ Does NOT add scheduled tasks

- ❌ Does NOT collect data

- ❌ Does NOT run permanently

**✔ Uses only official Windows commands:**

- ```sc```

- ```net```

- ```w32tm```

**📌 Ideal For:**

- Dual-boot users (Windows + Linux)

- Developers

- Laptop users

- Virtual machines

- Systems with broken time synchronization

- BIOS time drift issues

---

## 🏷 Version
TimeSync v1.0.0

---

## ⭐ Final Note

Windows still does not automatically fix time drift caused by Linux dual-boot.

Until it does — TimeSync keeps your clock accurate automatically.

*If you have ideas for:*

- GUI version

- tray icon

- background service

- auto-update

- signed executable

**Feel free to open an issue or contribute ⭐**