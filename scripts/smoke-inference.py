"""Optional real-model smoke test; requires Apple GPU, network/model access and memory."""

import argparse
import json
from pathlib import Path
import socket
import subprocess
import time
import urllib.error
import urllib.request


def request_json(url, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def smoke(binary, model, log_file, timeout):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    base = f"http://127.0.0.1:{port}/v1"
    with log_file.open("w") as log:
        process = subprocess.Popen(
            [str(binary), "server", "--model", model, "--host", "127.0.0.1", "--port", str(port)],
            stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + timeout
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f"Server exited with {process.returncode}; see {log_file}")
                try:
                    models = request_json(base + "/models")
                    break
                except urllib.error.HTTPError as error:
                    raise RuntimeError(f"Server returned HTTP {error.code}; see {log_file}") from error
                except urllib.error.URLError as error:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"HTTP readiness timed out: {error}; see {log_file}") from error
                    time.sleep(2)
            if models.get("object") != "list" or not models.get("data"):
                raise RuntimeError(f"Unexpected /v1/models response: {models}")
            identifier = models["data"][0]["id"]
            completion = request_json(base + "/chat/completions", {
                "model": identifier,
                "messages": [{"role": "user", "content": "Reply with the word hello."}],
                "max_tokens": 16,
                "stream": False,
            })
            if (completion.get("model") != identifier
                    or not completion.get("choices")
                    or completion["choices"][0]["message"]["role"] != "assistant"
                    or completion.get("usage", {}).get("completion_tokens", 0) <= 0):
                raise RuntimeError(f"Unexpected chat response: {completion}")
            print(json.dumps({"models": models, "completion": completion}, indent=2))
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("--model", required=True, help="Compatible chat-model ID or complete local directory")
    parser.add_argument("--log", type=Path, default=Path("dist/inference-smoke.log"))
    parser.add_argument("--timeout", type=int, default=900, help="Readiness/download timeout in seconds")
    args = parser.parse_args()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    smoke(args.binary.resolve(strict=True), args.model, args.log.resolve(), args.timeout)
