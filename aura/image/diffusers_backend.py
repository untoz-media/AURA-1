"""Diffusers backend for local AURA-1 image generation."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .service import ImageGenerationRequest

if TYPE_CHECKING:
    from diffusers import DiffusionPipeline


class DiffusersBackend:
    """Lazy-loaded Stable Diffusion backend optimized for constrained VRAM."""

    name = "diffusers"

    def __init__(
        self,
        model_name: str = "runwayml/stable-diffusion-v1-5",
        *,
        low_vram: bool = True,
    ) -> None:
        self.model_name = model_name
        self.low_vram = low_vram
        self._pipe: DiffusionPipeline | None = None

    def _load(self):
        if self._pipe is not None:
            return self._pipe

        try:
            import torch
            from diffusers import DiffusionPipeline
        except ImportError as exc:
            raise RuntimeError(
                "A geração local de imagens requer os pacotes opcionais 'torch', 'diffusers', "
                "'transformers', 'accelerate' e 'safetensors'."
            ) from exc

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        pipe = DiffusionPipeline.from_pretrained(
            self.model_name,
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False,
        )

        if torch.cuda.is_available():
            if self.low_vram:
                try:
                    pipe.enable_model_cpu_offload()
                except Exception:
                    pipe.to("cuda")
            else:
                pipe.to("cuda")
        else:
            pipe.to("cpu")

        try:
            pipe.enable_attention_slicing()
        except Exception:
            pass
        try:
            pipe.enable_vae_slicing()
        except Exception:
            pass

        self._pipe = pipe
        return pipe

    def generate(self, request: ImageGenerationRequest):
        import torch

        pipe = self._load()
        seed = request.seed if request.seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        generator = torch.Generator(device=device).manual_seed(seed)

        result = pipe(
            prompt=request.prompt.strip(),
            negative_prompt=request.negative_prompt.strip() or None,
            width=request.width,
            height=request.height,
            num_inference_steps=request.steps,
            guidance_scale=request.guidance_scale,
            generator=generator,
        )
        if not getattr(result, "images", None):
            raise RuntimeError("O modelo terminou sem devolver uma imagem.")
        return result.images[0], seed
