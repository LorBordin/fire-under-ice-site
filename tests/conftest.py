"""Shared pytest fixtures. pytest loads this file automatically."""
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def static_dir(tmp_path: Path) -> Path:
    """A throwaway `static/` folder holding three tiny real images."""
    img = tmp_path / "static" / "img"
    img.mkdir(parents=True)
    Image.new("RGB", (800, 600)).save(img / "a-800.webp")
    Image.new("RGB", (1400, 1050)).save(img / "a-1400.webp")
    Image.new("RGBA", (100, 50)).save(img / "logo.png")
    return tmp_path / "static"
