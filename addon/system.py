# Erkennt schwache Hardware, damit das Theme dort auf teure Effekte (Unschärfe, große
# Schatten) verzichtet. Läuft einmal beim Start; jede Prüfung ist billig und darf scheitern.
import glob
import os
import subprocess
import sys


def _ram_gb():
    try:
        if sys.platform.startswith("linux"):
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) / 1024 / 1024
        if sys.platform == "darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=2).stdout
            return int(out) / 1024 ** 3
        if sys.platform == "win32":
            import ctypes

            class MemStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MemStatus()
            st.dwLength = ctypes.sizeof(MemStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return st.ullTotalPhys / 1024 ** 3
    except Exception:
        pass
    return None


def _on_battery():
    try:
        if sys.platform.startswith("linux"):
            for bat in glob.glob("/sys/class/power_supply/BAT*/status"):
                with open(bat) as f:
                    if f.read().strip() == "Discharging":
                        return True
        elif sys.platform == "win32":
            import ctypes

            class PowerStatus(ctypes.Structure):
                _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                            ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                            ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]
            st = PowerStatus()
            ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(st))
            return st.ACLineStatus == 0
        elif sys.platform == "darwin":
            out = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=2).stdout
            return "Battery Power" in out
    except Exception:
        pass
    return False


def hardware_report(mw):
    """Fakten zur Hardware und ob sie als schwach gilt. Schwach = Software-Rendering,
    höchstens 4 CPU-Threads, unter 6 GB RAM oder Betrieb auf Akku."""
    info = {"software": False, "threads": os.cpu_count() or 0, "ram": _ram_gb(), "battery": _on_battery()}
    try:
        info["software"] = mw.pm.video_driver().value == "software"
    except Exception:
        pass
    info["weak"] = bool(info["software"] or 0 < info["threads"] <= 4
                        or (info["ram"] and info["ram"] < 6) or info["battery"])
    return info
