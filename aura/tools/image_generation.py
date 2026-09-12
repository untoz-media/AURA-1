"""Local image generation tool for AURA-1."""

from __future__ import annotations

from dataclasses import dataclass

from aura.image.diffusers_backend import DiffusersBackend
from aura.image.service import ImageGenerationRequest, LocalImageService
from aura.tools.base import Tool


@dataclass(frozen=True)
class ImageGenerationTool(Tool):
    """Generate an image locally and return metadata for the saved file."""

    name: str = "image_generation"
    description: str = "Gera uma imagem localmente a partir de um prompt de texto."

    def run(
        self,
        *,
        prompt: str,
        negative_prompt: str = "",
        width: int | str = 512,
        height: int | str = 512,
        steps: int | str = 20,
        guidance_scale: float | str = 7.0,
        seed: int | str | None = None,
        model: str = "runwayml/stable-diffusion-v1-5",
        low_vram: bool = True,
    ) -> dict[str, object]:
        parsed_seed = None if seed in (None, "", "random") else int(seed)
        request = ImageGenerationRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=int(width),
            height=int(height),
            steps=int(steps),
            guidance_scale=float(guidance_scale),
            seed=parsed_seed,
        )
        service = LocalImageService(DiffusersBackend(model_name=model, low_vram=bool(low_vram)))
        result = service.generate(request)
        return {
            "image_path": str(result.image_path),
            "seed": result.seed,
            "backend": result.backend,
            "model": result.model,
            "elapsed_seconds": round(result.elapsed_seconds, 2),
        }
