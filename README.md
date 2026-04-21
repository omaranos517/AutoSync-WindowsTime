<p align="right">
    <img height="70" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" />
</p>

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

---

## 🚀 Getting Started

### 🔧 Installation

Choose one of the following installation methods:

#### Option 1: Install from the latest release

1. Download the latest installer from [Releases](https://github.com/omaranos517/AutoSync-WindowsTime/releases/latest) (`TimeSync_<version>_Setup.exe`).
2. Run the installer as Administrator and complete the setup wizard.
3. Optional: keep **Run TimeSync at Windows startup** enabled during setup.

The installer will:

- Install TimeSync to `C:\Program Files\TimeSync`
- Add the install directory to the system `PATH`
- Register the app in Windows Apps & Features
- Optionally enable:
  - Startup sync task
  - Resume-from-sleep sync task

#### Option 2: Build from source

Follow the guide in [packaging/BUILD.md](packaging/BUILD.md).

---

## 💻 Usage

### GUI Mode

- Open **TimeSync** from the Start Menu, or run `timesync` with no arguments.
- Use the GUI to:
  - Sync immediately
  - Enable/disable Startup sync
  - Enable/disable Sync on Wake (Resume)
  - Enable/disable Notifications
  - Open the log file

### CLI Mode

Open **CMD** or **PowerShell** and use:

| Command | Description |
|----------|------------|
| `timesync help` / `timesync commands` | Show all available commands |
| `timesync now` | Sync time immediately |
| `timesync status` | Show admin, startup, resume, and notification status |
| `timesync startup status` | Check startup sync task status |
| `timesync startup enable` | Enable sync at Windows login |
| `timesync startup disable` | Disable sync at Windows login |
| `timesync resume status` | Check sync-on-wake task status |
| `timesync resume enable` | Enable sync after sleep/hibernate wake |
| `timesync resume disable` | Disable sync after sleep/hibernate wake |
| `timesync notify status` | Check notification status |
| `timesync notify enable` | Enable desktop notifications |
| `timesync notify disable` | Disable desktop notifications |
| `timesync logs` | Open the log file |
| `timesync about` | Show app information |
| `timesync version` | Show current version |

Advanced/internal commands:

- `timesync now --auto` (used by scheduled tasks)
- `timesync cancel`
- `timesync disable-warning`

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
