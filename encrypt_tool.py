from collections.abc import Iterator
from pathlib import Path

from PIL import Image, ImageOps


def _hilbert_indices(width: int, height: int) -> Iterator[int]:
    """Visit a rectangle in Hilbert order, clipping empty square quadrants."""
    side = 1 << (max(width, height) - 1).bit_length()

    def walk(x: int, y: int, ax: int, ay: int, bx: int, by: int, size: int):
        if size == 1:
            if 0 <= x < width and 0 <= y < height:
                yield y * width + x
            return

        end_x = x + (size - 1) * (ax + bx)
        end_y = y + (size - 1) * (ay + by)
        if (
            min(x, end_x) >= width
            or max(x, end_x) < 0
            or min(y, end_y) >= height
            or max(y, end_y) < 0
        ):
            return

        half = size // 2
        yield from walk(x, y, bx, by, ax, ay, half)
        yield from walk(x + half * bx, y + half * by, ax, ay, bx, by, half)
        yield from walk(
            x + half * (ax + bx), y + half * (ay + by), ax, ay, bx, by, half
        )
        yield from walk(
            x + (size - 1) * ax + (half - 1) * bx,
            y + (size - 1) * ay + (half - 1) * by,
            -bx,
            -by,
            -ax,
            -ay,
            half,
        )

    yield from walk(0, 0, 1, 0, 0, 1, side)


def _transform_image(image_path: str | Path, decrypt: bool) -> Path:
    source_path = Path(image_path)
    operation = "decrypt" if decrypt else "encrypt"
    output_path = source_path.with_name(f"{source_path.stem}_{operation}.png")

    with Image.open(source_path) as source:
        if getattr(source, "is_animated", False):
            raise ValueError("暂不支持动图，请使用静态图片")
        with ImageOps.exif_transpose(source) as normalized:
            if (
                normalized.mode not in {"L", "LA", "RGB", "RGBA"}
                or "transparency" in normalized.info
            ):
                has_alpha = (
                    "A" in normalized.getbands() or "transparency" in normalized.info
                )
                image = normalized.convert("RGBA" if has_alpha else "RGB")
            else:
                image = normalized.copy()

    with image:
        width, height = image.size
        channels = len(image.getbands())
        pixels = memoryview(image.tobytes())
        output = bytearray(len(pixels))
        for index, curve_index in enumerate(_hilbert_indices(width, height)):
            linear_offset = index * channels
            curve_offset = curve_index * channels
            if decrypt:
                output[linear_offset : linear_offset + channels] = pixels[
                    curve_offset : curve_offset + channels
                ]
            else:
                output[curve_offset : curve_offset + channels] = pixels[
                    linear_offset : linear_offset + channels
                ]

        with Image.frombytes(image.mode, image.size, bytes(output)) as result:
            result.save(output_path, format="PNG")

    return output_path


def encrypt_image(image_path: str | Path) -> Path:
    """Scramble static image pixels along a Hilbert curve into an _encrypt PNG."""
    return _transform_image(image_path, decrypt=False)


def decrypt_image(image_path: str | Path) -> Path:
    """Reverse encrypt_image and save a _decrypt PNG without resizing pixels."""
    return _transform_image(image_path, decrypt=True)
