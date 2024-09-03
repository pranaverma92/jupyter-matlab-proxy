# Copyright 2023-2024 The MathWorks, Inc.

import asyncio
import os
import psutil
import tests.integration.utils.integration_test_utils as utils
import pytest
import requests.exceptions
from matlab_proxy import settings as mwi_settings

_MATLAB_STARTUP_TIMEOUT = mwi_settings.get_process_startup_timeout()

if os.getenv("MWI_USE_FALLBACK_KERNEL") == "true":

    print(f"MWI_USE_FALLBACK_KERNEL is {os.getenv('MWI_USE_FALLBACK_KERNEL')}")

    @pytest.fixture(autouse=True, scope="module")
    def matlab_proxy_fixture(module_monkeypatch):
        """
        Pytest fixture for managing a standalone matlab-proxy process
        for testing purposes. This fixture sets up a matlab-proxy process in
        the module scope, and tears it down after all the tests are executed.

        Args:
            monkeypatch_module_scope (fixture): returns a MonkeyPatch object
            available in module scope
        """
        import matlab_proxy.util

        utils.perform_basic_checks()

        # Select a random free port to serve matlab-proxy for testing
        mwi_app_port = utils.get_random_free_port()
        mwi_base_url = "/matlab-test"

        # '127.0.0.1' is used instead 'localhost' for testing since Windows machines consume
        # some time to resolve 'localhost' hostname
        matlab_proxy_url = f"http://127.0.0.1:{mwi_app_port}{mwi_base_url}"

        # Set the log path based on the test's execution environment
        log_path = "tests/integration/integ_logs.log"
        base_path = os.environ.get(
            "GITHUB_WORKSPACE", os.path.dirname(os.path.abspath(__name__))
        )
        matlab_proxy_logs_path = os.path.join(base_path, log_path)

        # Start matlab-proxy-app for testing
        input_env = {
            # MWI_JUPYTER_TEST env variable is used in jupyter_matlab_kernel/kernel.py
            # to bypass jupyter server for testing
            "MWI_JUPYTER_TEST": "true",
            "MWI_APP_PORT": mwi_app_port,
            "MWI_BASE_URL": mwi_base_url,
            "MWI_LOG_FILE": str(matlab_proxy_logs_path),
            "MWI_ENABLE_TOKEN_AUTH": "false",
        }

        # Get event loop to start matlab-proxy in background
        loop = matlab_proxy.util.get_event_loop()

        # Run matlab-proxy in the background in an event loop
        proc = loop.run_until_complete(
            utils.start_matlab_proxy_app(input_env=input_env)
        )
        # Poll for matlab-proxy URL to respond
        utils.poll_web_service(
            matlab_proxy_url,
            step=5,
            timeout=_MATLAB_STARTUP_TIMEOUT,
            ignore_exceptions=(
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ),
        )

        # Wait for matlab-proxy to be up and running
        utils.wait_matlab_proxy_ready(matlab_proxy_url)

        # Update the OS environment variables such as app port, base url etc.
        # so that they can be used by MATLAB Kernel to obtain MATLAB
        for key, value in input_env.items():
            module_monkeypatch.setenv(key, value)

        # Run the jupyter kernel tests
        yield

        # Terminate matlab-proxy
        timeout = 120
        child_process = psutil.Process(proc.pid).children(recursive=True)
        for process in child_process:
            try:
                process.terminate()
                process.wait()
            except Exception:
                pass

        try:
            proc.terminate()
            loop.run_until_complete(asyncio.wait_for(proc.wait(), timeout=timeout))
        except Exception:
            proc.kill()

@pytest.fixture(scope="module", name="module_monkeypatch")
def monkeypatch_module_scope_fixture():
    """
    Pytest fixture for creating a monkeypatch object in 'module' scope.
    The default monkeypatch fixture returns monkeypatch object in
    'function' scope but a 'module' scope object is needed with matlab-proxy
    'module' scope fixture.

    Yields:
        class object: Object of class MonkeyPatch
    """
    with pytest.MonkeyPatch.context() as mp:
        yield mp
