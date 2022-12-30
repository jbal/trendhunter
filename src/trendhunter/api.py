"""Core API code."""

import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import Semaphore
from itertools import chain
from typing import Dict, Generator, List, Optional, Tuple, Union
from urllib.parse import urlencode, urljoin, urlparse, urlunparse

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from trendhunter.taxonomies import AJAXIncrement, APIAction, PageType
from trendhunter.tuples import (
    Article,
    Image,
    Metadata,
    Resource,
    Text,
    URLPair,
)
from trendhunter.utils import format_console

TRENDHUNTER_URL = "https://www.trendhunter.com/"


class ResourceError(Exception):
    pass


def sync_url_and_params(url: str, params: Dict) -> str:
    parts = list(urlparse(url))
    parts[4] = urlencode(params or {})
    return urlunparse(parts)


async def _async_get_url(
    url: str,
    semaphore: Semaphore,
    session: ClientSession,
    proxy: Optional[str],
    timeout: int,
    propagate: bool,
) -> Optional[Resource]:
    async with semaphore:
        try:
            format_console(__name__).info(
                f'Downloading content from "{url}"...'
            )

            async with session.get(
                url,
                proxy=proxy,
                allow_redirects=False,
                timeout=timeout,
                raise_for_status=True,
            ) as resp:
                content = await resp.read()

            if not (content.find(b'{"success":true,"data":""}') == -1):
                raise ResourceError(f'No content retrieved from "{url}".')

            return Resource(url, content)
        except (ClientError, ResourceError) as e:
            if propagate:
                raise e
            else:
                format_console(__name__).error(
                    f'HTTP error downloading content of "{url}". Error: {e}.'
                )


async def _async_bridge(
    urls: Union[List[str], Tuple[str], str],
    semaphore: Semaphore,
    session: ClientSession,
    proxy: Optional[str],
    timeout: int,
    propagate: bool,
) -> Union[List[Resource], Resource]:
    if isinstance(urls, (list, tuple)):
        resources = []

        for url in urls:
            resources.append(
                await _async_get_url(
                    url, semaphore, session, proxy, timeout, propagate
                )
            )

        return resources
    else:
        return await _async_get_url(
            urls, semaphore, session, proxy, timeout, propagate
        )


async def async_get_urls(
    urls: Union[List[List[str]], List[Tuple[str]], List[str]],
    concurrency: int,
    proxy: Optional[str],
    timeout: int,
    propagate: bool = False,
) -> Union[List[List[Resource]], List[Resource]]:
    semaphore = Semaphore(concurrency)

    async with ClientSession() as session:
        tasks = [
            _async_bridge(url, semaphore, session, proxy, timeout, propagate)
            for url in urls
        ]
        return await asyncio.gather(*tasks)


def extract_urls(resource: Resource) -> List[URLPair]:
    soup = BeautifulSoup(resource.content, "html.parser")

    def href_contains_trends(href):
        return not (href.replace("\\", "").find("/trends/") == -1)

    urls = []
    elements = soup.find_all(
        "a", attrs={"class": "thar", "href": href_contains_trends}
    )

    for element in elements:
        image = element.find("img", attrs={"data-src": True})

        if image:
            urls.append(
                URLPair(
                    urljoin(
                        TRENDHUNTER_URL, element["href"].replace("\\", "")
                    ),
                    image["data-src"].replace("\\", ""),
                )
            )

    return urls


def extract_image_url(resource: Resource) -> Image:
    soup = BeautifulSoup(resource.content, "html.parser")
    img = soup.find("img", attrs={"class": "gal__mainImage", "data-src": True})
    image_url = img["data-src"].replace("\\", "") if img else None
    return Image(image_url)


def extract_text(resource: Resource) -> Text:
    soup = BeautifulSoup(resource.content, "html.parser")
    title = soup.find("h2", attrs={"class": "tha__title2"})
    description = soup.find("div", attrs={"class": "tha__articleText"})
    meta = soup.find(
        "div",
        attrs={
            "class": "th__article",
            "data-eid": True,
            "data-cid": True,
        },
    )

    title_text = title.get_text().strip() if title else None
    description_text = description.get_text().strip() if description else None
    metadata = Metadata(meta["data-eid"], meta["data-cid"]) if meta else None

    return Text(title_text, description_text, metadata)


class URLIterator(ABC):
    def __init__(self):
        self._increment = 0
        self.increment = 0

    def __iter__(self):
        self.increment = self._increment
        return self

    @abstractmethod
    def __next__(self):
        pass


