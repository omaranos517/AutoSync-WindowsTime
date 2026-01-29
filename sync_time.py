import subprocess
import ctypes
import os
import sys
import shutil
from time import sleep
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False
    
def relaunch_as_admin():
    if is_admin():
        return

    if getattr(sys, "frozen", False):
        exe = sys.executable
        params = ""
    else:
        exe = sys.executable
        params = f'"{sys.argv[0]}" ' + " ".join(f'"{a}"' for a in sys.argv[1:])

    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe, params, None, 1
    )
    sys.exit(0)

def startup_folder():
    return Path(os.getenv("APPDATA")) / "Microsoft/Windows/Start Menu/Programs/Startup"

def check_the_path():
    path = sys.executable if getattr(sys, "frozen", False) else __file__
    script_path = Path(path).resolve()
    startup = startup_folder()
    startup_script = startup / script_path.name

    # التحقق من الصلاحيات أولاً
    if not is_admin():
        relaunch_as_admin()

    if startup in script_path.parents:
        print("✅ Already running from startup folder.")
        return

    try:
        shutil.copy2(script_path, startup_script)
        print(f"✅ Copied to: {startup_script}")
    except Exception as e:
        print(f"❌ Copy failed: {e}")
        sleep(2)

def sync_windows_time():
    try:
        print("🔄 Syncing Windows time, Please wait...\n")
        subprocess.run("sc config w32time start= auto", shell=True, check=True, capture_output=True)
        subprocess.run("net stop w32time", shell=True, capture_output=True)
        subprocess.run("net start w32time", shell=True, check=True, capture_output=True)
        sleep(2)

        # المزامنة مع أكثر من سيرفر (جوجل + NTP Pool + مايكروسوفت)
        peers = "time.google.com,0x1 pool.ntp.org,0x1 time.windows.com,0x1"
        subprocess.run(f'w32tm /config /manualpeerlist:"{peers}" /syncfromflags:manual /update', shell=True, check=True)

        result = subprocess.run("w32tm /resync", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Time synchronized successfully.")
        else:
            print(f"⚠️ Sync failed: {result.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error during execution: {e}")


if __name__ == "__main__":
    check_the_path()
    sync_windows_time()
