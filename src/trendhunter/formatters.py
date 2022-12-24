""""""

import os
from io import BytesIO
from pathlib import Path
from typing import List

from pptx import Presentation

from trendhunter.tuples import Article, Context
from trendhunter.utils import format_console, resize_image


def console(articles: List[Article], context: Context):
    for article in articles:
        format_console(__name__).debug(
            f"""Article ({article.url.rsplit("/")[-1]}) {{
    url: {{
        {article.url}
    }},
    title: {{
        {article.text.title}
    }},
    description: {{
        {article.text.description}
    }},
    metadata: {{
        id: {{
            {article.text.metadata.eid}
        }},
        category: {{
            {article.text.metadata.cid}
        }},
    }},
    image: {{
        url: {{
            {article.image.url}
        }},
        image: {{
            {article.image.image[:500]} (truncated to a maximum of 500 bytes)
        }},
    }},
}}
"""
        )


def slideshow(articles: List[Article], context: Context) -> None:
    path = (context.directory or Path(os.getcwd())) / f"{context.uid}.pptx"
    show = Presentation(path if path.exists() else None)

    title_layout = show.slide_layouts[0]
    title_slide = show.slides.add_slide(title_layout)
    title_slide.shapes.title.text = "TrendHunter Ideas & Insights"
    title_slide.shapes.placeholders[1].text = context.uid

    for article in articles:
        trend_layout = show.slide_layouts[8]
        slide = show.slides.add_slide(trend_layout)

        slide.placeholders[0].text = article.text.title
        slide.placeholders[1].insert_picture(
            resize_image(article.image, context.pixels)
        )
        slide.placeholders[2].text = article.text.description

    show.save(path)
    format_console(__name__).info(
        f'Formatted {len(articles)} articles to "{path}".'
    )
