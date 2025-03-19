#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time

def find_jarvis_processes():
    """Find all Jarvis-related processes."""
    try:
        # Get list of all Python processes running start_desktop.py
        result = subprocess.run(
            ["pgrep", "-f", "start_desktop.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            return [int(pid) for pid in result.stdout.strip().split('\n') if pid]
        return []
    except Exception as e:
        print(f"Error finding processes: {e}")
        return []

def get_process_info(pid):
    """Get more detailed information about a process."""
    try:
        cmd = ["ps", "-p", str(pid), "-o", "pid,ppid,user,%cpu,%mem,command"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        return f"Unable to get process info for PID {pid}"
    except Exception as e:
        return f"Error getting process info: {e}"

def kill_processes(pids, force=False):
    """Kill processes with the given PIDs."""
    sig = signal.SIGKILL if force else signal.SIGTERM
    
    for pid in pids:
        try:
            print(f"Attempting to kill process {pid}...")
            print(f"Process details:\n{get_process_info(pid)}")
            os.kill(pid, sig)
            print(f"Signal {'SIGKILL' if force else 'SIGTERM'} sent to process {pid}")
        except ProcessLookupError:
            print(f"Process {pid} not found.")
        except PermissionError:
            print(f"Permission denied when trying to kill {pid}. Trying with sudo...")
            try:
                subprocess.run(["sudo", "kill", "-9" if force else "-15", str(pid)])
                print(f"Sudo kill command executed for {pid}")
            except Exception as e:
                print(f"Failed to kill with sudo: {e}")
        except Exception as e:
            print(f"Error killing process {pid}: {e}")

def main():
    print(f"Shutting down Jarvis application... (This script running as PID {os.getpid()})")
    
    # Find jarvis processes
    pids = find_jarvis_processes()
    
    if not pids:
        print("No Jarvis processes found running.")
        return
    
    print(f"Found {len(pids)} Jarvis processes: {pids}")
    
    # Try graceful shutdown first
    print("Attempting graceful shutdown with SIGTERM...")
    kill_processes(pids, force=False)
    
    # Wait a bit and check if processes are still running
    print("Waiting to see if processes terminate...")
    time.sleep(2)
    remaining_pids = find_jarvis_processes()
    
    if remaining_pids:
        print(f"Some processes still running: {remaining_pids}")
        print("Forcing termination with SIGKILL...")
        kill_processes(remaining_pids, force=True)
        
        # Final check
        time.sleep(1)
        final_check = find_jarvis_processes()
        if final_check:
            print(f"WARNING: Unable to terminate some processes: {final_check}")
            
            # Extra debug information
            print("\nProcess details for resistant processes:")
            for pid in final_check:
                details = get_process_info(pid)
                print(details)
                
            print("\nTrying additional methods to terminate...")
            for pid in final_check:
                print(f"Attempting to kill process tree for PID {pid}...")
                try:
                    # Try killing the entire process group
                    subprocess.run(["sudo", "pkill", "-9", "-g", str(pid)])
                    print("Process group kill attempted")
                except Exception as e:
                    print(f"Error killing process group: {e}")
            
            print("\nYou may need to restart your computer or use Activity Monitor to force quit.")
        else:
            print("All Jarvis processes terminated successfully.")
    else:
        print("All Jarvis processes terminated successfully.")

if __name__ == "__main__":
    main() 