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
import time
import asyncio

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


def resize_image(image: Image, size: Tuple[int]) -> BytesIO:
    im = PIL.Image.open(BytesIO(image.image)).convert("RGB")
    image_buf = BytesIO()

    im.thumbnail(size, PIL.Image.LANCZOS)
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


class TokenBucketError(Exception):
    pass


class TokenBucket:
    def __init__(self, max_bucket_size: int, rate: float) -> None:
        if max_bucket_size <= 0 or not isinstance(max_bucket_size, int):
            raise TokenBucketError(
                "Max bucket size must be a positive integer."
            )
        self.max_bucket_size = max_bucket_size

        if rate <= 0:
            raise TokenBucketError("Rate must be a positive number.")
        self.rate = rate

        self.current_bucket_size = max_bucket_size
        self.bucket_resized_at = None

    def get_current_time_in_nanoseconds(self) -> int:
        return time.time_ns()

    def resize_bucket(self) -> None:
        current_time = self.get_current_time_in_nanoseconds()

        if self.bucket_resized_at is not None:
            time_span = current_time - self.bucket_resized_at
            new_tokens = time_span * self.rate / 10**9
            combined_size = self.current_bucket_size + new_tokens
            self.current_bucket_size = min(combined_size, self.max_bucket_size)

        self.bucket_resized_at = current_time

    async def throttle(self) -> None:
        while self.current_bucket_size < 1:
            rate_per_token_in_seconds = 1 / self.rate
            min_tokens_required = 1 - self.current_bucket_size
            snooze_time = rate_per_token_in_seconds * min_tokens_required

            await asyncio.sleep(snooze_time)

            self.resize_bucket()

    async def __aenter__(self) -> None:
        self.resize_bucket()
        await self.throttle()
        self.current_bucket_size -= 1

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        # no control on exit
        pass
