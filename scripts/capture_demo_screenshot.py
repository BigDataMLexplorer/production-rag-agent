from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts/demo_chat.png",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 980})
        page.goto(f"{args.base_url}/demo", wait_until="networkidle")
        page.wait_for_function(
            "document.querySelector('#tenant') && document.querySelector('#tenant').options.length > 0"
        )
        page.select_option("#tenant", label="Acme Cloud (acme)")
        page.fill("#question", "How long are application logs kept by default?")
        page.click("#chat-form button")
        page.wait_for_function(
            "document.querySelectorAll('.message.assistant').length >= 2",
            timeout=120_000,
        )
        page.wait_for_timeout(600)
        page.screenshot(path=str(args.output), full_page=True)
        browser.close()

    print(f"Saved live demo screenshot to {args.output}")


if __name__ == "__main__":
    main()
