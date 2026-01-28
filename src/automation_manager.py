#!/usr/bin/env python

import time
import os
import logging
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

CHROME_PACKAGE = 'com.android.chrome'
PLAY_STORE_PACKAGE = 'com.android.vending'

def get_appium_driver(emulator_name, appium_port=4723):
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = emulator_name
    options.automation_name = 'UiAutomator2'
    options.no_reset = True
    options.full_reset = False
    
    try:
        driver = webdriver.Remote(f'http://127.0.0.1:{appium_port}', options=options)
        logging.info(f"Driver initialized for {emulator_name}:{appium_port}")
        return driver
    except Exception as e:
        logging.error(f"Driver init failed: {e}")
        return None

def get_chrome_driver(emulator_name, appium_port=4723):
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = emulator_name
    options.automation_name = 'UiAutomator2'
    options.browser_name = 'Chrome'
    options.no_reset = True
    
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
    except:
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
                    safe_click(driver, AppiumBy.ID, element_id)
                elif xpath:
                    safe_click(driver, AppiumBy.XPATH, xpath)
                elif text:
                    safe_click(driver, AppiumBy.XPATH, f'//*[contains(@text,"{text}")]')
                time.sleep(2)
                
            elif action_type == 'wait':
                duration = action.get('duration_seconds', 5)
                time.sleep(duration)
                
            elif action_type == 'scroll':
                driver.swipe(500, 1500, 500, 500, 1000)
                time.sleep(1)
                
            elif action_type == 'back':
                driver.back()
                time.sleep(1)
                
        except Exception as e:
            logging.warning(f"Action failed: {e}")
            continue
    
    return True

def run_automation(driver, email, password, group_link, beta_link, config, result_details):
    chrome_driver = None
    
    try:
        logging.info(f"Starting automation for {email}")
        
        device_id = driver.capabilities.get('deviceName', 'unknown')
        appium_url = driver.command_executor._url
        port = int(appium_url.split(':')[-1].split('/')[0]) if appium_url else 4723
        
        driver.quit()
        
        chrome_driver = get_chrome_driver(device_id, port)
        if not chrome_driver:
            raise RuntimeError("Failed to init Chrome driver")
        
        if not google_login(chrome_driver, email, password):
            raise RuntimeError("Login failed")
        
        if group_link and group_link.strip():
            join_google_group(chrome_driver, group_link)
        
        if beta_link and beta_link.strip():
            accept_beta(chrome_driver, beta_link)
        
        app_package = config.get('automation_steps', {}).get('app_package')
        if app_package:
            install_from_playstore(chrome_driver, app_package)
        
        chrome_driver.quit()
        chrome_driver = None
        
        app_driver = get_appium_driver(device_id, port)
        if app_driver and app_package:
            actions = config.get('automation_steps', {}).get('actions', [])
            open_app_and_interact(app_driver, app_package, actions)
            
            wait_minutes = config.get('wait_minutes', 10)
            logging.info(f"Waiting {wait_minutes} minutes...")
            time.sleep(wait_minutes * 60)
            
            app_driver.quit()
        
        result_details['status'] = 'Success'
        result_details['details'] = 'Completed'
        logging.info(f"Automation complete for {email}")
        
    except Exception as e:
        logging.error(f"Automation failed: {e}")
        result_details['details'] = str(e)
        
        screenshots_dir = 'screenshots'
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"fail_{email}_{timestamp}.png")
        
        active_driver = chrome_driver if chrome_driver else driver
        try:
            if active_driver:
                active_driver.save_screenshot(screenshot_path)
                result_details['screenshot_path'] = screenshot_path
        except:
            pass
        
        raise
    
    finally:
        if chrome_driver:
            try:
                chrome_driver.quit()
            except:
                pass
