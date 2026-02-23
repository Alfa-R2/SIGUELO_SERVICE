from dataclasses import dataclass
from pathlib import Path

from patchright.sync_api import BrowserContext, Locator, Page


@dataclass(frozen=True)
class GetInfoCommand:
    page: Page
    browser_context: BrowserContext
    data: Locator
    download_dir: Path
    codigo_tive: str = ""
