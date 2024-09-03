# Copyright 2023-2024 The MathWorks, Inc.

import asyncio
import os
import psutil
from tests.integration.utils import integration_test_utils as utils
import requests
import matlab_proxy_manager.lib.api as mpm_lib

from matlab_proxy import settings as mwi_settings
import matlab_proxy_manager.web.app as mpm

_MATLAB_STARTUP_TIMEOUT = mwi_settings.get_process_startup_timeout()


def start_matlab_proxy_sync(parent_id, caller_id, isolated_matlab=False):
    """
    Synchronous wrapper to start the MATLAB proxy using asyncio.

    Returns:
        dict: Information about the started MATLAB proxy.
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        mpm_lib.start_matlab_proxy_for_kernel(caller_id, parent_id, isolated_matlab)
    )


def shutdown_matlab_proxy_sync(parent_id, caller_id, mpm_auth_token):
    """
    Synchronous wrapper to shut down the MATLAB proxy using asyncio.

    Args:
        mpm_auth_token (str): Authentication token for shutting down the MATLAB proxy.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mpm_lib.shutdown(parent_id, caller_id, mpm_auth_token))

def license_matlab_proxy_no_mpm():
    try:
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
        # License matlab-proxy using playwright UI automation
        utils.license_matlab_proxy(matlab_proxy_url)

        # Wait for matlab-proxy to be up and running
        utils.wait_matlab_proxy_ready(matlab_proxy_url)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        try:
            shutdown_matlab_proxy_no_mpm(proc, loop)

        except Exception as e:
            print(f"Failed to shut down matlab-proxy: {e}")

def shutdown_matlab_proxy_no_mpm(proc, loop):
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

def license_matlab_proxy_mpm():
    import time

    """
    Pytest fixture for managing a standalone matlab-proxy process
    for testing purposes. This fixture sets up a matlab-proxy process in
    the module scope, and tears it down after all the tests are executed.

    Args:
        monkeypatch_module_scope (fixture): returns a MonkeyPatch object
        available in module scope
    """

    try:
        import uuid
        caller_id = str(uuid.uuid4())
        parent_id = str(uuid.uuid4())
        utils.perform_basic_checks()
        
        matlab_proxy_info = start_matlab_proxy_sync(parent_id, caller_id)
        headers = matlab_proxy_info.get("headers")
        mwi_auth_token = headers.get("MWI-AUTH-TOKEN")
        matlab_proxy_url = build_url(
            matlab_proxy_info.get("server_url"),
            headers.get("MWI-BASE-URL"),
            {"mwi-auth-token": mwi_auth_token},
        )
        mpm_auth_token = matlab_proxy_info.get("mpm_auth_token")

        # License matlab-proxy using playwright UI automation
        utils.license_matlab_proxy(matlab_proxy_url)

        # Wait for matlab-proxy to be up and running
        utils.wait_matlab_proxy_ready(
            matlab_proxy_info.get("absolute_url")
        )

        time.sleep(10)

    except Exception as err:
        print(f"An error occurred: {err}")
    finally:
        try:
            shutdown_matlab_proxy_sync(parent_id, caller_id, mpm_auth_token)

        except Exception as e:
            print(f"Failed to shut down matlab-proxy: {e}")

def build_url(base_url, path, query_params):
    # """
    # Constructs a full URL with the given base URL, path, and query parameters.

    # Args:
    #     base_url (str): The base URL (e.g., "https://example.com").
    #     path (str): The path to append to the base URL (e.g., "/api/resource").
    #     query_params (dict): A dictionary of query parameters (e.g., {"key1": "value1", "key2": "value2"}).

    # Returns:
    #     str: The full URL with encoded query parameters.
    # """
    from urllib.parse import urlencode, urlunparse, urlparse

    # Parse the base URL to extract the scheme and netloc
    parsed_url = urlparse(base_url)

    # Ensure the path is correctly concatenated
    full_path = f"{parsed_url.path.rstrip('/')}/{path.lstrip('/')}"

    query_string = urlencode(query_params)
    url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, full_path, "", query_string, "")
    )

    return url
