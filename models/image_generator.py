"""Image generation module using diffusers Stable Diffusion pipeline."""

from __future__ import annotations

import os
from typing import Callable, Optional

import torch
from diffusers import StableDiffusionPipeline


class ImageGenerator:
    """Wrapper around Stable Diffusion pipeline."""

    _model_name_map = {
        "Demo Mode": "CompVis/stable-diffusion-v1-4",
        "Stable Diffusion v1.5": "runwayml/stable-diffusion-v1-5",
        "Stable Diffusion v2.1": "stabilityai/stable-diffusion-2-1",
        "Stable Diffusion XL": "stabilityai/stable-diffusion-xl-base-1.0",
        "Waifu Diffusion (Аниме)": "hakurei/waifu-diffusion",
        "Realistic Vision v4.0": "SG161222/Realistic_Vision_V4.0",
        "DreamShaper v8": "Lykon/DreamShaper-v8",
    }

    def __init__(self, device: Optional[str] = None, models_dir: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.models_dir = models_dir or os.path.join(os.getcwd(), "hf_models")
        os.makedirs(self.models_dir, exist_ok=True)
        self.pipe: Optional[StableDiffusionPipeline] = None
        self.current_model = None

    def load_model(self, name: str) -> bool:
        model_id = self._model_name_map.get(name, name)
        try:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                model_id,
                cache_dir=self.models_dir,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
            if self.device == "cuda":
                self.pipe.to("cuda")
            self.current_model = name
            return True
        except Exception:
            self.pipe = None
            self.current_model = None
            return False

    def is_loaded(self) -> bool:
        return self.pipe is not None

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: int = 512,
        height: int = 512,
        steps: int = 50,
        guidance_scale: float = 7.5,
        style: str = "",
        callback: Optional[Callable[[float], None]] = None,
    ):
        if not self.pipe:
            raise RuntimeError("Model is not loaded")

        generator = torch.Generator(device=self.pipe.device)
        prompt_full = f"{style}, {prompt}" if style and style.lower() != "без ограничений" else prompt

        image = self.pipe(
            prompt_full,
            negative_prompt=negative_prompt or None,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]

        if callback:
            callback(1.0)
        return image
