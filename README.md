# Android Beta Testing Automation

Automate Google Play's closed testing requirement (20 testers for 14 days).

## Features

- Parallel testing on multiple emulators
- Google account login automation
- Google Groups join automation
- Play Store beta acceptance
- App install and interaction
- HTML reports with failure screenshots

## Setup

### Prerequisites

- Python 3.8+
- Android SDK with emulators
- Appium Server (`npm install -g appium`)
- Chrome on emulators

### Install

```bash
pip install -r requirements.txt
```

### Configure

1. Edit `config.json`:

```json
{
    "accounts_file": "accounts.csv",
    "wait_minutes": 10,
    "parallel_workers": [
        {"device_id": "emulator-5554", "appium_port": 4723},
        {"device_id": "emulator-5556", "appium_port": 4724}
    ],
    "automation_steps": {
        "app_package": "com.your.app",
        "actions": [
            {"type": "wait", "duration_seconds": 5},
            {"type": "scroll"},
            {"type": "click", "text": "Accept"}
        ]
    }
}
```

2. Add accounts to `accounts.csv`:

```csv
email,password,group_link,beta_link
user1@gmail.com,pass1,https://groups.google.com/g/mygroup,https://play.google.com/apps/testing/com.your.app
user2@gmail.com,pass2,https://groups.google.com/g/mygroup,https://play.google.com/apps/testing/com.your.app
```

### Run

1. Start emulators
2. Start Appium servers (one per emulator):
   ```bash
   appium -p 4723
   appium -p 4724
   ```
3. Run automation:
   ```bash
   python main.py
   ```

Or use the GUI:
```bash
python gui.py
```

## Action Types

| Type | Description | Parameters |
|------|-------------|------------|
| `click` | Click element | `element_id`, `xpath`, or `text` |
| `wait` | Wait | `duration_seconds` |
| `scroll` | Scroll down | - |
| `back` | Press back | - |

## Notes

- Run daily for 14 days to meet Google's requirement
- Use unique Google accounts (create with different recovery emails)
- BlueStacks supported via `emulator_type: "bluestacks"`
