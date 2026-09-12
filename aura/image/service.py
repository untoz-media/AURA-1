"""Backend-agnostic local image generation service for AURA-1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import time


@dataclass(frozen=True)
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20
    guidance_scale: float = 7.0
    seed: int | None = None
    output_dir: str | Path = "outputs/images"

    def validate(self) -> None:
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("O prompt da imagem não pode estar vazio.")
        if len(self.prompt) > 4000:
            raise ValueError("O prompt da imagem é demasiado longo.")
        if self.width < 256 or self.height < 256:
            raise ValueError("A resolução mínima é 256x256.")
        if self.width > 2048 or self.height > 2048:
            raise ValueError("A resolução máxima suportada pela interface é 2048x2048.")
        if self.width % 8 or self.height % 8:
            raise ValueError("A largura e altura devem ser múltiplos de 8.")
        if not 1 <= self.steps <= 100:
            raise ValueError("steps deve estar entre 1 e 100.")
        if not 1.0 <= self.guidance_scale <= 30.0:
            raise ValueError("guidance_scale deve estar entre 1.0 e 30.0.")


@dataclass(frozen=True)
class ImageGenerationResult:
    image_path: Path
    seed: int
    backend: str
    model: str
    elapsed_seconds: float


class ImageBackend(Protocol):
    """Interface implemented by local image-generation backends."""

    name: str
    model_name: str

    def generate(self, request: ImageGenerationRequest) -> tuple[object, int]:
        """Return a PIL-compatible image object and the effective seed."""
        ...


class LocalImageService:
    """Coordinates validation, output naming and backend execution."""

    def __init__(self, backend: ImageBackend) -> None:
        self.backend = backend

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        request.validate()
        output_dir = Path(request.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        started = time.perf_counter()
        image, seed = self.backend.generate(request)
        elapsed = time.perf_counter() - started

        filename = f"aura_{int(time.time())}_{seed}.png"
        output_path = output_dir / filename
        save = getattr(image, "save", None)
        if not callable(save):
            raise RuntimeError("O backend não devolveu uma imagem válida.")
        save(output_path)

        return ImageGenerationResult(
            image_path=output_path,
            seed=seed,
            backend=self.backend.name,
            model=self.backend.model_name,
            elapsed_seconds=elapsed,
        )
