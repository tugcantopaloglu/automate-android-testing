#!/usr/bin/env python

import time
import os
import logging
import uuid
from urllib.parse import urlsplit
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

CHROME_PACKAGE = 'com.android.chrome'
PLAY_STORE_PACKAGE = 'com.android.vending'

def get_appium_driver(emulator_name, appium_port=4723, system_port=None):
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = emulator_name
    options.udid = emulator_name
    options.automation_name = 'UiAutomator2'
    options.no_reset = True
    options.full_reset = False
    if system_port is not None:
        options.system_port = system_port
    
    try:
        driver = webdriver.Remote(f'http://127.0.0.1:{appium_port}', options=options)
        logging.info(f"Driver initialized for {emulator_name}:{appium_port}")
        return driver
    except Exception as e:
        logging.error(f"Driver init failed: {e}")
        return None

def get_chrome_driver(emulator_name, appium_port=4723, system_port=None, chromedriver_port=None):
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = emulator_name
    options.udid = emulator_name
    options.automation_name = 'UiAutomator2'
    options.browser_name = 'Chrome'
    options.no_reset = True
    if system_port is not None:
        options.system_port = system_port
    if chromedriver_port is not None:
        options.chromedriver_port = chromedriver_port
    
    try:
        driver = webdriver.Remote(f'http://127.0.0.1:{appium_port}', options=options)
        logging.info(f"Chrome driver initialized for {emulator_name}:{appium_port}")
        return driver
    except Exception as e:
        logging.error(f"Chrome driver init failed: {e}")
        return None

def wait_and_find(driver, by, value, timeout=15):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        return None

def wait_and_click(driver, by, value, timeout=15):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except TimeoutException:
        return False

def safe_click(driver, by, value):
    try:
        el = driver.find_element(by, value)
        el.click()
        return True
    except WebDriverException:
        return False

def google_login(driver, email, password):
    logging.info(f"Logging in as {email}")
    driver.get('https://accounts.google.com/signin')
    time.sleep(3)
    
    email_field = wait_and_find(driver, AppiumBy.XPATH, '//input[@type="email"]')
    if not email_field:
        email_field = wait_and_find(driver, AppiumBy.ID, 'identifierId')
    if not email_field:
        logging.error("Email field not found")
        return False
    
    email_field.clear()
    email_field.send_keys(email)
    time.sleep(1)
    
    if not wait_and_click(driver, AppiumBy.XPATH, '//button[contains(@class,"VfPpkd")]//span[text()="Next"]/ancestor::button'):
        wait_and_click(driver, AppiumBy.ID, 'identifierNext')
    time.sleep(3)
    
    password_field = wait_and_find(driver, AppiumBy.XPATH, '//input[@type="password"]')
    if not password_field:
        password_field = wait_and_find(driver, AppiumBy.NAME, 'password')
    if not password_field:
        logging.error("Password field not found")
        return False
    
    password_field.clear()
    password_field.send_keys(password)
    time.sleep(1)
    
    if not wait_and_click(driver, AppiumBy.XPATH, '//button[contains(@class,"VfPpkd")]//span[text()="Next"]/ancestor::button'):
        wait_and_click(driver, AppiumBy.ID, 'passwordNext')
    time.sleep(5)
    
    logging.info("Login submitted")
    return True

def join_google_group(driver, group_link):
    logging.info(f"Joining group: {group_link}")
    driver.get(group_link)
    time.sleep(5)
    
    join_xpaths = [
        '//button[contains(text(),"Join group")]',
        '//button[contains(text(),"Ask to join")]',
        '//span[contains(text(),"Join group")]/ancestor::button',
        '//span[contains(text(),"Ask to join")]/ancestor::button',
        '//*[contains(@aria-label,"Join")]',
    ]
    
    for xpath in join_xpaths:
        if wait_and_click(driver, AppiumBy.XPATH, xpath, timeout=3):
            logging.info("Clicked join button")
            time.sleep(3)
            return True
    
    if 'you are a member' in driver.page_source.lower() or 'leave group' in driver.page_source.lower():
        logging.info("Already a member")
        return True
    
    logging.warning("Join button not found")
    return False

def accept_beta(driver, beta_link):
    logging.info(f"Accepting beta: {beta_link}")
    driver.get(beta_link)
    time.sleep(5)
    
    accept_xpaths = [
        '//button[contains(text(),"Become a tester")]',
        '//button[contains(text(),"Accept")]',
        '//span[contains(text(),"Become a tester")]/ancestor::button',
        '//a[contains(text(),"Become a tester")]',
        '//*[contains(text(),"Become a tester")]',
        '//button[contains(@class,"tester")]',
    ]
    
    for xpath in accept_xpaths:
        if wait_and_click(driver, AppiumBy.XPATH, xpath, timeout=3):
            logging.info("Clicked become tester")
            time.sleep(3)
            return True
    
    if "you're a tester" in driver.page_source.lower() or 'leave the program' in driver.page_source.lower():
        logging.info("Already a tester")
        return True
    
    logging.warning("Beta accept button not found")
    return False

def install_from_playstore(driver, app_package):
    logging.info(f"Installing {app_package} from Play Store")
    
    playstore_url = f'https://play.google.com/store/apps/details?id={app_package}'
    driver.get(playstore_url)
    time.sleep(5)
    
    install_xpaths = [
        '//button[contains(text(),"Install")]',
        '//span[contains(text(),"Install")]/ancestor::button',
        '//*[contains(@aria-label,"Install")]',
    ]
    
    for xpath in install_xpaths:
        if wait_and_click(driver, AppiumBy.XPATH, xpath, timeout=3):
            logging.info("Clicked install")
            time.sleep(30)
            return True
    
    if 'uninstall' in driver.page_source.lower() or 'open' in driver.page_source.lower():
        logging.info("App already installed")
        return True
    
    logging.warning("Install button not found")
    return False

def xpath_literal(value):
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    parts = [f'"{part}"' for part in value.split('"')]
    return 'concat(' + ', \'"\', '.join(parts) + ')'

def open_app_and_interact(driver, app_package, actions):
    logging.info(f"Opening app: {app_package}")
    
    try:
        driver.activate_app(app_package)
        time.sleep(5)
    except Exception as e:
        logging.error(f"Failed to activate app: {e}")
        return False
    
    for action in actions:
        action_type = action.get('type')
        desc = action.get('description', action_type)
        logging.info(f"Action: {desc}")
        
        try:
            if action_type == 'click':
                element_id = action.get('element_id')
                xpath = action.get('xpath')
                text = action.get('text')
                
                if element_id:
                    clicked = safe_click(driver, AppiumBy.ID, element_id)
                elif xpath:
                    clicked = safe_click(driver, AppiumBy.XPATH, xpath)
                elif text:
                    clicked = safe_click(driver, AppiumBy.XPATH, f'//*[contains(@text,{xpath_literal(text)})]')
                else:
                    raise ValueError('Click action requires element_id, xpath, or text.')
                if not clicked:
                    raise RuntimeError(f'Click action failed: {desc}')
                time.sleep(2)
                
            elif action_type == 'wait':
                duration = action.get('duration_seconds', 5)
                time.sleep(duration)
                
            elif action_type == 'scroll':
                size = driver.get_window_size()
                x = int(size['width'] * 0.5)
                driver.swipe(x, int(size['height'] * 0.8), x, int(size['height'] * 0.2), 1000)
                time.sleep(1)
                
            elif action_type == 'back':
                driver.back()
                time.sleep(1)
            else:
                raise ValueError(f'Unknown action type: {action_type}')
                
        except Exception as e:
            logging.warning(f"Action failed: {e}")
            return False
    
    return True

def wait_with_session(driver, seconds):
    while seconds > 0:
        interval = min(seconds, 30)
        time.sleep(interval)
        driver.current_package
        seconds -= interval

def run_automation(driver, email, password, group_link, beta_link, config, result_details, worker_config=None):
    chrome_driver = None
    app_driver = None
    result_details['status'] = 'Failure'
    result_details['screenshot_path'] = None
    
    try:
        logging.info(f"Starting automation for {email}")
        
        app_package = config.get('automation_steps', {}).get('app_package')
        if not isinstance(app_package, str) or not app_package.strip():
            raise ValueError('automation_steps.app_package must be configured.')
        wait_seconds = float(config.get('wait_minutes', 10)) * 60
        if not 0 <= wait_seconds < float('inf'):
            raise ValueError('wait_minutes must be a finite non-negative number.')

        if worker_config is not None:
            device_id = worker_config['device_id']
            port = worker_config['appium_port']
            system_port = worker_config.get('system_port')
            chromedriver_port = worker_config.get('chromedriver_port')
        else:
            capabilities = driver.capabilities
            device_id = (capabilities.get('appium:udid') or capabilities.get('udid')
                         or capabilities.get('deviceUDID') or capabilities.get('deviceName'))
            if not device_id:
                raise ValueError('Driver did not identify the configured device.')
            appium_url = driver.command_executor.client_config.remote_server_addr
            port = urlsplit(appium_url).port or 4723
            system_port = capabilities.get('appium:systemPort', capabilities.get('systemPort'))
            chromedriver_port = capabilities.get('appium:chromedriverPort', capabilities.get('chromedriverPort'))
        
        driver.quit()
        driver = None
        
        chrome_driver = get_chrome_driver(device_id, port, system_port, chromedriver_port)
        if not chrome_driver:
            raise RuntimeError("Failed to init Chrome driver")
        
        if not google_login(chrome_driver, email, password):
            raise RuntimeError("Login failed")
        
        if group_link and group_link.strip():
            if not join_google_group(chrome_driver, group_link):
                raise RuntimeError('Group join step failed')
        
        if beta_link and beta_link.strip():
            if not accept_beta(chrome_driver, beta_link):
                raise RuntimeError('Beta acceptance step failed')
        
        if not install_from_playstore(chrome_driver, app_package):
            raise RuntimeError('Play Store install step failed')
        
        chrome_driver.quit()
        chrome_driver = None
        
        app_driver = get_appium_driver(device_id, port, system_port)
        if not app_driver:
            raise RuntimeError('Failed to init app driver')
        if not app_driver.is_app_installed(app_package):
            raise RuntimeError(f'App is not installed on the configured device: {app_package}')
        actions = config.get('automation_steps', {}).get('actions', [])
        if not open_app_and_interact(app_driver, app_package, actions):
            raise RuntimeError('App interaction failed')

        logging.info(f'Waiting {wait_seconds / 60} minutes...')
        wait_with_session(app_driver, wait_seconds)
        app_driver.quit()
        app_driver = None
        
        result_details['status'] = 'Success'
        result_details['details'] = 'Completed'
        logging.info(f"Automation complete for {email}")
        
    except Exception as e:
        logging.error(f"Automation failed: {e}")
        result_details['details'] = str(e)
        
        active_driver = app_driver or chrome_driver or driver
        try:
            if active_driver:
                os.makedirs('screenshots', exist_ok=True)
                screenshot_path = os.path.join('screenshots', f'fail_{uuid.uuid4().hex}.png')
                if active_driver.save_screenshot(screenshot_path):
                    result_details['screenshot_path'] = screenshot_path
        except Exception as screenshot_error:
            logging.warning(f'Failure screenshot unavailable: {screenshot_error}')
        
        raise
    
    finally:
        for active_driver in (app_driver, chrome_driver, driver):
            if active_driver:
                try:
                    active_driver.quit()
                except Exception as cleanup_error:
                    logging.warning(f'Driver cleanup failed: {cleanup_error}')
