# core/enums.py
from enum import StrEnum


class AvatarColor(StrEnum):
    BLUE = "#2563EB"
    PURPLE = "#7C3AED"
    PINK = "#DB2777"
    ORANGE = "#EA580C"
    GREEN = "#16A34A"
    CYAN = "#0891B2"


# Коллекция всех цветов для аватаров
AVATAR_COLORS = [
    AvatarColor.BLUE,
    AvatarColor.PURPLE,
    AvatarColor.PINK,
    AvatarColor.ORANGE,
    AvatarColor.GREEN,
    AvatarColor.CYAN,
]
