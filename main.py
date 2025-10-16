#!/usr/bin/env python

"""Main entry point for the Android automation framework."""

import csv
import os
import time

from src.config_reader import read_config
from src.emulator_manager import list_emulators, start_emulator, stop_emulator
from src.automation_manager import get_appium_driver, run_automation

def main():
    """Main function to orchestrate the automation process."""
    print("--- Starting Automation Framework ---")

    # 1. Read configuration
    config = read_config()
    sdk_path = os.path.expandvars(config.get('android_sdk_path')) # Expands env vars like %LOCALAPPDATA%
    accounts_file = config.get('accounts_file')

    # 2. Read accounts from CSV
    try:
        with open(accounts_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            accounts = list(reader)
    except FileNotFoundError:
        print(f"Error: Accounts file not found at '{accounts_file}'. Please check your config.json.")
        return

    if not accounts:
        print("No accounts found in the accounts file. Exiting.")
        return

    print(f"Found {len(accounts)} accounts to process.")

    # 3. Get available emulator
    # For simplicity, we use the first available emulator.
    emulators = list_emulators(sdk_path)
    if not emulators:
        print("No emulators found. Please create an emulator in Android Studio.")
        return
    emulator_name = emulators[0]
    emulator_device_id = 'emulator-5554' # This is a common default, but can change.

    # 4. Loop through each account and run the automation
    for i, account in enumerate(accounts):
        email = account.get('email')
        password = account.get('password')
        group_link = account.get('group_link')
        # A beta link could also be in the CSV per account
        beta_link = 'https://play.google.com/apps/testing/your.app.package' # Placeholder

        print(f"\n--- Processing Account {i+1}/{len(accounts)}: {email} ---")

        try:
            # Start the emulator
            if not start_emulator(sdk_path, emulator_name):
                raise RuntimeError("Failed to start emulator.")
            
            print("Waiting 60 seconds for emulator to fully boot...")
            time.sleep(60)

            # Get Appium driver
            driver = get_appium_driver(emulator_device_id)
            if not driver:
                raise RuntimeError("Failed to get Appium driver. Is the Appium server running?")

            # Run the automation steps
            run_automation(driver, email, password, group_link, beta_link)

        except Exception as e:
            print(f"An error occurred while processing account {email}: {e}")
            print("Skipping to the next account.")
        finally:
            # Stop the emulator
            stop_emulator(sdk_path, emulator_name)
            print("Waiting 30 seconds for emulator to shut down completely...")
            time.sleep(30)

    print("\n--- All Accounts Processed. Automation Finished. ---")

if __name__ == '__main__':
    main()
