import subprocess
import ctypes
import os
import sys
import shutil
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relaunch_as_admin():
    params = " ".join(sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        None,
        1
    )
    sys.exit(0)


def startup_folder():
    return Path(os.getenv("APPDATA")) / \
        "Microsoft" / "Windows" / \
        "Start Menu" / "Programs" / "Startup"


def check_the_path():
    if getattr(sys, "frozen", False):
        path = sys.executable   # exe
    else:
        path = __file__         # py

    script_path = Path(path).resolve()
    startup = startup_folder()
    startup_script = startup / script_path.name

    # not admin → request admin
    if not is_admin():
        relaunch_as_admin()

    # check location
    if startup in script_path.parents:
        print("✅ Already running from startup folder.")
        return

    print("📂 Copying full script to startup folder...")

    shutil.copy2(script_path, startup_script)

    print("✅ Full copy completed:")
    print(startup_script)

    print("🔁 Will auto-run on next login.")

def sync_windows_time():
    try:
        print("Syncing Windows time...")

        # 1. التأكد من تفعيل الخدمة وضبطها تلقائياً
        subprocess.run("sc config w32time start= auto", shell=True, check=True)
        
        # 2. إعادة تشغيل الخدمة
        subprocess.run("net stop w32time", shell=True, capture_output=True)
        subprocess.run("net start w32time", shell=True, check=True)

        # 3. تحديث قائمة السيرفرات وإجبار المزامنة
        # نستخدم سيرفرات جوجل أو مايكروسوفت لضمان الاستجابة
        subprocess.run("w32tm /config /manualpeerlist:\"time.google.com,0x1 pool.ntp.org,0x1\" /syncfromflags:manual /update", shell=True, check=True)
        
        # 4. المزامنة الفعلية
        result = subprocess.run("w32tm /resync", shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Time synchronized successfully.")
        else:
            print(f"\n❌ Error during synchronization: {result.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to execute commands: {e}")

if __name__ == "__main__":
    check_the_path()
    sync_windows_time()
