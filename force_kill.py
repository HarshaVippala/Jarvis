#!/usr/bin/env python3
"""
Last resort script to force kill a stubborn process using lldb on macOS.
This script will create an lldb script to attach to and terminate the process.
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

def find_jarvis_processes():
    """Find all Jarvis-related processes."""
    try:
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

def kill_with_lldb(pid):
    """Use lldb to forcefully terminate a process."""
    # Create a temporary file with lldb commands
    fd, temp_path = tempfile.mkstemp(suffix='.lldb')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(f"process attach --pid {pid}\n")
            f.write("thread backtrace all\n")  # Get backtrace to see what it's doing
            f.write("process kill\n")  # Kill the process
            f.write("quit\n")  # Exit lldb
        
        print(f"Attempting to kill process {pid} using lldb...")
        # Execute lldb with the commands file
        result = subprocess.run(
            ["sudo", "lldb", "-s", temp_path],
            capture_output=True,
            text=True
        )
        
        print("lldb output:")
        print(result.stdout)
        
        if result.stderr:
            print("lldb errors:")
            print(result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error using lldb: {e}")
        return False
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except:
            pass

def main():
    print("WARNING: This is a last resort script to forcefully terminate Jarvis processes.")
    print("It requires sudo privileges and uses debugging tools.")
    
    pids = find_jarvis_processes()
    if not pids:
        print("No Jarvis processes found.")
        return
    
    print(f"Found {len(pids)} Jarvis processes: {pids}")
    
    for pid in pids:
        # Get process info
        try:
            cmd = ["ps", "-p", str(pid), "-o", "pid,ppid,user,%cpu,%mem,command"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Process details:\n{result.stdout}")
        except:
            pass
        
        # First try regular kill
        try:
            print(f"Attempting regular kill -9 on PID {pid}...")
            subprocess.run(["sudo", "kill", "-9", str(pid)])
        except:
            pass
        
        # Wait a bit to see if it worked
        time.sleep(1)
        
        # Check if process is still running
        if pid not in find_jarvis_processes():
            print(f"Process {pid} terminated successfully!")
            continue
            
        # If regular kill fails, use lldb
        print(f"Process {pid} is still running. Attempting to use lldb...")
        success = kill_with_lldb(pid)
        
        if success:
            print(f"Successfully terminated process {pid} with lldb.")
        else:
            print(f"Failed to terminate process {pid} even with lldb.")
            print("You may need to restart your computer.")

if __name__ == "__main__":
    main() 