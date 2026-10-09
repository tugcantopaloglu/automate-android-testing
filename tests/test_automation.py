import io
import os
import tempfile
import threading
import unittest
from contextlib import ExitStack
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, mock_open, patch

import gui
import main
from appium.webdriver.appium_connection import AppiumConnection
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.client_config import ClientConfig

from src import automation_manager as automation
from src import emulator_manager
from src.config_reader import read_config
from src.report_generator import generate_html_report, screenshot_href


class DriverTests(unittest.TestCase):
    def test_both_session_types_target_the_configured_device(self):
        with patch.object(automation.webdriver, 'Remote') as remote:
            automation.get_appium_driver('emulator-5556', 4724, 8201)
            automation.get_chrome_driver('emulator-5556', 4724, 8201, 9001)
        for call in remote.call_args_list:
            self.assertEqual(call.args[0], 'http://127.0.0.1:4724')
            caps = call.kwargs['options'].to_capabilities()
            self.assertEqual(caps['appium:udid'], 'emulator-5556')
            self.assertEqual(caps['appium:systemPort'], 8201)
        self.assertEqual(remote.call_args_list[1].kwargs['options'].to_capabilities()['appium:chromedriverPort'], 9001)

    def test_missing_click_fails_without_executing_later_actions(self):
        driver = Mock()
        driver.find_element.side_effect = NoSuchElementException('Missing')
        with patch.object(automation.time, 'sleep'):
            succeeded = automation.open_app_and_interact(
                driver, 'com.example.app', [{'type': 'click', 'text': 'Accept'}, {'type': 'back'}]
            )
        self.assertFalse(succeeded)
        driver.back.assert_not_called()

    def test_quoted_text_is_a_valid_xpath_literal(self):
        driver = Mock()
        with patch.object(automation.time, 'sleep'):
            self.assertTrue(automation.open_app_and_interact(
                driver, 'com.example.app', [{'type': 'click', 'text': 'Say "it\'s ready"'}]
            ))
        self.assertEqual(driver.find_element.call_args.args[1],
                         '//*[contains(@text,concat("Say ", \'"\', "it\'s ready", \'"\', ""))]')

    def test_unknown_action_is_a_failure(self):
        with patch.object(automation.time, 'sleep'):
            self.assertFalse(automation.open_app_and_interact(Mock(), 'com.example.app', [{'type': 'typo'}]))

    def test_wait_keeps_session_alive_between_short_intervals(self):
        driver = Mock()
        current_package = PropertyMock(return_value='com.example.app')
        type(driver).current_package = current_package
        with patch.object(automation.time, 'sleep') as sleep:
            automation.wait_with_session(driver, 65)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [30, 30, 5])
        self.assertEqual(current_package.call_count, 3)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.previous_directory = os.getcwd()
        os.chdir(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(os.chdir, self.previous_directory)
        self.initial = Mock()
        self.initial.capabilities = {'deviceUDID': 'emulator-5556'}
        self.initial.command_executor = AppiumConnection(client_config=ClientConfig('http://127.0.0.1:4724'))
        self.chrome = Mock()
        self.native = Mock()
        self.result = {'status': 'Failure', 'details': '', 'screenshot_path': None}
        self.config = {'wait_minutes': 0, 'automation_steps': {'app_package': 'com.example.app', 'actions': []}}
        self.patches = ExitStack()
        self.addCleanup(self.patches.close)
        self.factories = {}
        for name, value in [('get_chrome_driver', self.chrome), ('get_appium_driver', self.native),
                            ('google_login', True), ('join_google_group', True), ('accept_beta', True),
                            ('install_from_playstore', True), ('open_app_and_interact', True)]:
            self.factories[name] = self.patches.enter_context(patch.object(automation, name, return_value=value))
        self.patches.enter_context(patch.object(automation.time, 'sleep'))

    def run_workflow(self, email='tester@example.com'):
        automation.run_automation(self.initial, email, 'placeholder', 'https://example.com/group',
                                  'https://example.com/beta', self.config, self.result)

    def test_public_connection_config_works_without_private_url(self):
        self.run_workflow()
        self.assertEqual(self.result['status'], 'Success')
        self.factories['get_chrome_driver'].assert_called_once_with('emulator-5556', 4724, None, None)
        for driver in (self.initial, self.chrome, self.native):
            driver.quit.assert_called_once()

    def test_failed_steps_do_not_report_success(self):
        for name in ('google_login', 'join_google_group', 'accept_beta', 'install_from_playstore'):
            with self.subTest(name=name):
                self.factories[name].return_value = False
                with self.assertRaises(RuntimeError):
                    self.run_workflow()
                self.assertEqual(self.result['status'], 'Failure')
                self.factories[name].return_value = True

    def test_missing_native_session_is_a_failure(self):
        self.factories['get_appium_driver'].return_value = None
        with self.assertRaisesRegex(RuntimeError, 'Failed to init app driver'):
            self.run_workflow()
        self.assertEqual(self.result['status'], 'Failure')
        self.chrome.quit.assert_called_once()

    def test_install_button_does_not_prove_installation_on_device(self):
        self.native.is_app_installed.return_value = False
        with self.assertRaisesRegex(RuntimeError, 'not installed'):
            self.run_workflow()
        self.native.quit.assert_called_once()
        self.factories['open_app_and_interact'].assert_not_called()

    def test_native_failure_uses_native_screenshot_and_closes_session(self):
        self.factories['open_app_and_interact'].return_value = False
        with self.assertRaisesRegex(RuntimeError, 'interaction failed'):
            self.run_workflow('../../private/account')
        self.assertEqual(self.result['status'], 'Failure')
        self.assertEqual(Path(self.result['screenshot_path']).parent, Path('screenshots'))
        self.assertNotIn('private', self.result['screenshot_path'])
        self.native.save_screenshot.assert_called_once()
        self.native.quit.assert_called_once()
        self.initial.save_screenshot.assert_not_called()

    def test_invalid_configuration_fails_before_any_account_operation(self):
        self.config['automation_steps']['app_package'] = ''
        with self.assertRaisesRegex(ValueError, 'app_package'):
            self.run_workflow()
        self.factories['google_login'].assert_not_called()
        self.initial.quit.assert_called_once()

    def test_screenshot_error_does_not_replace_the_primary_failure(self):
        self.factories['open_app_and_interact'].return_value = False
        self.native.save_screenshot.side_effect = OSError('Cannot save')
        with self.assertRaisesRegex(RuntimeError, 'interaction failed'):
            self.run_workflow()
        self.assertEqual(self.result['details'], 'App interaction failed')
        self.assertIsNone(self.result['screenshot_path'])
        self.native.quit.assert_called_once()


class SchedulingTests(unittest.TestCase):
    def test_account_jobs_never_overlap_on_one_worker_and_keep_csv_order(self):
        config = {'accounts_file': 'unused.csv', 'parallel_workers': [
            {'device_id': 'emulator-5554', 'appium_port': 4723},
            {'device_id': 'emulator-5556', 'appium_port': 4724}
        ]}
        lock = threading.Lock()
        active = {}
        peak = {}
        release = threading.Event()

        def task(args):
            account, worker, _ = args
            device = worker['device_id']
            with lock:
                active[device] = active.get(device, 0) + 1
                peak[device] = max(peak.get(device, 0), active[device])
            if account['id'] == '0':
                release.wait(0.1)
            if account['id'] == '2':
                release.set()
            with lock:
                active[device] -= 1
            return {'email': account['email'], 'status': 'Success', 'details': account['id']}

        accounts = 'email,password,id\nsame@example.com,placeholder,0\nother@example.com,placeholder,1\nsame@example.com,placeholder,2\n'
        with patch.object(main, 'read_config', return_value=config), patch.object(main, 'setup_logger'), \
                patch('builtins.open', mock_open(read_data=accounts)), patch.object(main, 'run_single_task', side_effect=task), \
                patch.object(main, 'generate_html_report') as report:
            main.main()
        self.assertEqual(peak, {'emulator-5554': 1, 'emulator-5556': 1})
        self.assertEqual([result['details'] for result in report.call_args.args[0]], ['0', '1', '2'])

    def test_duplicate_or_invalid_worker_assignments_are_rejected(self):
        cases = [
            [{'device_id': 'emulator-5554', 'appium_port': 4723}] * 2,
            [{'device_id': 'emulator-5554', 'appium_port': 4723}, {'device_id': 'emulator-5556', 'appium_port': 4723}],
            [{'device_id': 'emulator-5554', 'appium_port': None}],
            [{'device_id': '', 'appium_port': 4723}],
        ]
        for workers in cases:
            with self.subTest(workers=workers), self.assertRaises(ValueError):
                main.normalize_workers(workers)


class ReportTests(unittest.TestCase):
    def test_report_escapes_fields_and_rejects_non_screenshot_links(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'cwd', return_value=Path(directory)):
            output = io.StringIO()
            with patch('builtins.open', mock_open()) as report_file:
                report_file.return_value.write.side_effect = output.write
                generate_html_report([{'email': '<script>alert(1)</script>', 'status': '<img src=x>',
                                       'details': '<b>Failure</b> "quoted"', 'screenshot_path': 'javascript:alert(1)'}])
            rendered = output.getvalue()
            self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', rendered)
            self.assertIn('&lt;b&gt;Failure&lt;/b&gt;', rendered)
            self.assertNotIn('javascript:', rendered)
            self.assertNotIn('<img src=x>', rendered)
            self.assertIsNone(screenshot_href(Path(directory) / 'outside.png'))
            self.assertEqual(screenshot_href(Path(directory) / 'screenshots' / 'safe file.png'), 'screenshots/safe%20file.png')


class EmulatorTests(unittest.TestCase):
    def test_only_online_emulators_are_returned(self):
        devices = 'List of devices attached\nemulator-5554\tdevice\nemulator-5556\toffline\nphone\tdevice\n'
        with patch.object(emulator_manager.subprocess, 'run', return_value=SimpleNamespace(stdout=devices)):
            self.assertEqual(emulator_manager.get_running_devices('/sdk'), ['emulator-5554'])

    def test_empty_avd_listing_returns_no_emulators(self):
        with patch.object(emulator_manager.subprocess, 'run', return_value=SimpleNamespace(stdout='\n')):
            self.assertEqual(emulator_manager.list_emulators('/sdk'), [])

    def test_stop_targets_the_requested_avd_instead_of_the_first_device(self):
        responses = [SimpleNamespace(stdout='Unrelated\nOK\n'), SimpleNamespace(stdout='Requested\nOK\n'), SimpleNamespace(stdout='OK')]
        with patch.object(emulator_manager, 'get_running_devices', return_value=['emulator-5554', 'emulator-5556']), \
                patch.object(emulator_manager.subprocess, 'run', side_effect=responses) as run:
            self.assertTrue(emulator_manager.stop_emulator('/sdk', 'Requested'))
        self.assertEqual(run.call_args.args[0][-4:], ['-s', 'emulator-5556', 'emu', 'kill'])

    def test_unknown_avd_never_sends_a_kill_command(self):
        with patch.object(emulator_manager, 'get_running_devices', return_value=['emulator-5554']), \
                patch.object(emulator_manager.subprocess, 'run', return_value=SimpleNamespace(stdout='Unrelated\nOK\n')) as run:
            self.assertFalse(emulator_manager.stop_emulator('/sdk', 'Requested'))
        self.assertNotIn('kill', run.call_args.args[0])


class GuiTests(unittest.TestCase):
    def test_worker_only_enqueues_completion_without_touching_widgets(self):
        instance = SimpleNamespace(automation_events=Queue())
        with patch.object(main, 'main', side_effect=RuntimeError('example failure')):
            gui.AutomationGUI.run_automation(instance)
        self.assertEqual(instance.automation_events.get_nowait(), 'example failure')

    def test_main_thread_applies_queued_completion(self):
        instance = SimpleNamespace(automation_events=Queue(), status_var=Mock(), run_button=Mock(), report_button=Mock())
        instance.automation_events.put(None)
        with patch.object(gui.os.path, 'exists', return_value=True):
            gui.AutomationGUI.poll_automation(instance)
        instance.status_var.set.assert_called_once_with('Status: Finished. See report.html for details.')
        instance.run_button.config.assert_called_once_with(state='normal')
        instance.report_button.config.assert_called_once_with(state='normal')


class ConfigTests(unittest.TestCase):
    def test_invalid_json_or_non_object_configuration_is_rejected(self):
        for contents in ('{invalid', '[]'):
            with self.subTest(contents=contents), patch('builtins.open', mock_open(read_data=contents)):
                self.assertEqual(read_config(), {})


if __name__ == '__main__':
    unittest.main()
