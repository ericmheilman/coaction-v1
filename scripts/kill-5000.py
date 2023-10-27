import psutil

def terminate_processes_on_port(port):
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'cmdline' in process.info and len(process.info['cmdline']) > 1:
            # Check if the process has the specified port in its command line
            if f":{port}" in process.info['cmdline'][1]:
                print(f"Terminating process: {process.info['pid']} - {process.info['name']}")
                try:
                    process.terminate()
                except psutil.NoSuchProcess:
                    print(f"Process {process.info['pid']} no longer exists.")
                except psutil.AccessDenied:
                    print(f"Access denied to terminate process {process.info['pid']}.")
            else:
                print(f"Skipping process: {process.info['pid']} - {process.info['name']}")

if __name__ == "__main__":
    port_to_kill = 5000
    terminate_processes_on_port(port_to_kill)

