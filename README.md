<p align="right">
    <img height="65" src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" />
</p>

# Windows Time Auto-Synchronizer 🕒

A Python-based utility designed to fix Windows clock desynchronization issues automatically. This tool ensures your system time stays accurate by syncing with global NTP servers and persisting itself in the Windows Startup directory.

## ✨ Features
* **Automatic Admin Elevation:** Automatically detects and requests Administrator privileges required for system time modification.
* **Persistent Sync:** Copies itself to the Windows Startup folder (`AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`) to run every time you log in.
* **Service Management:** Configures the `w32time` service to start automatically and forces a restart of the service to clear errors.
* **Reliable Time Sources:** Forces synchronization using Google's NTP servers (`time.google.com`) and `pool.ntp.org`.

---

## 🛠️ How It Works
1.  **Check Permissions:** Uses `ctypes` to verify if the script is running as Admin. If not, it triggers a UAC prompt.
2.  **Self-Installation:** Checks if the executable/script is already in the Startup folder. If not, it copies itself there using `shutil`.
3.  **Time Sync Logic:**
    * Sets `w32time` service to `auto`.
    * Resets the Windows Time service.
    * Configures manual peer lists.
    * Triggers an immediate `/resync` command.

---

## 📋 Requirements
- OS: Windows 10 / 11
- Permissions: Administrative privileges (requested automatically)

---

## 🚀 Usage

### Running the Script
Ensure you have Python installed, then run:
```bash
python sync_time.py
```
