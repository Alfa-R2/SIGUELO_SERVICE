from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from patchright.sync_api import Page

from siguelo_service.applications.get_download_error import GetDownloadError
from siguelo_service.models.dataclasses import ResourceDownloadResult
from siguelo_service.scripts import DOWNLOAD_PDF_SCRIPT


@contextmanager
def download_from_new_tab(
    page: Page, download_path: Path, type: str, timeout: float = 30_000
) -> Generator[ResourceDownloadResult, None, None]:
    """
    raises:
        - UnknownDownloadException: If no known error message is found in the page.
    """

    download_result: ResourceDownloadResult = ResourceDownloadResult(
        error=False,
        error_message=None,
        path=None,
        resource_type=type,
    )

    try:
        if not download_path.exists():
            with page.context.expect_page(timeout=timeout) as new_page_info:
                yield download_result

            new_page: Page = new_page_info.value

            try:
                with new_page.expect_download() as download_info:
                    new_page.evaluate(DOWNLOAD_PDF_SCRIPT)

                download_info.value.save_as(download_path)
                download_result.path = download_path

            finally:
                if not new_page.is_closed():
                    new_page.close()
        else:
            download_result.path = download_path
            yield download_result

    except TimeoutError:
        download_result.error = True
        download_result.error_message = GetDownloadError.execute(page=page)
