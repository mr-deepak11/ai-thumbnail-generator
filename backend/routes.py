from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from database import engine, get_session
from models import Job, Thumbnail
from services.generator import STYLES, process_job
from services.imagekit_service import get_variants, upload_file

import asyncio
import json

router = APIRouter()


class ThumbnailResponse(BaseModel):
    id: str
    style_name: str
    status: str
    imagekit_url: str | None = None
    error_message: str | None = None
    variants: dict | None = None


class JobResponse(BaseModel):
    id: str
    prompt: str
    num_thumbnails: int
    headshot_url: str
    status: str
    thumbnails: list[ThumbnailResponse] = Field(default_factory=list)


class JobCreateRequest(BaseModel):
    prompt: str
    headshot_url: str
    num_thumbnails: int = Field(default=1, ge=1, le=3)
    style: str | None = None
    styles: list[str] | None = None


@router.post("/upload-headshot")
async def upload_headshot(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are supported.",
        )

    file_bytes = await file.read()
    file_name = file.filename or "headshot.png"

    try:
        url = upload_file(
            file_bytes=file_bytes,
            file_name=file_name,
            folder="headshots/",
        )
    except Exception as exc:  # pragma: no cover - depends on external service
        raise HTTPException(
            status_code=500,
            detail=f"Headshot upload failed: {exc}",
        ) from exc

    return {"url": url}


@router.post("/jobs")
async def create_job(payload: JobCreateRequest):
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    headshot_url = payload.headshot_url.strip()
    if not headshot_url:
        raise HTTPException(status_code=400, detail="Headshot URL is required.")

    requested_styles = payload.styles or [payload.style or "clean_minimal"]
    normalized_styles = []

    for style in requested_styles:
        style_name = str(style).strip().lower()
        if style_name in STYLES:
            normalized_styles.append(style_name)
        else:
            mapping = {
                "professional": "clean_minimal",
                "bold": "bold_dramatic",
                "cinematic": "bold_dramatic",
                "minimal": "clean_minimal",
                "energetic": "vibrant_energetic",
            }
            normalized_styles.append(mapping.get(style_name, "clean_minimal"))

    if not normalized_styles:
        normalized_styles = ["clean_minimal"]

    num_thumbnails = min(max(payload.num_thumbnails, 1), 3)
    requested_styles = normalized_styles[:num_thumbnails]
    while len(requested_styles) < num_thumbnails:
        requested_styles.append("clean_minimal")

    with Session(engine) as session:
        job = Job(
            prompt=prompt,
            num_thumbnails=num_thumbnails,
            headshot_url=headshot_url,
            status="pending",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        job_id = job.id

        for style_name in requested_styles:
            thumbnail = Thumbnail(
                job_id=job.id,
                style_name=style_name,
                status="pending",
            )
            session.add(thumbnail)

        session.commit()

    asyncio.create_task(process_job(job_id))

    return {
        "id": job_id,
        "prompt": prompt,
        "num_thumbnails": num_thumbnails,
        "headshot_url": headshot_url,
        "status": "pending",
        "thumbnails": [],
    }


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    thumbnails = session.exec(
        select(Thumbnail).where(
            Thumbnail.job_id == job_id
        )
    ).all()

    thumb_response = []

    for t in thumbnails:
        variants = (
            get_variants(t.imagekit_url)
            if t.imagekit_url
            else None
        )

        thumb_response.append(
            ThumbnailResponse(
                id=t.id,
                style_name=t.style_name,
                status=t.status,
                imagekit_url=t.imagekit_url,
                error_message=t.error_message,
                variants=variants,
            )
        )

    return JobResponse(
        id=job.id,
        prompt=job.prompt,
        num_thumbnails=job.num_thumbnails,
        headshot_url=job.headshot_url,
        status=job.status,
        thumbnails=thumb_response,
    )


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):

    async def event_generator():
        from database import engine

        sent_thumbnails = set()

        while True:
            with Session(engine) as session:

                job = session.get(Job, job_id)

                if not job:
                    yield (
                        f"event: error\n"
                        f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    )
                    return

                thumbnails = session.exec(
                    select(Thumbnail).where(
                        Thumbnail.job_id == job_id
                    )
                ).all()

                for t in thumbnails:

                    if t.id in sent_thumbnails:
                        continue

                    if t.status == "uploaded":

                        variants = get_variants(
                            t.imagekit_url
                        )

                        data = json.dumps(
                            {
                                "thumbnail_id": t.id,
                                "style_name": t.style_name,
                                "imagekit_url": t.imagekit_url,
                                "variants": variants,
                            }
                        )

                        yield (
                            f"event: thumbnail_ready\n"
                            f"data: {data}\n\n"
                        )

                        sent_thumbnails.add(t.id)

                    elif t.status == "failed":

                        data = json.dumps(
                            {
                                "thumbnail_id": t.id,
                                "style_name": t.style_name,
                                "error_message": t.error_message,
                            }
                        )

                        yield (
                            f"event: thumbnail_failed\n"
                            f"data: {data}\n\n"
                        )

                        sent_thumbnails.add(t.id)

                all_done = all(
                    t.status in ("uploaded", "failed")
                    for t in thumbnails
                )

                if (
                    all_done
                    and len(sent_thumbnails)
                    == len(thumbnails)
                ):
                    data = json.dumps(
                        {
                            "job_id": job.id,
                            "status": job.status,
                        }
                    )

                    yield (
                        f"event: job_complete\n"
                        f"data: {data}\n\n"
                    )

                    # Keep the legacy event name for older clients.
                    yield (
                        f"event: job_completed\n"
                        f"data: {data}\n\n"
                    )

                    return

                await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )