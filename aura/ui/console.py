from __future__ import annotations

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text


class AuraConsole:
    """Terminal UI for AURA-1."""

    def __init__(self):
        self.console = Console()

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    def header(self) -> None:
        self.console.clear()

        logo = Text()
        logo.append(
            "AURA-1",
            style="bold bright_cyan",
        )

        subtitle = Text(
            "\nUntoz AI Assistant",
            style="white",
        )

        version = Text(
            "\nALPHA 2",
            style="bold magenta",
        )

        content = Text.assemble(
            logo,
            subtitle,
            version,
        )

        self.console.print(
            Panel(
                Align.center(content),
                border_style="bright_cyan",
                padding=(1, 6),
                title="[bold]AURA[/bold]",
                subtitle="[dim]Local Intelligence[/dim]",
            )
        )

        self.console.print(
            "[green]●[/green] "
            "[bold]SYSTEM ONLINE[/bold]  "
            "[dim]Windows Agent Runtime[/dim]\n"
        )

    # --------------------------------------------------
    # INPUT
    # --------------------------------------------------

    def ask(self) -> str:
        return Prompt.ask(
            "[bold bright_blue]TU[/bold bright_blue]"
        ).strip()

    # --------------------------------------------------
    # AURA MESSAGE
    # --------------------------------------------------

    def aura(
        self,
        message: str,
    ) -> None:
        self.console.print()

        self.console.print(
            Panel(
                message,
                title=(
                    "[bold bright_cyan]"
                    "AURA"
                    "[/bold bright_cyan]"
                ),
                border_style="cyan",
                padding=(0, 1),
            )
        )

    # --------------------------------------------------
    # INFORMATION
    # --------------------------------------------------

    def info(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[bright_blue]ℹ[/bright_blue] "
            f"{message}"
        )

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    def success(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[green]✓[/green] {message}"
        )

    # --------------------------------------------------
    # WARNING
    # --------------------------------------------------

    def warning(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[yellow]⚠[/yellow] {message}"
        )

    # --------------------------------------------------
    # ERROR
    # --------------------------------------------------

    def error(
        self,
        message: str,
    ) -> None:
        self.console.print(
            f"[bold red]✕[/bold red] "
            f"{message}"
        )

    # --------------------------------------------------
    # BLOCKED
    # --------------------------------------------------

    def blocked(
        self,
        message: str,
    ) -> None:
        self.console.print(
            Panel(
                message,
                title="[bold red]BLOCKED[/bold red]",
                border_style="red",
            )
        )

    # --------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------

    def confirm(
        self,
        message: str,
    ) -> bool:

        self.console.print()

        self.console.print(
            Panel(
                message,
                title=(
                    "[bold yellow]"
                    "CONFIRMATION REQUIRED"
                    "[/bold yellow]"
                ),
                border_style="yellow",
            )
        )

        answer = Prompt.ask(
            "[yellow]Confirmar?[/yellow]",
            choices=[
                "s",
                "n",
            ],
            default="n",
        )

        return answer.lower() == "s"

    # --------------------------------------------------
    # LOADING
    # --------------------------------------------------

    def loading(
        self,
        message: str,
    ):
        return self.console.status(
            f"[cyan]{message}[/cyan]",
            spinner="dots",
        )

    # --------------------------------------------------
    # PLAN
    # --------------------------------------------------

    def plan(
        self,
        description: str,
        actions,
    ) -> None:

        table = Table(
            show_header=True,
            header_style="bold bright_cyan",
            border_style="cyan",
            expand=False,
        )

        table.add_column(
            "#",
            justify="right",
            style="dim",
            width=3,
        )

        table.add_column(
            "AÇÃO",
        )

        table.add_column(
            "TOOL",
            style="dim",
        )

        for index, action in enumerate(
            actions,
            start=1,
        ):
            description_text = (
                action.description
                or action.action
            )

            tool_text = (
                f"{action.tool}."
                f"{action.action}"
            )

            table.add_row(
                str(index),
                description_text,
                tool_text,
            )

        self.console.print()

        self.console.print(
            Panel(
                table,
                title=(
                    "[bold bright_cyan]"
                    "AURA PLAN"
                    "[/bold bright_cyan]"
                ),
                subtitle=description,
                border_style="bright_cyan",
            )
        )

    # --------------------------------------------------
    # PLAN RESULT
    # --------------------------------------------------

    def plan_complete(
        self,
        completed: int,
        total: int,
    ) -> None:

        self.console.print()

        self.console.print(
            Panel(
                (
                    f"[bold green]✓ PLAN COMPLETED[/bold green]\n\n"
                    f"{completed}/{total} ações executadas."
                ),
                border_style="green",
            )
        )

    # --------------------------------------------------
    # PROCESS TABLE
    # --------------------------------------------------

    def processes(
        self,
        processes: list[dict],
    ) -> None:

        table = Table(
            title="Processos",
            header_style="bold cyan",
            border_style="cyan",
        )

        table.add_column(
            "PID",
            justify="right",
        )

        table.add_column(
            "Processo",
        )

        table.add_column(
            "Memória",
            justify="right",
        )

        for process in processes:
            table.add_row(
                str(
                    process.get(
                        "pid",
                        "?",
                    )
                ),
                str(
                    process.get(
                        "nome",
                        "Desconhecido",
                    )
                ),
                (
                    f"{process.get('memoria_mb', '?')} MB"
                ),
            )

        self.console.print(table)

    # --------------------------------------------------
    # SEPARATOR
    # --------------------------------------------------

    def separator(self) -> None:
        self.console.rule(
            style="dim cyan"
        )