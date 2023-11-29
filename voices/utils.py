from enum import Enum


def count_max_length(enum: Enum):
    return max((len(val) for val in enum))


def get_minify_image(image: str) -> str:
    filename = image.split("/")[-1]
    name, file_ext = filename.split(".")
    return f"https://storage.yandexcloud.net/my-city/{name}-min.{file_ext}"
