#!/usr/bin/env python

"""Main entry point for the Android automation framework."""

import csv
import os
import time
import logging

from src.config_reader import read_config
from src.emulator_manager import (
    list_emulators, start_emulator, stop_emulator, 
    connect_to_bluestacks, disconnect_from_bluestacks, 
    get_running_devices, start_bluestacks
)
from src.automation_manager import get_appium_driver, run_automation
from src.logger_setup import setup_logger
from src.report_generator import generate_html_report

def main():
    """Main function to orchestrate the automation process."""
    setup_logger()
    logging.info("--- Starting Automation Framework ---")

    config = read_config()
    sdk_path = os.path.expandvars(config.get('android_sdk_path'))
    accounts_file = config.get('accounts_file')

    try:
        with open(accounts_file, 'r', newline='') as f:
            accounts = list(csv.DictReader(f))
    except FileNotFoundError:
        logging.error(f"Accounts file not found at '{accounts_file}'. Please check config.json.")
        return

    if not accounts:
        logging.warning("No accounts found in accounts file. Exiting.")
        return

    logging.info(f"Found {len(accounts)} accounts to process.")
    emulator_type = config.get('emulator_type', 'sdk')
    results = []

    for i, account in enumerate(accounts):
        email = account.get('email')
        password = account.get('password')
        group_link = account.get('group_link')
        beta_link = 'https://play.google.com/apps/testing/your.app.package'  # Placeholder

        logging.info(f"\n--- Processing Account {i + 1}/{len(accounts)}: {email} ---")

        device_id = None
        driver = None
        emulator_name = None
        port = None
        
        result_details = {
            'email': email,
            'status': 'Failure',
            'details': '',
            'screenshot_path': None
        }

        try:
            if emulator_type == 'sdk':
                emulators = list_emulators(sdk_path)
                if not emulators:
                    raise RuntimeError("No SDK emulators found.")
                emulator_name = emulators[0]
                devices_before = get_running_devices(sdk_path)
                logging.info(f"Running devices before start: {devices_before}")
                if not start_emulator(sdk_path, emulator_name):
                    raise RuntimeError("Failed to start SDK emulator.")
                logging.info("Waiting 30s for emulator to appear...")
                time.sleep(30)
                devices_after = get_running_devices(sdk_path)
                logging.info(f"Running devices after start: {devices_after}")
                device_id = next(iter(set(devices_after) - set(devices_before)), None)
                if not device_id:
                    raise RuntimeError("Failed to detect new SDK emulator.")

            elif emulator_type == 'bluestacks':
                exe_path = config.get('bluestacks_exe_path')
                instance_name = config.get('bluestacks_instance_name')
                if exe_path and instance_name:
                    if not start_bluestacks(exe_path, instance_name):
                        raise RuntimeError("Failed to issue BlueStacks start command.")
                    logging.info("Waiting 45s for BlueStacks to start...")
                    time.sleep(45)
                port = config.get('bluestacks_adb_port', 5555)
                device_id = connect_to_bluestacks(sdk_path, port)
                if not device_id:
                    raise RuntimeError(f"Failed to connect to BlueStacks on port {port}.")
            else:
                raise ValueError(f"Unsupported emulator_type: {emulator_type}")

            logging.info(f"Detected device ID: {device_id}")
            logging.info("Waiting 30s for device to be ready...")
            time.sleep(30)

            driver = get_appium_driver(device_id)
            if not driver:
                raise RuntimeError("Failed to get Appium driver.")

            run_automation(driver, email, password, group_link, beta_link, config, result_details)
            result_details['status'] = 'Success'
            result_details['details'] = 'Completed successfully.'

        except Exception as e:
            error_message = str(e)
            logging.error(f"An error occurred: {error_message}")
            result_details['details'] = error_message

        finally:
            if driver:
                driver.quit()
            if emulator_type == 'sdk' and emulator_name:
                stop_emulator(sdk_path, emulator_name)
            elif emulator_type == 'bluestacks' and port:
                disconnect_from_bluestacks(sdk_path, port)
            results.append(result_details)
            logging.info("Cleanup complete. Waiting 15s...")
            time.sleep(15)

    if results:
        generate_html_report(results)

    logging.info("\n--- All Accounts Processed. Automation Finished. ---")

if __name__ == '__main__':
    main()