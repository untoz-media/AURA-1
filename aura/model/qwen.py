"""Local Qwen runtime used by AURA-1."""

from __future__ import annotations

from collections.abc import Sequence

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from aura.config import AuraConfig


class QwenRuntime:
    """Load Qwen Instruct locally and generate contextual responses."""

    def __init__(self, config: AuraConfig | None = None) -> None:
        self.config = config or AuraConfig()
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

        quantization_config = None
        if self.config.load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type=self.config.quantization_type,
                bnb_4bit_use_double_quant=self.config.double_quant,
                bnb_4bit_compute_dtype=torch.float16,
            )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            quantization_config=quantization_config,
            device_map="auto",
            dtype=torch.float16,
        )
        self.model.eval()

    def _build_messages(
        self, conversation: Sequence[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Build a context window while preserving complete conversation turns."""
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            *conversation,
        ]

        budget = max(
            512,
            self.config.max_context_tokens - self.config.max_new_tokens,
        )
        while len(messages) > 2:
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=self.config.enable_thinking,
            )
            token_count = len(
                self.tokenizer(text, add_special_tokens=False)["input_ids"]
            )
            if token_count <= budget:
                return messages

            # Keep the system prompt and remove the oldest user+assistant turn.
            if len(messages) >= 3 and messages[1]["role"] == "user":
                del messages[1:3]
            else:
                del messages[1]

        return messages

    def generate(self, conversation: Sequence[dict[str, str]]) -> str:
        """Generate a response from the current conversation."""
        messages = self._build_messages(conversation)

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self.config.enable_thinking,
        )
        inputs = self.tokenizer(text, return_tensors="pt")
        inputs = {key: value.to(self.model.device) for key, value in inputs.items()}

        with torch.inference_mode():
            generation_kwargs = {
                "max_new_tokens": self.config.max_new_tokens,
                "do_sample": self.config.temperature > 0,
                "repetition_penalty": self.config.repetition_penalty,
                "eos_token_id": self.tokenizer.eos_token_id,
                "pad_token_id": self.tokenizer.pad_token_id,
            }
            if self.config.temperature > 0:
                generation_kwargs["temperature"] = self.config.temperature
                generation_kwargs["top_p"] = self.config.top_p

            output = self.model.generate(**inputs, **generation_kwargs)

        generated = output[0][inputs["input_ids"].shape[1] :]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()
