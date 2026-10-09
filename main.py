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
        driver = get_appium_driver(device_id, appium_port, worker_config.get('system_port'))
        if not driver:
            raise RuntimeError(f"Driver init failed for {device_id}")

        run_automation(
            driver, email, password, group_link, beta_link, global_config, result,
            worker_config=worker_config
        )

    except Exception as e:
        logging.error(f"Task failed for {email}: {e}")
        result['details'] = str(e)

    logging.info(f"Task end: {email} - {result['status']}")
    return result

def normalize_workers(workers):
    normalized = []
    device_ids = set()
    ports = set()
    for index, worker in enumerate(workers):
        worker = dict(worker)
        device_id = worker.get('device_id')
        if not isinstance(device_id, str) or not device_id.strip():
            raise ValueError('Each worker needs a device_id from adb devices.')
        if device_id in device_ids:
            raise ValueError(f'Duplicate device_id: {device_id}')
        device_ids.add(device_id)
        worker.setdefault('system_port', 8200 + index)
        worker.setdefault('chromedriver_port', 9000 + index)
        for key in ('appium_port', 'system_port', 'chromedriver_port'):
            port = worker.get(key)
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError(f'{key} must be an integer between 1 and 65535.')
            if port in ports:
                raise ValueError(f'Duplicate worker port: {port}')
            ports.add(port)
        normalized.append(worker)
    return normalized

def run_worker_tasks(tasks):
    return [(index, run_single_task(task)) for index, task in tasks]

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
        workers = normalize_workers(workers)
    except (TypeError, ValueError) as e:
        logging.error(f'Invalid workers: {e}')
        return

    try:
        with open(accounts_file, 'r', newline='', encoding='utf-8-sig') as f:
            accounts = list(csv.DictReader(f))
    except FileNotFoundError:
        logging.error(f"Accounts file not found: {accounts_file}")
        return

    if not accounts:
        logging.warning("No accounts found")
        return

    logging.info(f"Accounts: {len(accounts)}, Workers: {len(workers)}")

    worker_tasks = [[] for _ in workers]
    for index, account in enumerate(accounts):
        worker_index = index % len(workers)
        task = (account, workers[worker_index], config)
        worker_tasks[worker_index].append((index, task))
    indexed_results = []

    with ThreadPoolExecutor(max_workers=len(workers)) as executor:
        futures = [executor.submit(run_worker_tasks, tasks) for tasks in worker_tasks if tasks]
        for future in as_completed(futures):
            try:
                indexed_results.extend(future.result())
            except Exception as e:
                logging.error(f"Task exception: {e}")

    results = [result for _, result in sorted(indexed_results, key=lambda item: item[0])]
    if results:
        generate_html_report(results)

    success = sum(1 for r in results if r['status'] == 'Success')
    logging.info(f"=== Done: {success}/{len(results)} succeeded ===")

if __name__ == '__main__':
    main()
