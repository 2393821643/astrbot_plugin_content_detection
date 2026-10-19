from math import isfinite
from pathlib import Path

from PIL import Image, ImageChops, ImageOps


def _load_grayscale(image_path: str | Path, background: int) -> Image.Image:
    """Normalize orientation and flatten input transparency before encoding."""
    with Image.open(image_path) as source:
        if getattr(source, "is_animated", False):
            raise ValueError("暂不支持动图，请使用静态图片")
        with (
            ImageOps.exif_transpose(source) as normalized,
            normalized.convert("RGBA") as rgba,
            Image.new("RGBA", rgba.size, (background,) * 3 + (255,)) as base,
            Image.alpha_composite(base, rgba) as flattened,
        ):
            return flattened.convert("L")


def _add_noise(image: Image.Image, strength: float) -> Image.Image:
    """Add centered Gaussian noise while clamping grayscale values to 0..255."""
    if strength == 0:
        return image.copy()
    with Image.effect_noise(image.size, strength) as noise:
        return ImageChops.add(image, noise, offset=-128)


def create_phantom_tank(
    invisible_image_path: str | Path,
    visible_image_path: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    noise_strength: float = 10.0,
) -> Path:
    """Encode a grayscale black/white-background tank on alternating pixels.

    Even cells use black RGB and alpha=255-visible to hide on black.
    Odd cells use white RGB and alpha=invisible to hide on white.
    Add Gaussian noise to the inner image before encoding; zero disables it.
    """
    if not isfinite(noise_strength) or noise_strength < 0:
        raise ValueError("噪点强度必须是非负有限数值")
    invisible_image_path = Path(invisible_image_path)
    visible_image_path = (
        Path(visible_image_path)
        if visible_image_path
        else Path(__file__).with_name("def.png")
    )
    output_path = (
        Path(output_path).with_suffix(".png")
        if output_path
        else invisible_image_path.with_name(
            f"{invisible_image_path.stem}_phantom_tank.png"
        )
    )

    with (
        _load_grayscale(invisible_image_path, background=0) as original_invisible,
        _add_noise(original_invisible, noise_strength) as invisible,
        _load_grayscale(visible_image_path, background=255) as visible,
        visible.resize(invisible.size, Image.Resampling.LANCZOS) as resized_visible,
        ImageOps.invert(resized_visible) as visible_alpha,
        Image.new("RGBA", invisible.size, (0, 0, 0, 255)) as visible_layer,
        Image.new("RGBA", invisible.size, (255, 255, 255, 255)) as invisible_layer,
    ):
        visible_layer.putalpha(visible_alpha)
        invisible_layer.putalpha(invisible)
        width, height = invisible.size
        even_row = (bytes((255, 0)) * ((width + 1) // 2))[:width]
        odd_row = (bytes((0, 255)) * ((width + 1) // 2))[:width]
        mask_bytes = (even_row + odd_row) * (height // 2) + even_row * (height % 2)
        with (
            Image.frombytes("L", invisible.size, mask_bytes) as mask,
            Image.composite(visible_layer, invisible_layer, mask) as result,
        ):
            result.save(output_path, format="PNG")

    return output_path
