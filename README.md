# Automation Framework for Android Testing

A production-ready framework with a GUI for automating Android application testing across multiple accounts and emulator types.

## Features

- **GUI Front-End:** A user-friendly graphical interface built with `tkinter`.
- **Parallel Execution:** Runs automation tasks concurrently on a pre-configured pool of devices.
- **Multi-Emulator Support:** Works with both standard Android SDK emulators and BlueStacks.
- **Configurable Automation:** Define UI interaction steps (clicks, waits) in a JSON configuration file.
- **HTML Reporting:** Generates a sleek, professional HTML report after each run summarizing the results.
- **Robust Logging:** All actions are logged to `automation.log` for easy debugging.
- **Failure Screenshots:** Automatically takes a screenshot when a UI automation task fails.

## Getting Started

These instructions are for developers who want to run the project from the source code.

### Prerequisites

- Python 3.8+
- Android SDK installed and configured with the `ANDROID_HOME` environment variable.
- At least one Android Emulator created in Android Studio.
- (Optional) BlueStacks 5 installed.
- One or more running Appium servers. For parallel execution, you need one Appium server per device, each running on a different port.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Use

1.  **Run the GUI:**
    ```bash
    python gui.py
    ```

2.  **Configure Settings:**
    - Use the GUI to set the path to your Android SDK and, if applicable, your BlueStacks executable and instance name.
    - Click "Save Config".

3.  **Configure Workers:**
    - Open `config.json` and populate the `parallel_workers` list. Each entry requires:
        - `device_id`: The ID of the running emulator (e.g., `emulator-5554`). Get this from the `adb devices` command.
        - `appium_port`: The port of the Appium server assigned to that device.

4.  **Add Accounts:**
    - Open `accounts.csv` and add the Google accounts you want to test with, one per line, in the format `email,password,group_link`.

5.  **Run Automation:**
    - Click the "Run Automation" button in the GUI.
    - Monitor the logs in the GUI's text area.

6.  **View Report:**
    - Once the run is finished, click the "View Last Report" button to open the `report.html` file in your browser.

## Configuration Reference (`config.json`)

- `android_sdk_path`: **(Required)** Absolute path to your Android SDK installation.
- `accounts_file`: Path to your accounts CSV file (default: `accounts.csv`).
- `app_apk_path`: Path to the `.apk` file you intend to test (currently a placeholder).
- `emulator_type`: Not used in parallel mode. Kept for legacy purposes.
- `bluestacks_adb_port`: Not used in parallel mode.
- `bluestacks_exe_path`: Not used in parallel mode.
- `bluestacks_instance_name`: Not used in parallel mode.
- `parallel_workers`: **(Required)** A list of worker configurations for parallel execution.
- `automation_steps`: A list of actions to perform within your app after it's installed.

## Troubleshooting

- **`adb.exe` not found:** Ensure your `android_sdk_path` is set correctly in the GUI and that the `platform-tools` directory exists.
- **Appium Connection Error:** Make sure your Appium servers are running on the ports defined in `parallel_workers`.
- **Emulator not found:** Ensure your emulators are running *before* starting the automation and that their `device_id`s match the configuration.