class ArticleURLIterator(URLIterator):
    def __init__(
        self,
        eid: str,
        cid: str,
        page_type: PageType,
    ):
        super().__init__()
        self.eid = eid
        self.cid = cid
        self.page_type = page_type

    def __next__(self) -> str:
        """"""
        self.increment += 1

        params = {
            "act": APIAction.LP,
            "p": self.increment,
            "aj": AJAXIncrement.ONE,
        }

        if self.increment == 1:
            params["eid"] = self.eid
        else:
            params["cid"] = self.cid

        return sync_url_and_params(
            urljoin(TRENDHUNTER_URL, self.page_type), params
        )


class PageTypeURLIterator(URLIterator):
    def __init__(self, uid: str, page_type: PageType):
        super().__init__()
        self.uid = uid
        self.page_type = page_type

    def __next__(self) -> str:
        """"""
        # page type iterator begins at 1
        self.increment += 1

        params = {
            "act": APIAction.LP,
            "p": self.increment,
            "aj": AJAXIncrement.ONE,
            "pt": self.page_type,
            "v": self.uid,
            "t": PageType.TREND,
        }

        return sync_url_and_params(TRENDHUNTER_URL, params)


class TrendHunterAPI:
    def __init__(
        self,
        n: int,
        chunk_size: int,
        concurrency: int,
        proxy: Optional[str],
        timeout: int,
    ):
        self.n = n
        self.chunk_size = chunk_size
        self.concurrency = concurrency
        self.proxy = proxy
        self.timeout = timeout

    def __enter__(self):
        logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL + 1)

        return self

    def __exit__(self, type, value, traceback):
        pass

    def _fetch_all(
        self,
        iterator: URLIterator,
        n: Optional[int] = None,
        extra: List[List[str]] = [],
        extra_resources: List[Tuple[str]] = [],
    ) -> Generator[Article, None, None]:
        all_urls = []
        all_unique_urls = set()
        failsafe = 0
        iterator = chain(iter(extra_resources), iterator)

        while len(all_urls) < (n if n is not None else self.n):
            # fetch 3 results from the iterator at a time
            resource_urls = [next(iterator), next(iterator), next(iterator)]
            resources = asyncio.run(
                async_get_urls(
                    resource_urls,
                    self.concurrency,
                    self.proxy,
                    self.timeout,
                    propagate=True,
                )
            )

            for resource in filter(None, resources):
                limit = (n if n is not None else self.n) - len(all_urls)
                extracted_urls = extract_urls(resource)[:limit]

                for urls in extracted_urls:
                    # do not wrap in `URLPair`, would just have to
                    # be unpacked in a moment
                    url_pair = (urls.url, urls.image_url)

                    if url_pair not in all_unique_urls:
                        all_urls.append(list(url_pair))
                        all_unique_urls.add(url_pair)

            failsafe += 1

            if failsafe > 1000:
                raise ResourceError(
                    "Unable to parse out the required resources after "
                    "hitting 1000 resource pages, the failsafe mechanism to "
                    "halt the fetch has been activated."
                )

        # mix in the extra article urls and remove duplicate
        # resourced articles while maintaining order
        all_urls = extra + all_urls

        while all_urls:
            chunk_urls, all_urls = (
                all_urls[: self.chunk_size],
                all_urls[self.chunk_size :],
            )
            subresources = asyncio.run(
                async_get_urls(
                    chunk_urls, self.concurrency, self.proxy, self.timeout
                )
            )

            articles = []

            for urls, resources in zip(chunk_urls, subresources):
                # `_async_get_url` has previously logged this error
                if not (resources[0] and resources[1]):
                    continue

                text = extract_text(resources[0])
                image = Image(urls[1], resources[1].content)

                if not (text.title or text.description or text.metadata):
                    format_console(__name__).error(
                        "The title, description, or metadata was not "
                        f'parsed from "{resources[0].url}".'
                    )
                    continue

                articles.append(Article(urls[0], text, image))

            yield articles

    def _fetch_one(self, url: str) -> Optional[Text]:
        resources = asyncio.run(
            async_get_urls(
                [url],
                self.concurrency,
                self.proxy,
                self.timeout,
                propagate=True,
            )
        )

        return Article(
            url, extract_text(resources[0]), extract_image_url(resources[0])
        )

    def execute(self, uid: str, page_type: PageType):
        extra, extra_resources = [], []

        if page_type in [PageType.TREND, PageType.LIST]:
            article = self._fetch_one(
                urljoin(TRENDHUNTER_URL, f"{page_type}/{uid}")
            )

            if not article.text.metadata:
                raise ResourceError(
                    f'The metadata was not parsed from "{article.url}".'
                )

            if page_type == PageType.TREND and article.image.url:
                extra = [[article.url, article.image.url]]

            extra_resources = [article.url]

            iterator = ArticleURLIterator(
                article.text.metadata.eid,
                article.text.metadata.cid,
                page_type,
            )
        else:
            iterator = PageTypeURLIterator(uid, page_type)

        yield from self._fetch_all(
            iterator, self.n - len(extra), extra, extra_resources
        )
