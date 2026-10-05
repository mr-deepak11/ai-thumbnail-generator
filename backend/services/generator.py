import asyncio
import logging

from sqlmodel import Session, select

from database import engine
from models import Job, Thumbnail
from services.pollinations_service import generate_thumbnail
from services.imagekit_service import upload_file

logger = logging.getLogger(__name__)

STYLES = {
    "bold_dramatic": (
        "Create a viral YouTube thumbnail. "
        "Large main subject filling most of the frame. "
        "Extreme close-up face. "
        "High contrast lighting. "
        "Cinematic composition. "
        "Bright colors. "
        "Strong emotional impact. "
        "Professional thumbnail design. "
        "Leave space for title text overlay. "
        "Attention grabbing. "
        "High click-through-rate style."
    ),

    "clean_minimal": (
        "Create a modern YouTube thumbnail. "
        "Large clear subject. "
        "Clean composition. "
        "Bright professional lighting. "
        "Minimal distractions. "
        "Strong focus on the main subject. "
        "Professional creator style. "
        "Leave empty space for text overlay."
    ),

    "vibrant_energetic": (
        "Create a viral YouTube thumbnail. "
        "Bright saturated colors. "
        "Energetic composition. "
        "Large main subject. "
        "Dynamic perspective. "
        "High contrast. "
        "Eye-catching design. "
        "Professional YouTube creator style. "
        "Leave space for title text overlay."
    ),

    "documentary": (
        "Create a professional documentary YouTube thumbnail. "
        "National Geographic style. "
        "Large main subject. "
        "Dramatic storytelling. "
        "Cinematic realism. "
        "Leave room for title text."
    ),
}

STYLE_ORDER = [
    "bold_dramatic",
    "clean_minimal",
    "vibrant_energetic",
    "documentary",
]


async def generate_single_thumbnail(
    thumbnail_id: str,
    prompt: str,
):
    with Session(engine) as session:
        thumb = session.get(Thumbnail, thumbnail_id)

        thumb.status = "generating"

        style_name = thumb.style_name

        session.add(thumb)
        session.commit()

    style_prompt = STYLES[style_name]

    enhanced_prompt = (
        f"{prompt}. "
        "Professional YouTube thumbnail. "
        "Large main subject. "
        "High CTR. "
        "Bold composition. "
        "Strong focal point. "
        "Dramatic lighting. "
        "Vibrant colors. "
        "Attention grabbing. "
        "Leave empty space for thumbnail title."
    )

    try:
        image_byte = await generate_thumbnail(
            enhanced_prompt,
            style_prompt,
        )

        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)
            job_id = thumb.job_id

            url = upload_file(
                file_bytes=image_byte,
                file_name=f"{thumbnail_id}.jpg",
                folder=f"thumbnails/{job_id}/",
            )

        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)

            thumb.imagekit_url = url
            thumb.status = "uploaded"

            session.add(thumb)
            session.commit()

        logger.info(
            f"Thumbnail {thumbnail_id} generated and uploaded successfully."
        )

    except Exception as e:
        logger.error(
            f"Error generating thumbnail {thumbnail_id}: {e}"
        )

        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)

            thumb.status = "failed"
            thumb.error_message = str(e)[:500]

            session.add(thumb)
            session.commit()


async def process_job(job_id: str):
    with Session(engine) as session:
        job = session.get(Job, job_id)

        job.status = "processing"
        prompt = job.prompt

        session.add(job)
        session.commit()

    with Session(engine) as session:
        thumbnails = session.exec(
            select(Thumbnail).where(
                Thumbnail.job_id == job_id
            )
        )

        thumbnails_ids = [t.id for t in thumbnails]

    tasks = [
        generate_single_thumbnail(
            tid,
            prompt,
        )
        for tid in thumbnails_ids
    ]

    await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )

    with Session(engine) as session:
        thumbnails = session.exec(
            select(Thumbnail).where(
                Thumbnail.job_id == job_id
            )
        ).all()

        all_failed = all(
            t.status == "failed"
            for t in thumbnails
        )

        job = session.get(Job, job_id)

        job.status = (
            "failed"
            if all_failed
            else "completed"
        )

        session.add(job)
        session.commit()