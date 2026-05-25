import hashlib
from io import BytesIO
from urllib.parse import urlencode

from PIL import Image, ImageDraw, ImageFont

from django.core.files.base import ContentFile
from django.core.paginator import Paginator

from users.constants import AVATAR_FONT_SIZE, AVATAR_SIZE, AVATAR_Y_OFFSET, USERS_PER_PAGE
from users.enums import AVATAR_COLORS


def avatar_upload_to(instance: "User", filename: str):
    return f"avatars/user_{instance.pk or 'new'}.png"


def build_avatar(first_letter: str, size: int = AVATAR_SIZE):
    letter = (first_letter or "?").strip()[:1].upper() or "?"

    color_idx = int(
        hashlib.md5(letter.encode(), usedforsecurity=False).hexdigest(),
        16
    ) % len(AVATAR_COLORS)
    color = AVATAR_COLORS[color_idx]

    image = Image.new("RGB", (size, size), color)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", AVATAR_FONT_SIZE)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) / 2
    y = (size - text_height) / 2 - AVATAR_Y_OFFSET

    draw.text((x, y), letter, fill="white", font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{letter.lower()}_avatar.png")


def get_query_prefix(request, *keys: str):
    params = request.GET.copy()
    params.pop("page", None)
    allowed = {key: value for key, value in params.items() if key in keys and value}
    return f"{urlencode(allowed)}&" if allowed else ""
