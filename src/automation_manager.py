#!/usr/bin/env python

"""This script is the core of the automation process."""

import time
import os
import logging
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

# TODO: The user needs to have an Appium server running on localhost:4723

def get_appium_driver(emulator_name, appium_port=4723):
    """Initializes and returns an Appium driver for the specified emulator."""
    options = UiAutomator2Options()
    options.platform_name = 'Android'
    options.device_name = emulator_name
    options.automation_name = 'UiAutomator2'
    # Add other capabilities as needed, e.g.:
    # options.app = '/path/to/your/app.apk'

    try:
        appium_url = f'http://127.0.0.1:{appium_port}'
        driver = webdriver.Remote(appium_url, options=options)
        logging.info(f"Appium driver initialized for {emulator_name} on port {appium_port}")
        return driver
    except Exception as e:
        logging.error(f"Error initializing Appium driver: {e}")
        return None

def run_automation(driver, email, password, group_link, beta_link, config, result_details):
    """Runs the automation steps for a single account."""
    try:
        logging.info("Starting automation...")
        # 1. Open Google Group link and log in
        driver.get('https://accounts.google.com') # Go directly to login page
        time.sleep(5)

        # Enter email
        # NOTE: The resource-id 'identifierId' is a placeholder.
        email_field = driver.find_element(by=AppiumBy.ID, value='com.google.android.gms:id/identifierId')
        email_field.send_keys(email)
        # NOTE: The resource-id for the 'Next' button is a placeholder.
        driver.find_element(by=AppiumBy.ID, value='com.google.android.gms:id/identifierNext').click()
        time.sleep(5)

        # Enter password
        # NOTE: The resource-id for the password field is a placeholder.
        password_field = driver.find_element(by=AppiumBy.ID, value='com.google.android.gms:id/password')
        password_field.send_keys(password)
        # NOTE: The resource-id for the 'Next' button is a placeholder.
        driver.find_element(by=AppiumBy.ID, value='com.google.android.gms:id/passwordNext').click()
        time.sleep(10) # Wait for login to complete

        logging.info("Login attempt finished. Now joining group...")

        # 2. Join the Google Group
        driver.get(group_link)
        time.sleep(5) # Wait for page to load
        # TODO: Add logic to find and click the 'Join Group' button.
        logging.info(f"Opened Google Group link: {group_link}")

        # 3. Open Beta link
        driver.get(beta_link)
        time.sleep(5) # Wait for page to load
        # TODO: Add steps to download and install the app from the Play Store
        logging.info(f"Opened Beta link: {beta_link}")

        # 4. Interact with the app based on config
        app_package = config.get('automation_steps', {}).get('app_package')
        actions = config.get('automation_steps', {}).get('actions', [])

        if app_package and actions:
            logging.info(f"Activating app: {app_package}")
            driver.activate_app(app_package)
            time.sleep(5)

            for action in actions:
                action_type = action.get('type')
                logging.info(f"Performing action: {action.get('description', action_type)}")
                if action_type == 'click':
                    element_id = action.get('element_id')
                    if element_id:
                        element = driver.find_element(by=AppiumBy.ID, value=element_id)
                        element.click()
                        time.sleep(2)
                elif action_type == 'wait':
                    duration = action.get('duration_seconds', 5)
                    time.sleep(duration)
            logging.info("Finished configured app interactions.")
        else:
            logging.warning("No configured app interactions found. Skipping.")

        # 5. Wait for 10 minutes
        logging.info("Waiting for 10 minutes...")
        time.sleep(600)

        logging.info("Automation finished.")

    except Exception as e:
        logging.error(f"An error occurred during automation: {e}")
        
        # Take screenshot on failure
        screenshots_dir = 'screenshots'
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        screenshot_path = os.path.join(screenshots_dir, f"failure_{timestamp}.png")
        
        try:
            if driver:
                driver.save_screenshot(screenshot_path)
                logging.info(f"Screenshot saved to {screenshot_path}")
                result_details['screenshot_path'] = screenshot_path # Update the result dict
        except Exception as screenshot_e:
            logging.error(f"Failed to save screenshot: {screenshot_e}")
            
        raise # Re-raise the exception to be caught by the main loop
    finally:
        if driver:
            driver.quit()
            logging.info("Appium driver quit.")

if __name__ == '__main__':
    # This is for testing purposes.
    from src.logger_setup import setup_logger
    setup_logger()

    test_emulator = 'emulator-5554'
    test_email = 'your-email@gmail.com'
    test_password = 'your-password'
    test_group_link = 'https://groups.google.com/g/your-group'
    test_beta_link = 'https://play.google.com/apps/testing/your.app.package'
    test_config = {
        'automation_steps': {
            'app_package': 'com.example.app',
            'actions': [] # No actions for this simple test
        }
    }

    appium_driver = get_appium_driver(test_emulator)
    if appium_driver:
        # A dummy result dict for testing
        dummy_result_details = {}
        run_automation(appium_driver, test_email, test_password, test_group_link, test_beta_link, test_config, dummy_result_details)