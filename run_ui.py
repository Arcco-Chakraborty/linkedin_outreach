import socket
import subprocess
import sys
from pathlib import Path


def find_open_port(start: int = 8501, end: int = 8600) -> int:
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No open port found between 8501 and 8600.")


if __name__ == "__main__":
    port = find_open_port()
    ui_path = str(Path(__file__).with_name("ui.py"))
    print(f"Starting LinkedIn Outreach UI at http://127.0.0.1:{port}")
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                ui_path,
                "--server.port",
                str(port),
            ]
        )
    )
