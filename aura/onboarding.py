"""First-run setup and hardware compatibility checks for AURA-1."""

from __future__ import annotations

import json
import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

from aura.config import AuraConfig
from aura.settings import AuraSettings

DEFAULT_SETUP_PATH = Path("data/settings/first_run.json")
VALID_PROFILES = {"fast", "balanced", "deep"}
MIN_RAM_GB = 8.0
RECOMMENDED_RAM_GB = 16.0
MIN_FREE_DISK_GB = 12.0
RECOMMENDED_FREE_DISK_GB = 20.0
RECOMMENDED_VRAM_GB = 4.0


class OnboardingManager:
    """Persist first-run choices without loading the language model."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        path: str | Path = DEFAULT_SETUP_PATH,
        *,
        settings_factory=AuraSettings,
    ) -> None:
        self.path = Path(path)
        self.settings_factory = settings_factory
        self.data: dict[str, Any] = {
            "completed": False,
            "profile": "balanced",
            "privacy_acknowledged": False,
            "permission_boundary_acknowledged": False,
            "completed_at": None,
        }
        self.load()

    @property
    def completed(self) -> bool:
        return bool(self.data.get("completed"))

    @property
    def profile(self) -> str:
        profile = self.data.get("profile")
        return profile if profile in VALID_PROFILES else "balanced"

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(loaded, dict):
            return

        profile = loaded.get("profile")
        if profile in VALID_PROFILES:
            self.data["profile"] = profile
        for key in (
            "completed",
            "privacy_acknowledged",
            "permission_boundary_acknowledged",
        ):
            value = loaded.get(key)
            if isinstance(value, bool):
                self.data[key] = value
        completed_at = loaded.get("completed_at")
        if isinstance(completed_at, str) or completed_at is None:
            self.data["completed_at"] = completed_at

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"_setup_version": self.SCHEMA_VERSION, **self.data}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def complete(
        self,
        *,
        profile: str,
        privacy_acknowledged: bool,
        permission_boundary_acknowledged: bool,
    ) -> None:
        profile = profile.lower().strip()
        if profile not in VALID_PROFILES:
            raise ValueError("Perfil inválido.")
        if privacy_acknowledged is not True:
            raise ValueError("É necessário confirmar a informação de privacidade.")
        if permission_boundary_acknowledged is not True:
            raise ValueError("É necessário confirmar a política de ações protegidas.")

        settings = self.settings_factory()
        if not settings.set_profile(profile):
            raise ValueError("Não foi possível guardar o perfil selecionado.")

        self.data.update(
            {
                "completed": True,
                "profile": profile,
                "privacy_acknowledged": True,
                "permission_boundary_acknowledged": True,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.save()

    def reset(self) -> None:
        self.data.update(
            {
                "completed": False,
                "privacy_acknowledged": False,
                "permission_boundary_acknowledged": False,
                "completed_at": None,
            }
        )
        self.save()

    def public_state(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "profile": self.profile,
            "model": AuraConfig().model_name,
            "profiles": [
                {
                    "id": "fast",
                    "name": "Fast",
                    "description": "Lower latency and shorter answers.",
                },
                {
                    "id": "balanced",
                    "name": "Balanced",
                    "description": "Recommended default for everyday AURA use.",
                },
                {
                    "id": "deep",
                    "name": "Deep",
                    "description": "Longer reasoning and higher local resource use.",
                },
            ],
        }

    def hardware_check(self) -> dict[str, Any]:
        """Return a bounded compatibility snapshot without reading user content."""
        memory = psutil.virtual_memory()
        ram_total_gb = round(memory.total / 1024**3, 1)
        ram_available_gb = round(memory.available / 1024**3, 1)

        disk_root = Path.home().anchor or os.getcwd()
        disk = shutil.disk_usage(disk_root)
        disk_free_gb = round(disk.free / 1024**3, 1)

        gpu = self._gpu_info()
        warnings: list[str] = []
        blockers: list[str] = []

        if ram_total_gb < MIN_RAM_GB:
            blockers.append(
                f"AURA requires at least {MIN_RAM_GB:g} GB of RAM for this Alpha."
            )
        elif ram_total_gb < RECOMMENDED_RAM_GB:
            warnings.append(
                f"{RECOMMENDED_RAM_GB:g} GB of RAM is recommended for a smoother experience."
            )

        if disk_free_gb < MIN_FREE_DISK_GB:
            blockers.append(
                f"At least {MIN_FREE_DISK_GB:g} GB of free disk space is required before model setup."
            )
        elif disk_free_gb < RECOMMENDED_FREE_DISK_GB:
            warnings.append(
                f"Keep around {RECOMMENDED_FREE_DISK_GB:g} GB free for the model cache and updates."
            )

        if platform.system() != "Windows":
            warnings.append("The Alpha 2 desktop experience is primarily tested on Windows.")

        if gpu["available"] and isinstance(gpu.get("vram_gb"), (int, float)):
            if float(gpu["vram_gb"]) < RECOMMENDED_VRAM_GB:
                warnings.append(
                    f"A GPU with at least {RECOMMENDED_VRAM_GB:g} GB VRAM is recommended for local acceleration."
                )
        elif not gpu["available"]:
            warnings.append(
                "No CUDA GPU was detected. AURA may run on CPU, but local inference can be significantly slower."
            )

        if blockers:
            status = "unsupported"
        elif warnings:
            status = "limited"
        else:
            status = "ready"

        return {
            "status": status,
            "operating_system": platform.system() or "Unknown",
            "os_version": platform.release() or "Unknown",
            "architecture": platform.machine() or "Unknown",
            "cpu_logical": os.cpu_count() or 0,
            "ram_total_gb": ram_total_gb,
            "ram_available_gb": ram_available_gb,
            "disk_free_gb": disk_free_gb,
            "gpu": gpu,
            "warnings": warnings,
            "blockers": blockers,
            "can_continue": not blockers,
        }

    @staticmethod
    def _gpu_info() -> dict[str, Any]:
        """Detect CUDA acceleration without loading AURA's language model."""
        try:
            import torch
        except Exception:
            return {
                "available": False,
                "name": None,
                "vram_gb": None,
                "backend": None,
            }

        try:
            if not torch.cuda.is_available():
                return {
                    "available": False,
                    "name": None,
                    "vram_gb": None,
                    "backend": "cpu",
                }
            device = torch.cuda.current_device()
            properties = torch.cuda.get_device_properties(device)
            return {
                "available": True,
                "name": torch.cuda.get_device_name(device),
                "vram_gb": round(properties.total_memory / 1024**3, 1),
                "backend": "cuda",
            }
        except Exception:
            return {
                "available": False,
                "name": None,
                "vram_gb": None,
                "backend": None,
            }
