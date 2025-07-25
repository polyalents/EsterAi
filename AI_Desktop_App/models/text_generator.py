"""Text generation module using Hugging Face transformers."""

from __future__ import annotations

import os
from typing import Callable, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline


class TextGenerator:
    """Wrapper around HuggingFace text-generation pipeline."""

    _model_name_map = {
        "Demo Mode": "distilgpt2",
        "GPT-J 6B (Рекомендуется)": "EleutherAI/gpt-j-6B",
        "GPT-Neo 2.7B (Быстрая)": "EleutherAI/gpt-neo-2.7B",
        "GPT-Neo 1.3B (Легковесная)": "EleutherAI/gpt-neo-1.3B",
        "DialoGPT (Диалоги)": "microsoft/DialoGPT-medium",
    }

    def __init__(self, device: Optional[str] = None, models_dir: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.models_dir = models_dir or os.path.join(os.getcwd(), "hf_models")
        os.makedirs(self.models_dir, exist_ok=True)
        self.pipeline = None
        self.current_model = None

    def load_model(self, name: str) -> bool:
        """Load a model by friendly name."""
        model_id = self._model_name_map.get(name, name)
        try:
            self.pipeline = pipeline(
                "text-generation",
                model=model_id,
                tokenizer=model_id,
                device=0 if self.device == "cuda" else -1,
                model_kwargs={"cache_dir": self.models_dir},
            )
            self.current_model = name
            return True
        except Exception:
            self.pipeline = None
            self.current_model = None
            return False

    def is_loaded(self) -> bool:
        return self.pipeline is not None

    def generate(
        self,
        prompt: str,
        max_length: int = 200,
        temperature: float = 0.7,
        style: str = "",
        callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        if not self.pipeline:
            raise RuntimeError("Model is not loaded")

        full_prompt = f"{style}: {prompt}" if style and style.lower() != "нейтральный" else prompt

        outputs = self.pipeline(
            full_prompt,
            max_length=max_length,
            temperature=temperature,
            num_return_sequences=1,
            do_sample=True,
        )
        if callback:
            callback(1.0)
        return outputs[0]["generated_text"]
