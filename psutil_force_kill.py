#!/usr/bin/env python3
"""
Advanced script to forcefully terminate Jarvis processes using psutil library.
This can handle zombie processes and process trees effectively.
"""
import os
import sys
import time
import signal
import subprocess
import psutil

def find_jarvis_processes():
    """Find all processes related to Jarvis application."""
    jarvis_procs = []
    
    # Find by process name pattern
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
        try:
            # Check for processes with 'jarvis' or 'start_desktop.py' in their cmdline
            cmdline = ' '.join(proc.info['cmdline'] or []).lower()
            if 'start_desktop.py' in cmdline or 'jarvis' in cmdline:
                jarvis_procs.append(proc)
                
            # Also check process name for Python processes that might be related
            if proc.info['name'] == 'Python' and (proc.status() == psutil.STATUS_ZOMBIE or
                                                 any('jarvis' in arg.lower() for arg in (proc.cmdline() or []))):
                jarvis_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return jarvis_procs

def get_process_details(proc):
    """Get detailed information about a process."""
    try:
        info = proc.as_dict(attrs=[
            'pid', 'name', 'status', 'create_time', 'cpu_percent', 
            'memory_percent', 'cmdline', 'ppid', 'username'
        ])
        
        # Format create time
        ctime = time.strftime('%Y-%m-%d %H:%M:%S', 
                             time.localtime(info['create_time'])) if info['create_time'] else 'Unknown'
        
        # Convert cmdline to string
        cmdline = ' '.join(info['cmdline'] or [])
        
        # Get parent process info
        try:
            parent = psutil.Process(info['ppid'])
            parent_name = parent.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            parent_name = "Unknown"
        
        return {
            'pid': info['pid'],
            'name': info['name'],
            'status': info['status'],
            'created': ctime,
            'cpu_percent': info['cpu_percent'],
            'memory_percent': info['memory_percent'],
            'cmdline': cmdline,
            'ppid': info['ppid'],
            'parent_name': parent_name,
            'username': info['username']
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return {'pid': proc.pid, 'status': 'Access Denied or No Longer Exists'}

def kill_process_tree(pid, sig=signal.SIGKILL, include_parent=True, timeout=5):
    """Kill a process tree (including parent and all children) with the specified signal."""
    try:
        parent = psutil.Process(pid)
        print(f"Attempting to kill process tree of PID {pid} ({parent.name()})...")
        
        # Get children first
        children = parent.children(recursive=True)
        if include_parent:
            children.append(parent)
        
        # First send SIGTERM
        for p in children:
            try:
                print(f"Sending SIGTERM to {p.pid} ({p.name()})")
                p.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # Wait for processes to terminate
        gone, alive = psutil.wait_procs(children, timeout=timeout)
        print(f"{len(gone)} processes terminated with SIGTERM")
        
        # If any remain, use SIGKILL
        if alive:
            print(f"{len(alive)} processes still alive, using SIGKILL...")
            for p in alive:
                try:
                    print(f"Sending SIGKILL to {p.pid} ({p.name()})")
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Wait again
            gone2, alive2 = psutil.wait_procs(alive, timeout=timeout)
            print(f"{len(gone2)} additional processes terminated with SIGKILL")
            
            if alive2:
                print(f"WARNING: {len(alive2)} processes still alive!")
                return False
        
        return True
    
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"Error terminating process tree {pid}: {e}")
        return False

