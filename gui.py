#!/usr/bin/env python

"""GUI Front-end for the Automation Framework."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import webbrowser
from threading import Thread

class AutomationGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Automation Framework")
        self.geometry("800x650")
        self.resizable(False, False)

        self.config_path = 'config.json'
        self.config_data = {}

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Configuration Section ---
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)

        self.config_vars = {}
        config_keys = [
            'android_sdk_path', 'bluestacks_exe_path', 'bluestacks_instance_name'
        ]

        for i, key in enumerate(config_keys):
            ttk.Label(config_frame, text=f"{key}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar()
            ttk.Entry(config_frame, textvariable=var, width=80).grid(row=i, column=1, sticky=tk.W, padx=5)
            self.config_vars[key] = var

        save_button = ttk.Button(config_frame, text="Save Config", command=self.save_config)
        save_button.grid(row=len(config_keys), column=1, sticky=tk.E, padx=5, pady=10)

        # --- Control Panel ---
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
        control_frame.pack(fill=tk.X, pady=5)

        self.run_button = ttk.Button(control_frame, text="Run Automation", command=self.start_automation_thread)
        self.run_button.pack(pady=5, side=tk.LEFT, padx=10)

        self.report_button = ttk.Button(control_frame, text="View Last Report", command=self.view_report, state='disabled')
        self.report_button.pack(pady=5, side=tk.LEFT)

        self.status_var = tk.StringVar(value="Status: Idle")
        ttk.Label(control_frame, textvariable=self.status_var).pack(pady=5, side=tk.RIGHT, padx=10)

        # --- Log Viewer ---
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def start_automation_thread(self):
        self.run_button.config(state='disabled')
        self.report_button.config(state='disabled')
        self.status_var.set("Status: Running...")
        automation_thread = Thread(target=self.run_automation, daemon=True)
        automation_thread.start()
        self.after(1000, self.update_log_viewer)

    def run_automation(self):
        from main import main as run_main_automation
        try:
            run_main_automation()
            self.status_var.set("Status: Finished. See report.html for details.")
        except Exception as e:
            self.status_var.set(f"Status: Error! Check logs.")
            messagebox.showerror("Runtime Error", str(e))
        finally:
            self.run_button.config(state='normal')
            if os.path.exists('report.html'):
                self.report_button.config(state='normal')

    def update_log_viewer(self):
        try:
            with open('automation.log', 'r') as f:
                log_content = f.read()
            self.log_text.config(state='normal')
            self.log_text.delete('1.0', tk.END)
            self.log_text.insert(tk.END, log_content)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
        except FileNotFoundError:
            pass
        if "Running" in self.status_var.get():
            self.after(1000, self.update_log_viewer)

    def load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
            for key, var in self.config_vars.items():
                var.set(self.config_data.get(key, ''))
        except FileNotFoundError:
            pass # It's ok if the file doesn't exist on first run
        except json.JSONDecodeError:
            messagebox.showerror("Error", f"Could not decode JSON from {self.config_path}")

    def save_config(self):
        if not self.config_data:
            self.config_data = {}
        for key, var in self.config_vars.items():
            self.config_data[key] = var.get()
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            messagebox.showinfo("Success", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def view_report(self):
        report_path = os.path.abspath('report.html')
        if os.path.exists(report_path):
            webbrowser.open(f'file://{report_path}')
        else:
            messagebox.showinfo("Info", "report.html not found. Run an automation first.")

if __name__ == "__main__":
    app = AutomationGUI()
    app.mainloop()