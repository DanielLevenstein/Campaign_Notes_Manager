import os
import subprocess
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import expect, sync_playwright


ROOT_DIR = Path(__file__).resolve().parents[2]
APP_URL = "http://127.0.0.1:8511"


def streamlit_command() -> list[str]:
    workspace_python = ROOT_DIR.parent / ".venv/bin/python"
    project_python = ROOT_DIR / ".venv/bin/python"
    python = project_python if project_python.exists() else workspace_python
    return [str(python), "-m", "streamlit"]


def wait_for_streamlit(url: str, process: subprocess.Popen, timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            if "PermissionError: [Errno 1] Operation not permitted" in output and "sock.bind" in output:
                pytest.skip("Local Streamlit port binding is not permitted in this test environment.")
            raise RuntimeError(f"Streamlit exited before startup.\n{output}")
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    output = ""
    if process.stdout:
        try:
            output = process.stdout.read()
        except Exception:
            output = ""
    raise TimeoutError(f"Streamlit app did not start at {url}\n{output}")


@pytest.fixture(scope="module")
def streamlit_app(free_tcp_port_factory):
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    port = free_tcp_port_factory()
    app_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            *streamlit_command(),
            "run",
            "streamlit_app.py",
            "--server.port",
            str(port),
            "--server.headless",
            "true",
        ],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_streamlit(app_url, process)
        yield app_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
