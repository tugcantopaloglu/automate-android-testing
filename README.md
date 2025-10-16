# ✨ Android Automation Framework ✨

<p align="center">
  <img src="assets/gui_main_window.png" alt="Main GUI Window" width="700">
</p>

<p align="center">
  <b>Tired of manually running the same tests over and over for your Android apps? This tool is for you!</b>
</p>

---

This project provides a powerful, GUI-driven framework to automate the boring parts of beta testing. It's designed to be easy to use, configurable, and scalable, whether you're a solo developer or part of a larger team.

## 🤔 So, What Can It Do?

This isn't just a simple script. It's a full application built to make your life easier. Here's what's under the hood:

- **🖥️ Sleek GUI:** No more command-line hassles. Manage and run everything from a simple, intuitive user interface.
- **⚡ Parallel Testing:** Run tests on multiple devices at the same time to get through your accounts list in record time.
- **⚙️ Multi-Emulator Support:** Works with standard Android SDK emulators and BlueStacks.
- **📊 Professional HTML Reports:** Get a clean, beautiful report after every run showing what passed, what failed, and why.

  <img src="assets/html_report_sample.png" alt="HTML Report Sample" width="700">

- **📸 Automatic Failure Screenshots:** When something goes wrong, the tool automatically saves a screenshot, so you can see exactly what happened without guessing.
- **🔧 Fully Configurable:** Define your own test steps, from simple clicks to more complex interactions, all within a JSON config file.

## 🚀 Quick Start Guide

Ready to get started? Here's how to get up and running in a few minutes.

#### 1. Prerequisites

Make sure you have these installed and ready to go:

- **Python 3.8+**
- **Android SDK:** Make sure the `ANDROID_HOME` environment variable is set.
- **Appium Server:** You'll need this to communicate with the emulators. You can install it via npm: `npm install -g appium`.
- **Your Emulators:** Have your Android SDK emulators (or BlueStacks instances) created and ready.

#### 2. Setup

Clone this repository and install the necessary Python packages.

```bash
# Clone the repo
git clone <repository_url>
cd <repository_directory>

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configuration

This is the most important part! The tool needs to know about your setup.

1.  **Start Your Emulators & Appium Servers:** Before you do anything else, make sure your emulators are running and you have one Appium server running for each emulator, each on a different port (e.g., `appium -p 4723`, `appium -p 4724`).

2.  **Run the GUI:**
    ```bash
    python gui.py
    ```

3.  **Fill out the GUI Config:**
    - Point the `android_sdk_path` to your SDK folder.
    - Click **Save Config**.
    - Click **Validate Setup** to make sure everything is configured correctly!

4.  **Edit `config.json` for Workers:**
    - Open the `config.json` file.
    - In the `parallel_workers` section, list all your running devices. You can get the `device_id` from the `adb devices` command.

    ```json
    "parallel_workers": [
        {
            "device_id": "emulator-5554",
            "appium_port": 4723
        },
        {
            "device_id": "emulator-5556",
            "appium_port": 4724
        }
    ]
    ```

5.  **Add Your Accounts:**
    - Open `accounts.csv` and add your test accounts in the `email,password,group_link` format.

#### 4. Run!

- Head back to the GUI and click the **Run Automation** button. Sit back and watch the magic happen!
- Once it's done, click **View Last Report** to see the results.

## 💡 Troubleshooting

- **Connection Errors?** Double-check that your Appium servers are running and the ports in `config.json` match.
- **Device Not Found?** Make sure your emulators are fully booted before you run the automation and that the `device_id`s are correct.
- **Validation Fails?** The log viewer in the GUI is your best friend! It will tell you exactly which check failed.

## 🤝 Contributing

Got an idea to make this even better? Feel free to open an issue or submit a pull request. All contributions are welcome!

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
