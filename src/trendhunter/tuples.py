"""Tuples."""

from pathlib import Path
from typing import NamedTuple, Optional, Tuple

from trendhunter.taxonomies import PageType


class Image(NamedTuple):

    url: Optional[str] = None
    image: Optional[bytes] = None


class Metadata(NamedTuple):
    """Article id and category id."""

    eid: str
    cid: str


class Text(NamedTuple):

    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Metadata] = None


class Article(NamedTuple):
    """Article title, description, metadata, and image."""

    url: str
    text: Text
    image: Image


class URLPair(NamedTuple):

    url: str
    image_url: str


class Resource(NamedTuple):
    """HTML resource, including text and url."""

    url: str
    content: str


class Context(NamedTuple):

    size: Tuple[int]
    path: Optional[Path] = None