def handle_zombie_process(pid):
    """Special handling for zombie processes."""
    print(f"Handling zombie process PID {pid}...")
    
    try:
        # Get the parent process
        process = psutil.Process(pid)
        if process.status() == psutil.STATUS_ZOMBIE:
            parent_pid = process.ppid()
            print(f"Found zombie process {pid} with parent PID {parent_pid}")
            
            # Try to signal the parent to reap its zombie children
            if parent_pid and parent_pid != 1:  # Skip if parent is init
                try:
                    parent = psutil.Process(parent_pid)
                    print(f"Sending SIGCHLD to parent process {parent_pid} ({parent.name()})")
                    parent.send_signal(signal.SIGCHLD)
                    time.sleep(1)  # Give it time to reap zombies
                    
                    # Check if zombie is still there
                    if not psutil.pid_exists(pid) or psutil.Process(pid).status() != psutil.STATUS_ZOMBIE:
                        print(f"Zombie process {pid} has been reaped!")
                        return True
                except psutil.NoSuchProcess:
                    print(f"Parent process {parent_pid} no longer exists")
                    return False
            
            # If that didn't work, try more aggressive approaches
            print(f"Attempting to forcefully terminate the zombie process {pid}")
            try:
                # Try with sudo
                subprocess.run(["sudo", "kill", "-9", str(pid)], check=False)
                time.sleep(1)
                
                # Use sysctl if available (macOS)
                if sys.platform == 'darwin':
                    subprocess.run(["sudo", "sysctl", f"debug.zombproc.pid={pid}"], check=False)
                
                return not (psutil.pid_exists(pid) and 
                           psutil.Process(pid).status() == psutil.STATUS_ZOMBIE)
            except subprocess.SubprocessError as e:
                print(f"Error running subprocess: {e}")
                return False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        print(f"Process {pid} no longer exists or access denied")
        return False
    
    return False

def main():
    """Main function to find and kill Jarvis processes."""
    print(f"Jarvis Force Kill Utility (running as PID {os.getpid()})")
    print("Searching for Jarvis-related processes...")
    
    # Find Jarvis processes
    jarvis_procs = find_jarvis_processes()
    
    if not jarvis_procs:
        print("No Jarvis processes found.")
        return
    
    print(f"Found {len(jarvis_procs)} Jarvis-related processes:")
    
    # Print detailed information about each process
    for i, proc in enumerate(jarvis_procs, 1):
        try:
            details = get_process_details(proc)
            print(f"\n{i}. Process: {details.get('name', 'Unknown')} (PID: {details.get('pid', 'Unknown')})")
            print(f"   Status: {details.get('status', 'Unknown')}")
            print(f"   Command: {details.get('cmdline', 'Unknown')}")
            print(f"   Parent: {details.get('parent_name', 'Unknown')} (PID: {details.get('ppid', 'Unknown')})")
            print(f"   User: {details.get('username', 'Unknown')}")
            print(f"   Created: {details.get('created', 'Unknown')}")
            print(f"   CPU: {details.get('cpu_percent', 'Unknown')}%, Memory: {details.get('memory_percent', 'Unknown')}%")
        except Exception as e:
            print(f"{i}. Process {proc.pid}: Error getting details - {e}")
    
    print("\nAttempting to terminate all Jarvis processes...")
    
    # First attempt: Kill parent processes and their children
    for proc in jarvis_procs:
        try:
            if proc.status() == psutil.STATUS_ZOMBIE:
                print(f"\nDetected zombie process PID {proc.pid}")
                handle_zombie_process(proc.pid)
            else:
                kill_process_tree(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"Error with process {proc.pid}: {e}")
    
    # Check if any processes remain
    time.sleep(2)
    remaining = find_jarvis_processes()
    
    if not remaining:
        print("\nAll Jarvis processes have been terminated successfully!")
    else:
        print(f"\nWARNING: {len(remaining)} Jarvis processes are still running!")
        print("These processes may be zombies or protected. You might need to restart your system.")
        
        # Try one last approach for zombies
        for proc in remaining:
            try:
                if proc.status() == psutil.STATUS_ZOMBIE:
                    print(f"Last attempt to handle zombie PID {proc.pid}...")
                    handle_zombie_process(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Final check
        final_check = find_jarvis_processes()
        if not final_check:
            print("\nAll Jarvis processes have been terminated successfully after final attempt!")
        else:
            print(f"\nUnable to terminate {len(final_check)} Jarvis processes. System restart recommended.")

if __name__ == "__main__":
    main() 