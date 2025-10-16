#!/usr/bin/env python

"""Main entry point for the Android automation framework."""

import csv
import os
import time

from src.config_reader import read_config
from src.emulator_manager import list_emulators, start_emulator, stop_emulator, connect_to_bluestacks, disconnect_from_bluestacks, get_running_devices, start_bluestacks
from src.automation_manager import get_appium_driver, run_automation

import logging
from src.logger_setup import setup_logger

def main():
    """Main function to orchestrate the automation process."""
    setup_logger()
    logging.info("--- Starting Automation Framework ---")

    # 1. Read configuration
    config = read_config()
    sdk_path = os.path.expandvars(config.get('android_sdk_path'))
    accounts_file = config.get('accounts_file')

    # 2. Read accounts from CSV
    try:
        with open(accounts_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            accounts = list(reader)
    except FileNotFoundError:
        logging.error(f"Accounts file not found at '{accounts_file}'. Please check your config.json.")
        return

    if not accounts:
        logging.warning("No accounts found in the accounts file. Exiting.")
        return

    logging.info(f"Found {len(accounts)} accounts to process.")

    emulator_type = config.get('emulator_type', 'sdk')

    # 4. Loop through each account and run the automation
    for i, account in enumerate(accounts):
        email = account.get('email')
        password = account.get('password')
        group_link = account.get('group_link')
        beta_link = 'https://play.google.com/apps/testing/your.app.package' # Placeholder

        logging.info(f"\n--- Processing Account {i+1}/{len(accounts)}: {email} ---")

        device_id = None
        driver = None

        try:
            # --- Workflow for different emulator types ---
            if emulator_type == 'sdk':
                # Get available emulator
                emulators = list_emulators(sdk_path)
                if not emulators:
                    raise RuntimeError("No SDK emulators found.")
                emulator_name = emulators[0]

                # Dynamically detect the new emulator instance
                devices_before = get_running_devices(sdk_path)
                logging.info(f"Running devices before start: {devices_before}")
                if not start_emulator(sdk_path, emulator_name):
                    raise RuntimeError("Failed to start SDK emulator.")
                
                logging.info("Waiting for 30 seconds for emulator to appear in adb...")
                time.sleep(30)
                devices_after = get_running_devices(sdk_path)
                logging.info(f"Running devices after start: {devices_after}")
                device_id = next(iter(set(devices_after) - set(devices_before)), None)
                if not device_id:
                    raise RuntimeError("Failed to detect new SDK emulator device ID.")

            elif emulator_type == 'bluestacks':
                # Check for auto-start config
                exe_path = config.get('bluestacks_exe_path')
                instance_name = config.get('bluestacks_instance_name')

                if exe_path and instance_name:
                    if not start_bluestacks(exe_path, instance_name):
                        raise RuntimeError("Failed to issue BlueStacks start command.")
                    logging.info("Waiting 45 seconds for BlueStacks to start before connecting...")
                    time.sleep(45)

                port = config.get('bluestacks_adb_port', 5555)
                device_id = connect_to_bluestacks(sdk_path, port)
                if not device_id:
                    raise RuntimeError(f"Failed to connect to BlueStacks on port {port}. Is it running?")
            
            else:
                raise ValueError(f"Unsupported emulator_type in config: {emulator_type}")

            # --- Common workflow for all emulator types ---
            logging.info(f"Detected device ID: {device_id}")
            logging.info("Waiting 30 seconds for device to be ready...")
            time.sleep(30)

            driver = get_appium_driver(device_id)
            if not driver:
                raise RuntimeError("Failed to get Appium driver. Is the Appium server running?")

            run_automation(driver, email, password, group_link, beta_link, config)

        except Exception as e:
            logging.error(f"An error occurred while processing account {email}: {e}")
            logging.warning("Skipping to the next account.")
        finally:
            # --- Cleanup for different emulator types ---
            if driver:
                driver.quit()
            
            if emulator_type == 'sdk' and 'emulator_name' in locals():
                stop_emulator(sdk_path, emulator_name)
            elif emulator_type == 'bluestacks' and 'port' in locals():
                disconnect_from_bluestacks(sdk_path, port)
            
            logging.info("Waiting 15 seconds for cleanup...")
            time.sleep(15)

    logging.info("\n--- All Accounts Processed. Automation Finished. ---")

if __name__ == '__main__':
    main()
