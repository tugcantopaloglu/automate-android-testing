#!/usr/bin/env python

"""Generates a minimalist and sleek HTML report from test results."""

import time
import logging

def generate_html_report(results):
    """Generates an HTML report from a list of result dictionaries."""
    
    # --- CSS Styles (embedded for portability) ---
    styles = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f7f9; color: #333; margin: 0; padding: 2em; }
        .container { max-width: 1000px; margin: auto; background: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        h1 { color: #2c3e50; }
        p { color: #555; }
        .summary { display: flex; justify-content: space-around; padding: 1em 0; margin-bottom: 2em; border-top: 1px solid #eee; border-bottom: 1px solid #eee; }
        .summary-item { text-align: center; }
        .summary-item h2 { margin: 0; font-size: 2em; }
        .summary-item p { margin: 0; color: #7f8c8d; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #ecf0f1; }
        .status-success { color: #27ae60; font-weight: bold; }
        .status-failure { color: #c0392b; font-weight: bold; }
        a { color: #2980b9; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
    """

    # --- HTML Structure ---
    html_content = f"""<html><head><title>Automation Test Report</title>{styles}</head><body><div class="container">"""
    html_content += "<h1>Automation Test Report</h1>"
    generation_time = time.strftime("%Y-%m-%d %H:%M:%S")
    html_content += f"<p>Generated on: {generation_time}</p>"

    # --- Summary Section ---
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'Success')
    failed = total - passed
    html_content += f"""<div class="summary">
        <div class="summary-item"><h2>{total}</h2><p>Total Accounts</p></div>
        <div class="summary-item"><h2 style="color: #27ae60;">{passed}</h2><p>Passed</p></div>
        <div class="summary-item"><h2 style="color: #c0392b;">{failed}</h2><p>Failed</p></div>
    </div>"""

    # --- Results Table ---
    html_content += "<table><tr><th>#</th><th>Account</th><th>Status</th><th>Details</th><th>Screenshot</th></tr>"
    for i, result in enumerate(results):
        status_class = 'status-success' if result['status'] == 'Success' else 'status-failure'
        screenshot_link = f'<a href="{result["screenshot_path"]}" target="_blank">View</a>' if result.get("screenshot_path") else "N/A"
        html_content += f"""<tr>
            <td>{i+1}</td>
            <td>{result['email']}</td>
            <td><span class="{status_class}">{result['status'].upper()}</span></td>
            <td>{result['details']}</td>
            <td>{screenshot_link}</td>
        </tr>"""
    
    html_content += "</table></div></body></html>"

    # --- Write to file ---
    try:
        with open("report.html", "w") as f:
            f.write(html_content)
        logging.info("Successfully generated HTML report: report.html")
    except Exception as e:
        logging.error(f"Failed to generate HTML report: {e}")

if __name__ == '__main__':
    # For testing the report generator directly
    import logging
    logging.basicConfig(level=logging.INFO)
    test_results = [
        {'email': 'test1@example.com', 'status': 'Success', 'details': 'Completed successfully.', 'screenshot_path': None},
        {'email': 'test2@example.com', 'status': 'Failure', 'details': 'Element not found: com.google.android.gms:id/identifierId', 'screenshot_path': 'screenshots/failure_20251016-140000.png'},
        {'email': 'test3@example.com', 'status': 'Success', 'details': 'Completed successfully.', 'screenshot_path': None},
    ]
    generate_html_report(test_results)
