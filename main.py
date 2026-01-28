#!/usr/bin/env python

import csv
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config_reader import read_config
from src.automation_manager import get_appium_driver, run_automation
from src.logger_setup import setup_logger
from src.report_generator import generate_html_report

def run_single_task(task_args):
    account, worker_config, global_config = task_args
    email = account.get('email', '')
    password = account.get('password', '')
    group_link = account.get('group_link', '')
    beta_link = account.get('beta_link', '')

    device_id = worker_config.get('device_id')
    appium_port = worker_config.get('appium_port')

    logging.info(f"Task start: {email} on {device_id}")

    result = {
        'email': email,
        'status': 'Failure',
        'details': '',
        'screenshot_path': None
    }

    driver = None
    try:
        driver = get_appium_driver(device_id, appium_port)
        if not driver:
            raise RuntimeError(f"Driver init failed for {device_id}")

        run_automation(driver, email, password, group_link, beta_link, global_config, result)

    except Exception as e:
        logging.error(f"Task failed for {email}: {e}")
        result['details'] = str(e)

    logging.info(f"Task end: {email} - {result['status']}")
    return result

def main():
    setup_logger()
    logging.info("=== Automation Framework Started ===")

    config = read_config()
    accounts_file = config.get('accounts_file', 'accounts.csv')
    workers = config.get('parallel_workers', [])

    if not workers:
        logging.error("No workers in config")
        return

    try:
        with open(accounts_file, 'r', newline='') as f:
            accounts = list(csv.DictReader(f))
    except FileNotFoundError:
        logging.error(f"Accounts file not found: {accounts_file}")
        return

    if not accounts:
        logging.warning("No accounts found")
        return

    logging.info(f"Accounts: {len(accounts)}, Workers: {len(workers)}")

    tasks = [(accounts[i], workers[i % len(workers)], config) for i in range(len(accounts))]
    results = []

    with ThreadPoolExecutor(max_workers=len(workers)) as executor:
        futures = {executor.submit(run_single_task, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                logging.error(f"Task exception: {e}")

    if results:
        email_order = [a['email'] for a in accounts]
        results.sort(key=lambda r: email_order.index(r['email']) if r['email'] in email_order else 999)
        generate_html_report(results)

    success = sum(1 for r in results if r['status'] == 'Success')
    logging.info(f"=== Done: {success}/{len(results)} succeeded ===")

if __name__ == '__main__':
    main()
