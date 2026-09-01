"""Wait for a local HTTP service to become ready before proceeding."""

import sys
import time
import urllib.request


def wait_for_service(url: str = "http://localhost:2671", timeout: int = 20) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status in (200, 304, 404):
                    print(f"[*] Service is ready at {url}")
                    return True
        except Exception:
            time.sleep(0.5)

    print(f"[!] Warning: Service at {url} did not respond within {timeout}s.")
    return False


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:2671"
    max_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    wait_for_service(target_url, max_seconds)
