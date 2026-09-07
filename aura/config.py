"""Runtime configuration for AURA-1."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuraConfig:
    """Default configuration for the local AURA assistant."""

    model_name: str = "Qwen/Qwen3-4B-Instruct-2507"
    language: str = "pt-PT"
    max_new_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.8
    repetition_penalty: float = 1.05
    enable_thinking: bool = False

    system_prompt: str = (
        "És AURA, a assistente de inteligência artificial da Untoz. "
        "Responde em português de Portugal por defeito. Sê útil, clara, "
        "natural e honesta. Não inventes informação quando não tens a certeza."
    )
