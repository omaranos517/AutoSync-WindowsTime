# 🕒 TimeSync

**The definitive solution for Windows time desynchronization.**  
Perfect for Dual-Boot users (Windows + Linux) and systems with CMOS battery issues.

<p align="center">
  <a href="https://github.com/omaranos517/AutoSync-WindowsTime/releases/latest">
    <img src="https://img.shields.io/badge/⬇%20Download-Latest%20Release-blue?style=for-the-badge">
  </a>
</p>

---

## ❓ The Problem

If you dual-boot **Windows and Linux**, you've probably noticed that your Windows clock becomes incorrect after switching operating systems.

This happens because:

- 🐧 Linux stores the hardware clock (RTC) in **UTC**
- 🪟 Windows expects the RTC in **Local Time**

This mismatch causes Windows to display the wrong time after rebooting from Linux.

**TimeSync bridges this gap** by force-synchronizing Windows time using official Microsoft time services immediately after login.

---

## ✨ Key Features

- ✅ **One-Click Repair**  
  Restores and properly configures the `w32time` Windows Time Service.

- 🌐 **Smart Auto-Sync**  
  Automatically retries synchronization until an internet connection is available.

- 🏢 **System Integration**  
  Registers as a professional application inside Windows **Apps & Features**.

- 💻 **Global Command Access**  
  Run `timesync` from any CMD or PowerShell window.

- 🔐 **Silent Background Execution**  
  Uses Windows Task Scheduler with **Highest Privileges** for seamless startup sync.

- 🔔 **Native Windows Notifications**  
  Uses Windows Toast Notifications to inform you about sync status.

- 🧹 **Clean Uninstall**  
  Fully removes Registry entries, PATH modifications, and scheduled tasks.

---

## 🚀 Getting Started

### 🔧 Installation

1. Download the latest `TimeSync.exe`
2. Run the file
3. On first launch, choose **Install**

The installer will: 

- Move the application to: `C:\Program Files\TimeSync`
- Add the directory to your **System PATH**
- Enable the `timesync` command globally
- Optionally configure automatic startup synchronization

---

## 💻 Usage

Open **CMD** or **PowerShell** and use:

| Command | Description |
|----------|------------|
| `timesync now` | Sync time immediately (Manual mode) |
| `timesync now --auto` | Used internally for background startup sync |
| `timesync status` | Check Admin rights, PATH status, and Startup task |
| `timesync startup enable` | Enable auto-sync at every Windows login |
| `timesync startup disable` | Disable startup auto-sync |
| `timesync about` | View version and author information |
| `timesync uninstall` | Completely remove the app and clean Registry/PATH |

---

## 🛠 How It Works

TimeSync does not simply "change the time".

It executes a controlled sequence of official Windows commands:

### 1️⃣ Service Configuration
Sets the Windows Time Service (`w32time`) to start automatically.

### 2️⃣ Service Reset
Stops and restarts the time service to ensure a clean state.

### 3️⃣ NTP Peer Configuration
Configures reliable official time servers:

- `time.google.com`
- `pool.ntp.org`
- `time.windows.com`

### 4️⃣ Forced Resync
Triggers an immediate hardware clock update using: `w32tm /resync`

---

## 🔒 Safety & Transparency

- 🛑 **No permanent background process**  
  The app runs, syncs, and exits. No memory waste.

- 🧰 **Official Windows Methods Only**  
  Uses:
  - `sc`
  - `net`
  - `w32tm`
  - Windows Task Scheduler

- 🔐 **Privacy First**  
  No telemetry  
  No tracking  
  No data collection  
  No external servers (except standard NTP time servers)

---

## 🎯 Ideal For

- Dual-boot users (Windows + Linux)
- Systems with CMOS battery issues
- Users experiencing Windows time drift
- Developers who switch OS frequently
- Anyone who wants automatic, reliable time correction

---

## 👤 Author

Omar Anoss  

---

⭐ If this project helped you, consider starring the repository.
