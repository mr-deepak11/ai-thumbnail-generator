from imagekitio import ImageKit

from config import IMAGEKIT_PRIVATE_KEY

imagekit = (
    ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)
    if IMAGEKIT_PRIVATE_KEY
    else None
)


def upload_file(
    file_bytes: bytes,
    file_name: str,
    folder: str = "",
) -> str:
    if imagekit is None:
        raise RuntimeError(
            "IMAGEKIT_PRIVATE_KEY is missing from backend/.env."
        )

    result = imagekit.files.upload(
        file=file_bytes,
        file_name=file_name,
        folder=folder,
        use_unique_file_name=True,
    )

    return result.url


def get_variants(base_url: str):

    return {
        "youtube": f"{base_url}?tr=w-1280,h-720",
        "shorts": f"{base_url}?tr=w-1080,h-1920",
        "square": f"{base_url}?tr=w-1080,h-1080",
    }