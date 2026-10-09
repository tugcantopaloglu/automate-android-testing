# Android Beta Testing Automation

An Appium-based Python CLI and Tkinter GUI for running configured Android app checks on devices or emulators that you control. Each worker processes its assigned account rows sequentially, while distinct workers can run in parallel. Results are written to `report.html` and `automation.log`, with PNG screenshots when a failed session can capture one.

## Google Play testing requirements

As of October 9, 2026, Google's [official testing requirements](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en) say that personal developer accounts created after November 13, 2023 need a closed test with at least **12 testers opted in continuously for 14 days** before applying for production access. The application also asks about tester engagement, feedback, and production readiness.

Running this program daily or leaving an app open does not establish that requirement or guarantee production access. Recruit actual testers, collect their feedback, and follow Play Console's current instructions. Use account automation only with permission from the account holders.

## Prerequisites

- Python 3.9 or newer with Tkinter if using the GUI. The [Appium Python client compatibility matrix](https://github.com/appium/python-client#compatibility-matrix) covers Appium 5.x with Selenium 4.32 to 4.46. This project requires Selenium 4.32 or newer for its public connection configuration API.
- Android SDK platform tools and an already running, authorized Android device or emulator visible in `adb devices`.
- Java, `ANDROID_HOME` or `ANDROID_SDK_ROOT`, and an Appium server with the UiAutomator2 driver installed. Follow the [UiAutomator2 requirements](https://github.com/appium/appium-uiautomator2-driver#requirements) for compatible Android and Appium server versions.
- Chrome on each device and a compatible Chromedriver configured for Appium's Chrome sessions. See [UiAutomator2 web context capabilities](https://github.com/appium/appium-uiautomator2-driver#web-context).
- An app package available to the test account on the configured device's Play Store.

Install Python dependencies in an isolated environment:

```bash
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux, then run:

```bash
python -m pip install -r requirements.txt
```

For a current Appium installation, the driver must be installed separately:

```bash
npm install -g appium
appium driver install uiautomator2
appium driver doctor uiautomator2
```

Installing the latest UiAutomator2 driver requires a compatible Appium server. Use the official driver documentation when maintaining an older server installation.

## Configure

Run from the repository directory. `config.json`, the CSV path, logs, reports, and screenshots are resolved from the current working directory.

Edit `config.json` with your app package and the device IDs shown by `adb devices`. For example:

```json
{
    "accounts_file": "accounts.local.csv",
    "wait_minutes": 10,
    "parallel_workers": [
        {"device_id": "emulator-5554", "appium_port": 4723, "system_port": 8200, "chromedriver_port": 9000},
        {"device_id": "emulator-5556", "appium_port": 4724, "system_port": 8201, "chromedriver_port": 9001}
    ],
    "automation_steps": {
        "app_package": "com.example.app",
        "actions": [
            {"type": "wait", "duration_seconds": 5},
            {"type": "scroll"},
            {"type": "click", "text": "Accept"}
        ]
    }
}
```

Every worker needs a distinct device ID and Appium server port. `system_port` and `chromedriver_port` default to `8200 + worker index` and `9000 + worker index`; you can set them explicitly when those host ports are occupied. All configured worker ports must be distinct. See [Appium's parallel testing guidance](https://github.com/appium/appium-uiautomator2-driver#parallel-tests).

Create the ignored `accounts.local.csv` with accounts you are authorized to use:

```csv
email,password,group_link,beta_link
tester@example.com,REPLACE_LOCALLY,https://groups.google.com/g/your-test-group,https://play.google.com/apps/testing/com.example.app
```

Leave `group_link` or `beta_link` empty to skip those steps. Passwords are stored in plaintext by this CSV format. Keep local credentials out of Git and protect the file, logs, reports, and screenshots, which can contain account or app information. The checked-in examples are not usable credentials.

## Run

Start the devices yourself, then start one local Appium server per worker:

```bash
appium --address 127.0.0.1 --port 4723
appium --address 127.0.0.1 --port 4724
python main.py
```

The sequence creates a native session, replaces it with a Chrome session to submit login and optional group/beta steps, requests installation, then opens a native session to verify the package is installed and run its actions. Failed required steps and native actions are recorded as failures. Sessions are closed after each account task.

For the GUI:

```bash
python gui.py
```

The GUI can edit SDK/BlueStacks path fields, validate basic paths and local Appium ports, display logs, and open the last report. The main runner does not launch emulators or connect BlueStacks automatically; the `src/emulator_manager.py` helpers are separate from the CLI workflow. The `emulator_type` setting does not enable a BlueStacks integration in `main.py`.

## Action types

| Type | Behavior | Parameters |
|------|----------|------------|
| `click` | Click a native element; a missing target fails the task | `element_id`, `xpath`, or `text` |
| `wait` | Pause within the action sequence | `duration_seconds`, default 5 |
| `scroll` | Swipe upward using the current window size | None |
| `back` | Navigate back | None |

Unknown action types fail the task. `wait_minutes` is a non-negative pause after the actions, with periodic session checks to prevent Appium's idle timeout.

## Validation and limits

Run the regression suite without devices, servers, or Google accounts:

```bash
python -m unittest discover -s tests -v
```

The suite mocks Appium sessions, account operations, and subprocess calls. It checks device targeting, worker isolation, failure reporting, cleanup, report escaping, emulator selection, and GUI completion handling. It does not verify Google login, Play Store installation, Android interaction, or a native device session.

The Google login helper submits credentials but does not confirm the authenticated identity. Group and beta helpers use English button/text heuristics and may treat a submitted request as success. MFA, CAPTCHA, consent screens, localization, changed page layouts, and retained Chrome account state can require manual intervention. A successful report means the configured helper checks completed; it is not proof of tester engagement or Google Play eligibility. Use isolated device/account state when assessing results.

The manual `Build and Release` workflow runs regression tests and builds a Windows GUI executable with PyInstaller before creating a release. It does not run on pushes. An executable still needs the external configuration and account CSV in its working directory, plus the Android/Appium prerequisites above.
