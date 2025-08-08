import subprocess

def scan_file(filepath):
    result = subprocess.run(["clamscan", filepath], capture_output=True, text=True)
    return "OK" in result.stdout