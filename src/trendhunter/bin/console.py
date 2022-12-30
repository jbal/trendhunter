"""Click interface."""

import logging
from pathlib import Path
from typing import Callable, Optional, Tuple

import click
from aiohttp import ClientError
from slugify import slugify

from trendhunter.api import ResourceError, TrendHunterAPI
from trendhunter.formatters import console, slideshow
from trendhunter.taxonomies import PageType
from trendhunter.tuples import Context
from trendhunter.utils import format_console

FORMATTERS = [console, slideshow]


def catch_execute(func: Callable, *args):
    try:
        yield from func(*args)
    except (ResourceError, ClientError) as e:
        format_console(__name__).critical(f"({type(e).__name__}) {e}")


n = click.option(
    "-n",
    "n",
    default=50,
    type=click.INT,
    help=(
        "Number of articles. The API default is to return 50 articles "
        "matching the provided uid, but the `n` option is used to "
        "customize this value."
    ),
    show_default=True,
)

chunk_size = click.option(
    "-k",
    "--chunksize",
    "chunk_size",
    default=100,
    type=click.INT,
    help=(
        "Size of a simultaneously-processed article chunk. The API default is "
        "to process 100 articles at one time. Decrease this value to "
        "reduce memory usage."
    ),
    show_default=True,
)

concurrency = click.option(
    "-c",
    "--concurrency",
    "concurrency",
    default=5,
    type=click.INT,
    help=(
        "Number of concurrent requests. The API default is to send 5 "
        "concurrent requests, but can be increased to 100. You may want to "
        "limit concurrency to avoid 429 errors on the TrendHunter API."
    ),
    show_default=True,
)

proxy = click.option(
    "-y",
    "--proxy",
    "proxy",
    type=click.STRING,
    help=(
        "The HTTP url of a proxy server. The API default is to not use a "
        "proxy server, but if the TrendHunter API bans your IP address, you "
        "can provide one here. Please try to use a VPN before resorting to "
        "using a proxy server. If you do need to use a proxy, please be aware "
        "of the considerable risk if the provider is not secure."
    ),
)

timeout = click.option(
    "-t",
    "--timeout",
    "timeout",
    default=10,
    type=click.INT,
    help=(
        "Number of seconds until a request times out. The API default is to "
        "allow 10 seconds for a request to complete. If you are receiving "
        "several timeout exceptions, try to increaase this value."
    ),
    show_default=True,
)

format = click.option(
    "-f",
    "--format",
    "format",
    default="0",
    type=click.Choice(["0", "1"]),
    help=(
        "The output format. The API default (0) is to format the output to the"
        " console. If the user would prefer to output the details to a"
        " PowerPoint file, the 1 value can be used."
    ),
    show_default=True,
)

log_level = click.option(
    "-l",
    "--loglevel",
    "log_level",
    default=str(logging.INFO),
    type=click.Choice(
        [
            str(logging.DEBUG),
            str(logging.INFO),
            str(logging.WARNING),
            str(logging.ERROR),
            str(logging.CRITICAL),
        ]
    ),
    help=(
        "The log level of the root Python logger. The API default is to "
        "log anything at or above the INFO level. Decrease the value to "
        "view more verbose logs."
    ),
    show_default=True,
)

path = click.option(
    "-p",
    "--path",
    "path",
    type=click.Path(
        file_okay=True,
        dir_okay=True,
        readable=False,
        writable=True,
        resolve_path=True,
        path_type=Path,
    ),
    help=(
        "The path to write any output files. If one is not "
        "passed, the output path will be the current path."
    ),
)

pixels = click.option(
    "-x",
    "--pixels",
    "pixels",
    default=(300, 300),
    type=click.Tuple([int, int]),
    nargs=2,
    help=(
        "The maximum resolution of any created image files. The API "
        "default is to limit a thumbnail to a dimension of (300, 300). "
        "If an image is not equal in width and height "
        "dimension, the increase in resolution will be halted when "
        "the aspect ratio forces the larger dimension to hit "
        "the boundary specified here."
    ),
    show_default=True,
)

uid = click.argument("uid")


@click.group()
def cli() -> None:
    pass


@cli.command()
@n
@chunk_size
@concurrency
@proxy
@timeout
@format
@log_level
@path
@pixels
@uid
def search(
    n: int,
    chunk_size: int,
    concurrency: int,
    proxy: Optional[str],
    timeout: int,
    format: str,
    log_level: str,
    path: Optional[Path],
    pixels: Tuple[int],
    uid: str,
):
    logging.basicConfig(level=int(log_level))
    formatters = set([FORMATTERS[0], FORMATTERS[int(format)]])
    context = Context(slugify(uid), PageType.SEARCH, pixels, path)

    with TrendHunterAPI(n, chunk_size, concurrency, proxy, timeout) as api:
        for articles in catch_execute(
            api.execute,
            context.uid,
            context.page_type,
        ):
            for formatter in formatters:
                formatter(articles, context)


@cli.command()
@n
@chunk_size
@concurrency
@proxy
@timeout
@format
@log_level
@path
@pixels
@uid
def categories(
    n: int,
    chunk_size: int,
    concurrency: int,
    proxy: Optional[str],
    timeout: int,
    format: str,
    log_level: str,
    path: Optional[Path],
    pixels: Tuple[int],
    uid: str,
):
    logging.basicConfig(level=int(log_level))
    formatters = set([FORMATTERS[0], FORMATTERS[int(format)]])
    context = Context(
        slugify(uid, separator=""), PageType.CATAGORY, pixels, path
    )

    with TrendHunterAPI(n, chunk_size, concurrency, proxy, timeout) as api:
        for articles in catch_execute(
            api.execute, context.uid, context.page_type
        ):
            for formatter in formatters:
                formatter(articles, context)


@cli.command()
@n
@chunk_size
@concurrency
@proxy
@timeout
@format
@log_level
@path
@pixels
@uid
def lists(
    n: int,
    chunk_size: int,
    concurrency: int,
    proxy: Optional[str],
    timeout: int,
    format: str,
    log_level: str,
    path: Optional[Path],
    pixels: Tuple[int],
    uid: str,
):
    logging.basicConfig(level=int(log_level))
    formatters = set([FORMATTERS[0], FORMATTERS[int(format)]])
    context = Context(slugify(uid), PageType.LIST, pixels, path)

    with TrendHunterAPI(n, chunk_size, concurrency, proxy, timeout) as api:
        for articles in catch_execute(
            api.execute, context.uid, context.page_type
        ):
            for formatter in formatters:
                formatter(articles, context)


@cli.command()
@n
@chunk_size
@concurrency
@proxy
@timeout
@format
@log_level
@path
@pixels
@uid
def trends(
    n: int,
    chunk_size: int,
    concurrency: int,
    proxy: Optional[str],
    timeout: int,
    format: str,
    log_level: str,
    path: Optional[Path],
    pixels: Tuple[int],
    uid: str,
):
    logging.basicConfig(level=int(log_level))
    formatters = set([FORMATTERS[0], FORMATTERS[int(format)]])
    context = Context(slugify(uid), PageType.TREND, pixels, path)

    with TrendHunterAPI(n, chunk_size, concurrency, proxy, timeout) as api:
        for articles in catch_execute(
            api.execute, context.uid, context.page_type
        ):
            for formatter in formatters:
                formatter(articles, context)
