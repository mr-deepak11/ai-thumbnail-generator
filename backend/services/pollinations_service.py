from urllib.parse import quote

import httpx

POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt/"
POLLINATIONS_IMAGE_MODEL = "flux"


async def generate_thumbnail(
    prompt: str,
    style_prompt: str,
) -> bytes:

    full_prompt = (
        f"{style_prompt}\n\n"
        f"Video topic: {prompt}\n\n"
        "Professional YouTube thumbnail. "
        "Viral and high click-through-rate design. "
        "Large main subject occupying most of the frame. "
        "Strong focal point. "
        "Bold composition. "
        "High contrast. "
        "Dramatic cinematic lighting. "
        "Bright vibrant colors. "
        "Ultra detailed. "
        "Attention grabbing. "
        "Professional creator style. "
        "Leave empty space for title text overlay. "
        "No watermark. "
        "No logo. "
        "16:9 aspect ratio. "
        "Thumbnail optimized for YouTube."
    )

    async with httpx.AsyncClient(timeout=120.0) as http_client:
        response = await http_client.get(
            f"{POLLINATIONS_IMAGE_URL}{quote(full_prompt, safe='')}",
            params={
                "model": POLLINATIONS_IMAGE_MODEL,
                "width": 1280,
                "height": 720,
                "seed": 42,
            },
            follow_redirects=True,
        )

    if not response.is_success:
        raise RuntimeError(
            f"Pollinations image request failed ({response.status_code}): "
            f"{response.text[:500]}"
        )

    content_type = response.headers.get("content-type", "")

    if not content_type.startswith("image/"):
        raise ValueError(
            "Pollinations did not return image data."
        )

    return response.content