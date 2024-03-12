"""Core API code."""

import asyncio
import logging
import requests
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
from trendhunter.utils import format_console, TokenBucket

STATIC_URL = "https://cdn.trendhunterstatic.com/thumbs/"
BASE_URL = "https://www.trendhunter.com/"


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
    bucket: Optional[TokenBucket],
) -> Optional[Resource]:
    async with semaphore:
        try:
            format_console(__name__).info(
                f'Downloading content from "{url}"...'
            )
            _request = session.get(
                url,
                proxy=proxy,
                allow_redirects=False,
                timeout=timeout,
                raise_for_status=True,
            )

            if bucket:
                async with bucket:
                    async with _request as resp:
                        content = await resp.read()
            else:
                async with _request as resp:
                    content = await resp.read()

            if not (content.find(b'{"success":true,"data":""}') == -1):
                raise ResourceError(f'No content retrieved from "{url}".')

            return Resource(url, content)
        except (ClientError, ResourceError, TimeoutError) as e:
            # try to monkey patch with requests
            try:
                if bucket:
                    async with bucket:
                        requests_res = requests.get(url)
                else:
                    requests_res = requests.get(url)
            except:
                pass
            else:
                if requests_res.status_code == 200:
                    return Resource(url, requests_res.text)

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
    bucket: Optional[TokenBucket],
) -> Union[List[Resource], Resource]:
    if isinstance(urls, (list, tuple)):
        resources = []

        for url in urls:
            resources.append(
                await _async_get_url(
                    url, semaphore, session, proxy, timeout, propagate, bucket
                )
            )

        return resources
    else:
        return await _async_get_url(
            urls, semaphore, session, proxy, timeout, propagate, bucket
        )


async def async_get_urls(
    urls: Union[List[List[str]], List[Tuple[str]], List[str]],
    concurrency: int,
    proxy: Optional[str],
    timeout: int,
    propagate: bool = False,
    bucket: Optional[TokenBucket] = None,
) -> Union[List[List[Resource]], List[Resource]]:
    semaphore = Semaphore(concurrency)

    async with ClientSession() as session:
        tasks = [
            _async_bridge(
                url, semaphore, session, proxy, timeout, propagate, bucket
            )
            for url in urls
        ]
        return await asyncio.gather(*tasks)


def extract_urls(resource: Resource) -> List[URLPair]:
    soup = BeautifulSoup(resource.content, "html.parser")

    def href_contains_trends(href):
        return not (href.replace("\\", "").find("/trends/") == -1)

    urls = []
    elements = soup.find_all(
        "a",
        attrs={"class": "thar", "href": href_contains_trends, "data-id": True},
    )

    for element in elements:
        url = urljoin(BASE_URL, element["href"].replace("\\", ""))
        image_url = urljoin(
            STATIC_URL,
            "{}/{}.jpeg".format(
                element["data-id"][:3], url.rsplit("/", 1)[-1]
            ),
        )
        urls.append(URLPair(url, image_url))

    return urls


def extract_image_url_only(resource: Resource) -> Image:
    soup = BeautifulSoup(resource.content, "html.parser")
    body = soup.find(
        "body", attrs={"class": "th ", "data-url": True, "data-id": True}
    )
    image_url = None

    if body:
        image_url = urljoin(
            STATIC_URL,
            "{}/{}.jpeg".format(
                body["data-id"][:3], body["data-url"].rsplit("/")[-1]
            ),
        )

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
    def __init__(self, eid: str, cid: str):
        super().__init__()
        self.eid = eid
        self.cid = cid

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

        return sync_url_and_params(urljoin(BASE_URL, PageType.TREND), params)


class PageTypeURLIterator(URLIterator):
    def __init__(self, uid: str, page_type: PageType, is_best: bool):
        super().__init__()
        self.uid = uid
        self.page_type = page_type
        self.is_best = is_best

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

        if self.is_best:
            params["s"] = "best"

        return sync_url_and_params(BASE_URL, params)


class TrendHunterAPI:
    def __init__(
        self,
        concurrency: int,
        proxy: Optional[str],
        timeout: int,
        bucket: Optional[TokenBucket] = None,
    ):
        self.concurrency = concurrency
        self.proxy = proxy
        self.timeout = timeout
        self.bucket = bucket

    def __enter__(self):
        logging.getLogger("asyncio").setLevel(logging.CRITICAL + 1)
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL + 1)

        return self

    def __exit__(self, type, value, traceback):
        pass

    def _fetch_all(
        self,
        iterator: URLIterator,
        n: int,
        m: int,
        all_urls: set,
        extra: List[List[str]],
        extra_resources: List[Tuple[str]],
    ) -> Generator[Article, None, None]:
        urls = []
        iterator = chain(iter(extra_resources), iterator)

        while len(urls) < n:
            # fetch 3 results from the iterator at a time
            resource_urls = [next(iterator), next(iterator), next(iterator)]
            resources = asyncio.run(
                async_get_urls(
                    resource_urls,
                    self.concurrency,
                    self.proxy,
                    self.timeout,
                    propagate=True,
                    bucket=self.bucket,
                )
            )

            for resource in filter(None, resources):
                limit = n - len(urls)
                extracted_urls = extract_urls(resource)[:limit]

                for extracted_url in extracted_urls:
                    if extracted_url.url not in all_urls:
                        urls.append(
                            [extracted_url.url, extracted_url.image_url]
                        )
                        all_urls.add(extracted_url.url)

        # mix in the extra article urls and remove duplicate
        # resourced articles while maintaining order
        urls = extra + urls

        while urls:
            chunked_urls, urls = urls[:m], urls[m:]
            subresources = asyncio.run(
                async_get_urls(
                    chunked_urls,
                    self.concurrency,
                    self.proxy,
                    self.timeout,
                    bucket=self.bucket,
                )
            )

            articles = []

            for chunked_url, resources in zip(chunked_urls, subresources):
                # `_async_get_url` has previously logged this error
                if not (resources[0] and resources[1]):
                    continue

                text = extract_text(resources[0])
                image = Image(chunked_url[1], resources[1].content)

                if not (text.title or text.description or text.metadata):
                    format_console(__name__).error(
                        "The title, description, or metadata was not "
                        f'parsed from "{resources[0].url}".'
                    )
                    continue

                articles.append(Article(chunked_url[0], text, image))

            yield articles

    def _fetch_one(self, url: str) -> Optional[Text]:
        resources = asyncio.run(
            async_get_urls(
                [url],
                self.concurrency,
                self.proxy,
                self.timeout,
                propagate=True,
                bucket=self.bucket,
            )
        )

        return Article(
            url,
            extract_text(resources[0]),
            extract_image_url_only(resources[0]),
        )

    def execute(
        self,
        uid: str,
        page_type: PageType,
        n: int,
        m: int,
        urls: set,
        is_best: bool = False,
    ):
        extra, extra_resources = [], []

        if page_type in [PageType.TREND, PageType.LIST]:
            article = self._fetch_one(urljoin(BASE_URL, f"{page_type}/{uid}"))

            if not article.text.metadata:
                raise ResourceError(
                    f'The metadata was not parsed from "{article.url}".'
                )

            if (
                page_type == PageType.TREND
                and article.image.url
                and article.url not in urls
            ):
                extra = [[article.url, article.image.url]]

            extra_resources = [article.url]

            iterator = ArticleURLIterator(
                article.text.metadata.eid,
                article.text.metadata.cid,
            )
        else:
            iterator = PageTypeURLIterator(uid, page_type, is_best)

        yield from self._fetch_all(
            iterator, n - len(extra), m, urls, extra, extra_resources
        )
