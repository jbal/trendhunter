import re
from functools import partial
from io import BytesIO
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Union

from bs4 import BeautifulSoup
from PIL import Image

from trendhunter.taxonomies import APIAction


class Decompose(NamedTuple):
    tag: str
    attrs: Optional[Dict] = None


class AIOResponse(NamedTuple):
    url: Union[str, re.Pattern]
    status: int
    repeat: bool
    body: bytes


def image() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x1e\x00"
        b"\x00\x00\x1e\x08\x02\x00\x00\x00\xb4R9\xf5\x00\x00\x00"
        b"\x1aIDATx\x9c\xed\xc11\x01\x00\x00\x00\xc2\xa0\xf5Om\r"
        b"\x0f\xa0\x00\x00\xe0\xd1\x00\n\xaa\x00\x01&\x87E\x9e"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def read_html(name: str, decompose: List[Decompose] = []) -> str:
    data_path = Path(__file__).parent / "data" / name
    with data_path.open() as f:
        if decompose:
            soup = BeautifulSoup(f, "html.parser")

            for item in decompose:
                for tag in soup.find_all(*item):
                    tag.decompose()

            return str(soup)
        else:
            return f.read()


CDN = partial(
    AIOResponse,
    url=re.compile(r"^https://cdn\.trendhunterstatic\.com/.*$"),
    status=200,
    repeat=True,
    body=image(),
)
Trends = partial(
    AIOResponse,
    url=re.compile(r"^https://www.trendhunter\.com/trends/[^\?]*$"),
    status=200,
    repeat=True,
    body=read_html("A.html"),
)
Lists = partial(
    AIOResponse,
    url=re.compile(r"^https://www.trendhunter\.com/slideshow/[^\?]*$"),
    status=200,
    repeat=True,
    body=read_html("B.html"),
)
API = partial(
    AIOResponse,
    url=re.compile(
        rf"^https://www.trendhunter\.com/(?![^\?]*trends).*\?.*act={APIAction.LP}.*$"
    ),
    status=200,
    repeat=True,
    body=read_html("C.html"),
)
TrendsAPI = partial(
    AIOResponse,
    url=re.compile(
        rf"^https://www.trendhunter\.com/trends.*\?.*act={APIAction.LP}.*$"
    ),
    status=200,
    repeat=True,
    body=read_html("D.html"),
)
