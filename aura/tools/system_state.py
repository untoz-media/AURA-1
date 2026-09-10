from __future__ import annotations

import os
from typing import Any

import psutil


class SystemStateResult(dict):
    """Structured telemetry that also renders cleanly in the CLI."""

    def __init__(self, payload: dict[str, Any], message: str) -> None:
        super().__init__(payload)
        self.message = message

    def __str__(self) -> str:
        return self.message


class SystemStateTool:
    """Collect bounded, read-only runtime telemetry about the local computer.

    This tool intentionally avoids window titles, command lines, environment
    variables, usernames, clipboard contents and file contents. The goal is to
    understand system pressure without collecting unrelated personal data.
    """

    name = "system_state"
    description = "Observa CPU, RAM, bateria e estado geral do computador."

    TOP_PROCESS_LIMIT = 5
    CPU_HIGH_PERCENT = 85.0
    RAM_HIGH_PERCENT = 85.0

    def snapshot(self) -> dict:
        try:
            cpu_percent = round(float(psutil.cpu_percent(interval=0.1)), 1)
            memory = psutil.virtual_memory()
            ram = {
                "total_gb": self._bytes_to_gb(memory.total),
                "usado_gb": self._bytes_to_gb(memory.used),
                "disponivel_gb": self._bytes_to_gb(memory.available),
                "percentagem_usada": round(float(memory.percent), 1),
            }

            battery = self._battery_state()
            foreground = self._foreground_process_name()
            top_processes = self._top_memory_processes()

            pressure = self._pressure_level(
                cpu_percent,
                ram["percentagem_usada"],
            )

            payload = {
                "sucesso": True,
                "acao": "system_state_snapshot",
                "cpu_percent": cpu_percent,
                "ram": ram,
                "pressao": pressure,
                "bateria": battery,
                "foreground_app": foreground,
                "processos_memoria": top_processes,
            }

            message = self._format_message(payload)
            return SystemStateResult(payload, message)
        except Exception as exc:
            return {
                "sucesso": False,
                "erro": f"Não foi possível observar o estado do sistema: {exc}",
            }

    @classmethod
    def _pressure_level(cls, cpu_percent: float, ram_percent: float) -> str:
        if (
            cpu_percent >= cls.CPU_HIGH_PERCENT
            or ram_percent >= cls.RAM_HIGH_PERCENT
        ):
            return "high"
        if cpu_percent >= 65.0 or ram_percent >= 70.0:
            return "moderate"
        return "normal"

    @staticmethod
    def _bytes_to_gb(value: int | float) -> float:
        return round(float(value) / (1024 ** 3), 1)

    def _battery_state(self) -> dict[str, Any] | None:
        try:
            battery = psutil.sensors_battery()
        except (AttributeError, NotImplementedError, OSError):
            return None

        if battery is None:
            return None

        seconds_left = getattr(battery, "secsleft", None)
        if seconds_left in {
            getattr(psutil, "POWER_TIME_UNKNOWN", -1),
            getattr(psutil, "POWER_TIME_UNLIMITED", -2),
        }:
            seconds_left = None

        return {
            "percentagem": round(float(battery.percent), 1),
            "ligado_corrente": bool(battery.power_plugged),
            "segundos_restantes": (
                int(seconds_left)
                if isinstance(seconds_left, (int, float)) and seconds_left >= 0
                else None
            ),
        }

    def _top_memory_processes(self) -> list[dict[str, Any]]:
        processes: list[dict[str, Any]] = []

        try:
            iterator = psutil.process_iter(["pid", "name", "memory_info"])
        except Exception:
            return []

        for process in iterator:
            try:
                info = process.info
                memory_info = info.get("memory_info")
                memory_mb = (
                    float(memory_info.rss) / (1024 ** 2)
                    if memory_info is not None
                    else 0.0
                )
                processes.append(
                    {
                        "pid": info.get("pid"),
                        "nome": info.get("name") or "Desconhecido",
                        "memoria_mb": round(memory_mb, 1),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue

        processes.sort(
            key=lambda item: item["memoria_mb"],
            reverse=True,
        )
        return processes[: self.TOP_PROCESS_LIMIT]

    @staticmethod
    def _foreground_process_name() -> str | None:
        if os.name != "nt":
            return None

        try:
            import ctypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if not pid.value:
                return None

            return psutil.Process(pid.value).name()
        except Exception:
            return None

    @staticmethod
    def _format_message(payload: dict[str, Any]) -> str:
        ram = payload.get("ram", {})
        parts = [
            f"CPU: {payload.get('cpu_percent', '?')}%",
            (
                f"RAM: {ram.get('percentagem_usada', '?')}% usada "
                f"({ram.get('disponivel_gb', '?')} GB disponíveis)"
            ),
            f"pressão do sistema: {payload.get('pressao', 'desconhecida')}",
        ]

        foreground = payload.get("foreground_app")
        if foreground:
            parts.append(f"app em primeiro plano: {foreground}")

        battery = payload.get("bateria")
        if battery:
            power = "ligado à corrente" if battery.get("ligado_corrente") else "em bateria"
            parts.append(
                f"bateria: {battery.get('percentagem', '?')}% ({power})"
            )

        top_processes = payload.get("processos_memoria") or []
        if top_processes:
            top = ", ".join(
                f"{item.get('nome', 'processo')} {item.get('memoria_mb', '?')} MB"
                for item in top_processes[:3]
            )
            parts.append(f"maior uso de memória: {top}")

        return "Estado do PC — " + "; ".join(parts) + "."
