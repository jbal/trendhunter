""""""

from io import BytesIO
from itertools import chain
from typing import List
from urllib.parse import urljoin

import PIL
import pytest
from aiohttp import ClientError
from aioresponses import aioresponses

from tests.utils import (
    API,
    CDN,
    AIOResponse,
    Lists,
    Trends,
    TrendsAPI,
)
from trendhunter.api import BASE_URL, TrendHunterAPI
from trendhunter.taxonomies import PageType
from trendhunter.tuples import Article, Image, Metadata, Text


def image():
    im = PIL.Image.new(mode="RGB", size=(30, 30))
    image_buf = BytesIO()
    im.save(image_buf, "PNG")
    return image_buf.getvalue()


def TestArticle(uid: str) -> Article:
    return Article(
        url=urljoin(BASE_URL, f"trends/{uid}"),
        text=Text("test", "test", Metadata("test", "test")),
        image=Image(f"https://cdn.trendhunterstatic.com/{uid}", image()),
    )


def assert_articles(a: List[List[Article]], b: List[List[Article]]):
    assert len(a) == len(b)

    for chunk_a, chunk_b in zip(a, b):
        assert len(chunk_a) == len(chunk_b)

    for article_a, article_b in zip(
        chain.from_iterable(a), chain.from_iterable(b)
    ):
        assert article_a.url == article_b.url
        assert article_a.text == article_b.text
        assert article_a.image == article_b.image


def add_responses(
    m,
    cdn: AIOResponse = CDN(),
    trends: AIOResponse = Trends(),
    lists: AIOResponse = Lists(),
    api: AIOResponse = API(),
    trends_api: AIOResponse = TrendsAPI(),
    extra: List[AIOResponse] = [],
):
    for mocked in [cdn, trends, lists, api, trends_api] + extra:
        m.get(
            url=mocked.url,
            status=mocked.status,
            repeat=mocked.repeat,
            body=mocked.body,
        )


