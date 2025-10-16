import subprocess
import os

def get_emulator_path(sdk_path):
    """Gets the path to the emulator executable."""
    return os.path.join(sdk_path, 'emulator', 'emulator')

def list_emulators(sdk_path):
    """Lists all available Android emulators."""
    emulator_path = get_emulator_path(sdk_path)
    try:
        result = subprocess.run([emulator_path, '-list-avds'], capture_output=True, text=True, check=True)
        emulators = result.stdout.strip().split('\n')
        print(f"Available emulators: {emulators}")
        return emulators
    except FileNotFoundError:
        print(f"Error: 'emulator.exe' not found at {emulator_path}. Please check your Android SDK path in config.json.")
        return []
    except subprocess.CalledProcessError as e:
        print(f"Error listing emulators: {e.stderr}")
        return []

def get_adb_path(sdk_path):
    """Gets the path to the adb executable."""
    return os.path.join(sdk_path, 'platform-tools', 'adb')

def start_emulator(sdk_path, emulator_name):
    """Starts a given Android emulator."""
    emulator_path = get_emulator_path(sdk_path)
    print(f"Starting emulator: {emulator_name}...")
    try:
        # Using Popen for non-blocking start
        subprocess.Popen([emulator_path, '-avd', emulator_name, '-no-snapshot-load'])
        print(f"Emulator {emulator_name} is starting.")
        # We need to wait for the emulator to boot. This will be handled in the main script.
        return True
    except FileNotFoundError:
        print(f"Error: 'emulator.exe' not found at {emulator_path}.")
        return False

def stop_emulator(sdk_path, emulator_name):
    """Stops a running Android emulator."""
    adb_path = get_adb_path(sdk_path)
    print(f"Stopping emulator: {emulator_name}...")
    try:
        # The device id for an emulator is usually emulator-5554, emulator-5556, etc.
        # We need to find the correct device id for the given emulator name.
        # This is a simplification. A more robust solution would map avd name to device id.
        result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, check=True)
        devices = result.stdout.strip().split('\n')[1:] # Skip the header
        emulator_device = None
        for device in devices:
            if 'emulator' in device:
                emulator_device = device.split('\t')[0]
                break # Stop at the first found emulator

        if emulator_device:
            subprocess.run([adb_path, '-s', emulator_device, 'emu', 'kill'], check=True)
            print(f"Emulator {emulator_name} ({emulator_device}) stopped.")
            return True
        else:
            print("No running emulator found to stop.")
            return False

    except FileNotFoundError:
        print(f"Error: 'adb.exe' not found at {adb_path}.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error stopping emulator: {e.stderr}")
        return False

if __name__ == '__main__':
    # This is for testing purposes.
    import time
    sdk_path = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if sdk_path:
        emulators = list_emulators(sdk_path)
        if emulators:
            emulator_to_test = emulators[0]
            start_emulator(sdk_path, emulator_to_test)
            print("\nWaiting for 30 seconds for emulator to boot...")
            time.sleep(30)
            stop_emulator(sdk_path, emulator_to_test)
    else:
        print("Error: ANDROID_HOME or ANDROID_SDK_ROOT environment variable not set.")
        print("Please set it to your Android SDK root directory.")
