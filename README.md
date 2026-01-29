<p align="right">
    <img height="65" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" />
</p>

## 🕒 Windows Time Auto-Synchronizer

A lightweight system utility that automatically fixes Windows time desynchronization, especially for users running Windows + Linux (Ubuntu) dual boot via GRUB.

### ❗ The Problem (Why This Exists)

**If you use:**
    
- Windows + Ubuntu dual boot
    
- GRUB bootloader
    
- Or frequently switch between operating systems
- 

**You may notice that:**

Windows time becomes incorrect after reboot

Clock shifts by ±1–3 hours

Manual sync fixes it — but only *temporarily*


### ⚠️ Why does this happen?

Linux and Windows handle the system clock differently:

System	Hardware Clock (RTC)
Linux	UTC time
Windows	Local time

**When switching between systems:**

Linux writes UTC time to BIOS

Windows interprets it as local time

➡️ Result: *incorrect Windows clock every reboot*

---

## ✅ What This Tool Does

This program ensures that Windows always corrects its time automatically, without requiring any manual action.

- Fixes time after every boot
- Works silently in the background
- No registry edits required
- No permanent system modification
- No scheduled tasks needed

---

## ✨ Features

### 🔐 Automatic Administrator Elevation
Requests UAC permission only when required.

### 🔁 Startup Persistence
Automatically copies itself to:
    ```
    AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
    ```

so it runs at every login.

### ⚙️ Windows Time Service Repair

Sets w32time service to automatic

Restarts the service if broken

Rebuilds synchronization configuration

### 🌍 Reliable Global NTP Servers

time.google.com

pool.ntp.org

time.windows.com

### 📦 Supports both .py and .exe

Works with Python scripts

Fully compatible with PyInstaller executables

---

## 🛠️ How It Works
### 1️⃣ Administrator Check

Uses:
    ```
    ctypes.windll.shell32.IsUserAnAdmin()
    ```

If not elevated, Windows automatically prompts for admin access.

### 2️⃣ Self Installation

On first run:

Detects its current location

Copies itself to the Startup folder

Prevents duplicate copies

### 3️⃣ Time Synchronization Process

The tool performs the following:

• Enable Windows Time Service
• Restart w32time service
• Configure trusted NTP servers
• Force immediate synchronization

## 💻 Requirements

- Operating System: Windows 10 / Windows 11

- Permissions: Administrator privileges (requested automatically)

- Python Version (if running script): Python 3.9+

---

## 🚀 Usage
▶ Run from Python
```bash
python sync_time.py
```

**On first run:**

Admin permission will be requested

Script will install itself automatically

Time will be synchronized instantly

## 📦 Convert to EXE (Recommended)

You can convert it to a standalone Windows executable.

**🔧 Using PyInstaller:**
```
pip install pyinstaller
pyinstaller --onefile --noconsole sync_time.py
```

Output file:

dist/sync_time.exe


You can now delete Python — the EXE works independently.

---

## 🔁 When Does It Run?

Automatically at every Windows login

Especially useful after booting Linux and returning to Windows

---

## 🔒 Is This Safe?

- No registry modification
- No background service installation
- No scheduled tasks
- No telemetry
- No internet connection except NTP

*The tool only executes official Windows commands.*

---

## 📌 Ideal For

- Dual boot users (Windows + Linux)

- Developers

- Laptop users

- BIOS time drift issues

- Virtual machines

- Systems with broken time service

---

## ⭐ Final Note

This tool exists because:

***Windows should automatically fix its time — but it doesn’t.***

Until Microsoft resolves this dual-boot issue,
This utility ensures your clock is always correct.

If you want:

🔥 tray icon version

🔥 background silent service

🔥 auto-update support

🔥 signed executable

🔥 GUI version

***Feel free to contribute or open an issue ⭐***
