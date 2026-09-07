"""Local Qwen runtime used by AURA-1."""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from aura.config import AuraConfig


class QwenRuntime:
    """Load a Qwen instruct model and generate local responses."""

    def __init__(self, config: AuraConfig | None = None) -> None:
        self.config = config or AuraConfig()
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            device_map="auto",
            dtype=torch.float16,
        )
        self.model.eval()

    def generate(self, user_message: str) -> str:
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": user_message},
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.config.enable_thinking,
        )
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {key: value.to(self.model.device) for key, value in inputs.items()}

        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                do_sample=self.config.temperature > 0,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                repetition_penalty=self.config.repetition_penalty,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        generated = output[0][inputs["input_ids"].shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()
