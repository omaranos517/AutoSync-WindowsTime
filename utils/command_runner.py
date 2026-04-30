import subprocess

def run_cmd(cmd, silent=True):
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        capture_output=silent,
        creationflags=subprocess.CREATE_NO_WINDOW if silent else 0
    )
