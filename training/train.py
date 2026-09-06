"""AURA-1 QLoRA training entry point.

M003: first reproducible QLoRA/SFT training pipeline.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import torch
import yaml
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
from trl import SFTConfig, SFTTrainer


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def profile_dataset(dataset: Any) -> None:
    languages: dict[str, int] = {}
    categories: dict[str, int] = {}
    message_counts: list[int] = []

    for row in dataset:
        languages[row["language"]] = languages.get(row["language"], 0) + 1
        categories[row["category"]] = categories.get(row["category"], 0) + 1
        message_counts.append(len(row["messages"]))

    print(f"Examples: {len(dataset)}")
    print(f"Languages: {languages}")
    print(f"Categories: {categories}")
    print(
        "Messages/example: "
        f"min={min(message_counts)}, max={max(message_counts)}, "
        f"avg={sum(message_counts) / len(message_counts):.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train AURA-1 with QLoRA.")
    parser.add_argument("--config", default="training/config.yaml")
    parser.add_argument("--smoke-test", action="store_true", help="Run only two optimizer steps.")
    parser.add_argument("--profile-only", action="store_true", help="Profile the dataset and exit.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    cfg = load_config(root / args.config)
    set_seed(int(cfg["seed"]))

    dataset = load_dataset(
        "json",
        data_files=str(root / cfg["train_file"]),
        split="train",
    )

    profile_dataset(dataset)
    if args.profile_only:
        return

    if not torch.cuda.is_available():
        raise RuntimeError(
            "AURA-1 M003 QLoRA training requires a CUDA-capable environment. "
            "Run this script on a supported GPU machine."
        )

    bf16 = torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if bf16 else torch.float16

    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model_name_or_path"],
        use_fast=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type=cfg["quantization"]["type"],
        bnb_4bit_use_double_quant=bool(cfg["quantization"]["double_quant"]),
        bnb_4bit_compute_dtype=compute_dtype,
    )

    model = AutoModelForCausalLM.from_pretrained(
        cfg["model_name_or_path"],
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=compute_dtype,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    lora = cfg["lora"]
    peft_config = LoraConfig(
        r=int(lora["r"]),
        lora_alpha=int(lora["alpha"]),
        lora_dropout=float(lora["dropout"]),
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )

    output_dir = root / cfg["output_dir"]
    if args.smoke_test:
        output_dir = root / cfg["smoke_test_output_dir"]

    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=float(cfg["num_train_epochs"]),
        max_steps=2 if args.smoke_test else -1,
        learning_rate=float(cfg["learning_rate"]),
        per_device_train_batch_size=int(cfg["per_device_train_batch_size"]),
        gradient_accumulation_steps=int(cfg["gradient_accumulation_steps"]),
        max_length=int(cfg["max_seq_length"]),
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
        logging_strategy="steps",
        logging_steps=1,
        save_strategy="steps",
        save_steps=int(cfg["save_steps"]),
        save_total_limit=2,
        report_to="none",
        seed=int(cfg["seed"]),
        bf16=bf16,
        fp16=not bf16,
        assistant_only_loss=True,
        packing=False,
        remove_unused_columns=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    result = trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    trainer.save_state()

    print(f"Training complete. Output: {output_dir}")
    print(f"Final metrics: {result.metrics}")


if __name__ == "__main__":
    main()
