import subprocess
import pytest
import os
import time
from playwright.sync_api import sync_playwright

if os.getenv("MWI_USE_FALLBACK_KERNEL") == "false":

    @pytest.fixture(scope="session", autouse=True)
    def start_jupyter_lab():
        # Start JupyterLab
        token = "abcd1234"
        jupyter_process = subprocess.Popen(
            [
                "jupyter",
                "lab",
                "--no-browser",
                "--port=8889",
                f"--NotebookApp.token={token}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give JupyterLab some time to start
        time.sleep(10)

        yield

        # Gracefully shutdown JupyterLab
        jupyter_process.terminate()
        jupyter_process.wait()

    def is_process_running(process_name):
        import psutil

        # Iterate over all running processes
        for process in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = process.info["cmdline"]
                if isinstance(cmdline, list) and any(
                    process_name in part for part in cmdline
                ):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def test_process_got_created():
        from playwright.sync_api import sync_playwright, expect

        token = "abcd1234"

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"http://localhost:8889/?token={token}")
            page.pause()
            element = page.get_by_text("Open MATLAB [↗]")
            element.click()
            browser.close()

        assert is_process_running("matlab-proxy-manager-app") == True
