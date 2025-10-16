#!/usr/bin/env python

"""Main entry point for the Android automation framework."""

import csv
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config_reader import read_config
from src.automation_manager import get_appium_driver, run_automation
from src.logger_setup import setup_logger
from src.report_generator import generate_html_report

def run_single_automation_task(task_args):
    """Function executed by each worker thread."""
    account, worker_config, global_config = task_args
    email = account.get('email')
    password = account.get('password')
    group_link = account.get('group_link')
    beta_link = 'https://play.google.com/apps/testing/your.app.package'  # Placeholder

    device_id = worker_config.get('device_id')
    appium_port = worker_config.get('appium_port')

    logging.info(f"Starting task for account {email} on device {device_id}")

    result_details = {
        'email': email,
        'status': 'Failure',
        'details': '',
        'screenshot_path': None
    }

    driver = None
    try:
        driver = get_appium_driver(device_id, appium_port) # Modified to accept port
        if not driver:
            raise RuntimeError(f"Failed to get Appium driver for {device_id}")

        run_automation(driver, email, password, group_link, beta_link, global_config, result_details)
        result_details['status'] = 'Success'
        result_details['details'] = 'Completed successfully.'

    except Exception as e:
        error_message = str(e)
        logging.error(f"Error on task for {email} on {device_id}: {error_message}")
        result_details['details'] = error_message

    finally:
        if driver:
            driver.quit()
        logging.info(f"Finished task for account {email} on device {device_id}")
        return result_details

def main():
    """Main function to orchestrate the automation process."""
    setup_logger()
    logging.info("--- Starting Automation Framework (Parallel Mode) ---")

    config = read_config()
    accounts_file = config.get('accounts_file')
    workers = config.get('parallel_workers', [])

    if not workers:
        logging.error("No parallel_workers defined in config.json. Cannot run in parallel mode.")
        return

    try:
        with open(accounts_file, 'r', newline='') as f:
            accounts = list(csv.DictReader(f))
    except FileNotFoundError:
        logging.error(f"Accounts file not found at '{accounts_file}'.")
        return

    if not accounts:
        logging.warning("No accounts found in accounts file. Exiting.")
        return

    logging.info(f"Found {len(accounts)} accounts and {len(workers)} workers.")
    logging.info("NOTE: This mode assumes emulators and Appium servers are already running.")

    tasks = [(accounts[i], workers[i % len(workers)], config) for i in range(len(accounts))]
    results = []

    with ThreadPoolExecutor(max_workers=len(workers)) as executor:
        future_to_task = {executor.submit(run_single_automation_task, task): task for task in tasks}
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                logging.error(f"A task generated an exception: {exc}")

    if results:
        # Sort results to be in the same order as accounts
        results.sort(key=lambda r: [acc['email'] for acc in accounts].index(r['email']))
        generate_html_report(results)

    logging.info("\n--- All Accounts Processed. Automation Finished. ---")

if __name__ == '__main__':
    main()