def test_api_001():
    expected = [
        [
            TestArticle("#AA0"),
            TestArticle("#A0"),
            TestArticle("#A1"),
            TestArticle("#A2"),
            TestArticle("#A3"),
        ]
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.TREND, 5, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_002():
    expected = [
        [
            TestArticle("#AA0"),
            TestArticle("#A0"),
            TestArticle("#A1"),
        ],
        [
            TestArticle("#A2"),
            TestArticle("#A3"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.TREND, 5, 3, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_003():
    expected = [
        [
            TestArticle("#AA0"),
            TestArticle("#A0"),
            TestArticle("#A1"),
            TestArticle("#A2"),
            TestArticle("#A3"),
        ],
        [
            TestArticle("#A4"),
            TestArticle("#A5"),
            TestArticle("#D0"),
            TestArticle("#D1"),
            TestArticle("#D2"),
        ],
        [
            TestArticle("#D3"),
            TestArticle("#D4"),
            TestArticle("#D5"),
            TestArticle("#D6"),
            TestArticle("#D7"),
        ],
        [
            TestArticle("#D8"),
            TestArticle("#D9"),
            TestArticle("#D10"),
            TestArticle("#D11"),
            TestArticle("#D12"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.TREND, 20, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_004():
    with aioresponses() as m:
        add_responses(m, trends=Trends(status=404))
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            with pytest.raises(ClientError):
                for chunk_of_articles in api.execute(
                    "#AA0", PageType.TREND, 5, 5, set()
                ):
                    articles.append(chunk_of_articles)


def test_api_005():
    expected = [
        [
            TestArticle("#B0"),
            TestArticle("#B1"),
            TestArticle("#B2"),
            TestArticle("#B3"),
            TestArticle("#B4"),
        ]
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.LIST, 5, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_006():
    expected = [
        [
            TestArticle("#B0"),
            TestArticle("#B1"),
            TestArticle("#B2"),
        ],
        [
            TestArticle("#B3"),
            TestArticle("#B4"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.LIST, 5, 3, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_007():
    expected = [
        [
            TestArticle("#B0"),
            TestArticle("#B1"),
            TestArticle("#B2"),
            TestArticle("#B3"),
            TestArticle("#B4"),
        ],
        [
            TestArticle("#B5"),
            TestArticle("#B6"),
            TestArticle("#B7"),
            TestArticle("#B8"),
            TestArticle("#B9"),
        ],
        [
            TestArticle("#B10"),
            TestArticle("#B11"),
            TestArticle("#B12"),
            TestArticle("#B13"),
            TestArticle("#B14"),
        ],
        [
            TestArticle("#B15"),
            TestArticle("#B16"),
            TestArticle("#B17"),
            TestArticle("#B18"),
            TestArticle("#B19"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.LIST, 20, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_008():
    with aioresponses() as m:
        add_responses(m, lists=Lists(status=404))
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            with pytest.raises(ClientError):
                for chunk_of_articles in api.execute(
                    "#AA0", PageType.LIST, 5, 5, set()
                ):
                    articles.append(chunk_of_articles)


def test_api_009():
    expected = [
        [
            TestArticle("#C0"),
            TestArticle("#C1"),
            TestArticle("#C2"),
            TestArticle("#C3"),
            TestArticle("#C4"),
        ]
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.CATAGORY, 5, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_010():
    expected = [
        [
            TestArticle("#C0"),
            TestArticle("#C1"),
            TestArticle("#C2"),
        ],
        [
            TestArticle("#C3"),
            TestArticle("#C4"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.CATAGORY, 5, 3, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_011():
    expected = [
        [
            TestArticle("#C0"),
            TestArticle("#C1"),
            TestArticle("#C2"),
            TestArticle("#C3"),
            TestArticle("#C4"),
        ],
        [
            TestArticle("#C5"),
            TestArticle("#C6"),
            TestArticle("#C7"),
            TestArticle("#C8"),
            TestArticle("#C9"),
        ],
        [
            TestArticle("#C10"),
            TestArticle("#C11"),
            TestArticle("#C12"),
            TestArticle("#C13"),
            TestArticle("#C14"),
        ],
        [
            TestArticle("#C15"),
            TestArticle("#C16"),
            TestArticle("#C17"),
            TestArticle("#C18"),
            TestArticle("#C19"),
        ],
        [
            TestArticle("#C20"),
            TestArticle("#C21"),
            TestArticle("#C22"),
            TestArticle("#C23"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.CATAGORY, 24, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_012():
    with aioresponses() as m:
        add_responses(m, api=API(status=404))
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            with pytest.raises(ClientError):
                for chunk_of_articles in api.execute(
                    "#AA0", PageType.CATAGORY, 5, 5, set()
                ):
                    articles.append(chunk_of_articles)


def test_api_013():
    expected = [
        [
            TestArticle("#C0"),
            TestArticle("#C1"),
            TestArticle("#C2"),
            TestArticle("#C3"),
            TestArticle("#C4"),
        ]
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.SEARCH, 5, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_014():
    expected = [
        [
            TestArticle("#C0"),
            TestArticle("#C1"),
            TestArticle("#C2"),
        ],
        [
            TestArticle("#C3"),
            TestArticle("#C4"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.SEARCH, 5, 3, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_015():
    expected = [
        [
            TestArticle("#C0"),
            TestArticle("#C1"),
            TestArticle("#C2"),
            TestArticle("#C3"),
            TestArticle("#C4"),
        ],
        [
            TestArticle("#C5"),
            TestArticle("#C6"),
            TestArticle("#C7"),
            TestArticle("#C8"),
            TestArticle("#C9"),
        ],
        [
            TestArticle("#C10"),
            TestArticle("#C11"),
            TestArticle("#C12"),
            TestArticle("#C13"),
            TestArticle("#C14"),
        ],
        [
            TestArticle("#C15"),
            TestArticle("#C16"),
            TestArticle("#C17"),
            TestArticle("#C18"),
            TestArticle("#C19"),
        ],
        [
            TestArticle("#C20"),
            TestArticle("#C21"),
            TestArticle("#C22"),
            TestArticle("#C23"),
        ],
    ]

    with aioresponses() as m:
        add_responses(m)
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            for chunk_of_articles in api.execute(
                "#AA0", PageType.SEARCH, 24, 5, set()
            ):
                articles.append(chunk_of_articles)

    assert_articles(articles, expected)


def test_api_016():
    with aioresponses() as m:
        add_responses(m, api=API(status=404))
        articles = []

        with TrendHunterAPI(concurrency=5, proxy=None, timeout=10) as api:
            with pytest.raises(ClientError):
                for chunk_of_articles in api.execute(
                    "#AA0", PageType.SEARCH, 5, 5, set()
                ):
                    articles.append(chunk_of_articles)
