import sys
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def relaunch_as_admin():
    if is_admin():
        return

    print("💡 Tip: Run Terminal in Administrator mode for the best experience! 💻")
    
    # Prepare the executable path and arguments correctly.
    executable = sys.executable
    if getattr(sys, "frozen", False):
        args = sys.argv[1:]
    else:
        args = sys.argv
    
    params = " ".join([f'"{arg}"' for arg in args])
    
    # Relaunch with administrator privileges.
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, params, None, 1
    )
    sys.exit(0)
