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
    max_history_messages: int = 20

    # 4-bit loading keeps the local runtime practical on GPUs with limited VRAM.
    load_in_4bit: bool = True
    quantization_type: str = "nf4"
    double_quant: bool = True

    system_prompt: str = (
        "És AURA, a assistente de inteligência artificial da Untoz. "
        "Responde em português de Portugal por defeito, mas acompanha o idioma "
        "do utilizador quando fizer sentido. Sê útil, clara, natural e honesta. "
        "Não inventes informação quando não tens a certeza. "
        "Mantém as respostas proporcionais ao pedido."
    )
