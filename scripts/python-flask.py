import subprocess

def stop_flask_app_services():
    try:
        subprocess.run(['sudo', 'systemctl', 'stop', 'flask_app.service'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop flask_app.service: {e}")

def start_flask_app_services():
    try:
        subprocess.run(['sudo', 'systemctl', 'start', 'flask_app.service'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to start flask_app.service: {e}")

if __name__ == '__main__':
    # Stop the flask_app.service
    stop_flask_app_services()

    # Start the flask_app.service
    start_flask_app_services()

