import subprocess
import os
import logging

def get_emulator_path(sdk_path):
    """Gets the path to the emulator executable."""
    return os.path.join(sdk_path, 'emulator', 'emulator')

def list_emulators(sdk_path):
    """Lists all available Android emulators."""
    emulator_path = get_emulator_path(sdk_path)
    try:
        result = subprocess.run([emulator_path, '-list-avds'], capture_output=True, text=True, check=True)
        emulators = result.stdout.strip().split('\n')
        logging.info(f"Available emulators: {emulators}")
        return emulators
    except FileNotFoundError:
        logging.error(f"'emulator.exe' not found at {emulator_path}. Please check your Android SDK path in config.json.")
        return []
    except subprocess.CalledProcessError as e:
        logging.error(f"Error listing emulators: {e.stderr}")
        return []

def get_adb_path(sdk_path):
    """Gets the path to the adb executable."""
    return os.path.join(sdk_path, 'platform-tools', 'adb')

def start_emulator(sdk_path, emulator_name):
    """Starts a given Android emulator."""
    emulator_path = get_emulator_path(sdk_path)
    logging.info(f"Starting emulator: {emulator_name}...")
    try:
        subprocess.Popen([emulator_path, '-avd', emulator_name, '-no-snapshot-load'])
        logging.info(f"Emulator {emulator_name} is starting.")
        return True
    except FileNotFoundError:
        logging.error(f"'emulator.exe' not found at {emulator_path}.")
        return False

def get_running_devices(sdk_path):
    """Returns a list of running emulator device IDs."""
    adb_path = get_adb_path(sdk_path)
    try:
        result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, check=True)
        devices = result.stdout.strip().split('\n')[1:]
        device_ids = [line.split('\t')[0] for line in devices if 'emulator' in line]
        return device_ids
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error getting running devices: {e}")
        return []

def stop_emulator(sdk_path, emulator_name):
    """Stops a running Android emulator."""
    logging.info(f"Stopping emulator: {emulator_name}...")
    try:
        device_to_stop = next(iter(get_running_devices(sdk_path)), None)
        if device_to_stop:
            adb_path = get_adb_path(sdk_path)
            subprocess.run([adb_path, '-s', device_to_stop, 'emu', 'kill'], check=True)
            logging.info(f"Emulator {emulator_name} ({device_to_stop}) stopped.")
            return True
        else:
            logging.warning("No running emulator found to stop.")
            return False
    except Exception as e:
        logging.error(f"Error stopping emulator: {e}")
        return False

def start_bluestacks(exe_path, instance_name):
    """Starts a specific BlueStacks instance from its executable path."""
    logging.info(f"Attempting to start BlueStacks instance '{instance_name}'...")
    try:
        command = [exe_path, '--instance', instance_name]
        subprocess.Popen(command)
        logging.info("BlueStacks start command issued.")
        return True
    except FileNotFoundError:
        logging.error(f"BlueStacks executable not found at '{exe_path}'. Please check your config.json.")
        return False
    except Exception as e:
        logging.error(f"An error occurred while trying to start BlueStacks: {e}")
        return False

def connect_to_bluestacks(sdk_path, port):
    """Connects ADB to a BlueStacks instance running on a specific port."""
    adb_path = get_adb_path(sdk_path)
    device_id = f"localhost:{port}"
    logging.info(f"Attempting to connect to BlueStacks at {device_id}...")
    try:
        result = subprocess.run([adb_path, 'connect', device_id], capture_output=True, text=True, check=True)
        if "connected" in result.stdout:
            logging.info(f"Successfully connected to BlueStacks: {device_id}")
            return device_id
        else:
            logging.error(f"Failed to connect to BlueStacks. Response: {result.stdout}")
            return None
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error connecting to BlueStacks: {e}")
        return None

def disconnect_from_bluestacks(sdk_path, port):
    """Disconnects ADB from a BlueStacks instance."""
    adb_path = get_adb_path(sdk_path)
    device_id = f"localhost:{port}"
    logging.info(f"Disconnecting from BlueStacks at {device_id}...")
    try:
        subprocess.run([adb_path, 'disconnect', device_id], check=True)
        logging.info(f"Successfully disconnected from {device_id}")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Error disconnecting from BlueStacks: {e}")
        return False

if __name__ == '__main__':
    from logger_setup import setup_logger
    setup_logger()
    import time
    sdk_path = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk_path:
        emulators = list_emulators(sdk_path)
        if emulators:
            emulator_to_test = emulators[0]
            start_emulator(sdk_path, emulator_to_test)
            logging.info("\nWaiting for 30 seconds for emulator to boot...")
            time.sleep(30)
            stop_emulator(sdk_path, emulator_to_test)
    else:
        logging.error("ANDROID_HOME or ANDROID_SDK_ROOT environment variable not set.")
        logging.error("Please set it to your Android SDK root directory.")
