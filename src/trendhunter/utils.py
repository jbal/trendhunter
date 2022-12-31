"""Utilities."""

import logging
import os
from pathlib import Path
from functools import lru_cache
from io import BytesIO
from logging import Logger
from typing import Tuple, Optional
from urllib.parse import urlparse

import PIL

from trendhunter.tuples import Image


@lru_cache
def format_console(name: str) -> Logger:
    logger = logging.getLogger(name)
    logger.propagate = False
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "({asctime}) ({name}) ({levelname}) {message}",
        style="{",
        datefmt="%d-%m-%Y %H:%M",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def resize_image(image: Image, pixels: Tuple[int]) -> BytesIO:
    im = PIL.Image.open(BytesIO(image.image))
    image_buf = BytesIO()

    im.thumbnail(pixels, PIL.Image.ANTIALIAS)
    format_console(__name__).info(
        f'Resized image "{image.url}" to {im.size[0]}, {im.size[1]} (width,'
        " height)."
    )

    ext = os.path.splitext(urlparse(image.url).path)[1][1:]
    im.save(image_buf, method=6, quality=100, format=ext)

    return image_buf


def resolve_path(path: Optional[Path] = None) -> Path:
    path = path or Path(".").resolve()

    if not path.suffix:
        path.mkdir(parents=True, exist_ok=True)
        path = path / "template.pptx"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path
