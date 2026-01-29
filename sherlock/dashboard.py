"""Rich terminal dashboard for displaying LLM traffic."""

from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from sherlock.config import MAX_LOG_ENTRIES, PROMPT_PREVIEW_LENGTH


class SherlockDashboard:
    """Terminal dashboard for displaying intercepted LLM traffic."""

    def __init__(self, token_limit: int = 200_000):
        self.console = Console()
        self.token_limit = token_limit
        self.total_tokens = 0
        self.requests: list[dict] = []
        self.last_prompt = ""
        self.last_provider = ""

    def add_request(self, data: dict) -> None:
        """Add a new intercepted request to the dashboard."""
        tokens = data.get("tokens", 0)
        self.total_tokens += tokens

        # Store request info
        request_info = {
            "time": datetime.fromisoformat(data["timestamp"]).strftime("%H:%M:%S"),
            "provider": data.get("provider", "unknown").capitalize(),
            "model": data.get("model", "unknown"),
            "tokens": tokens,
        }
        self.requests.append(request_info)

        # Keep only the last N entries
        if len(self.requests) > MAX_LOG_ENTRIES:
            self.requests = self.requests[-MAX_LOG_ENTRIES:]

        # Update last prompt
        messages = data.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                self.last_prompt = msg.get("content", "")
                break
        self.last_provider = data.get("provider", "unknown").capitalize()

    def load_history(self, history: list[dict]) -> None:
        """Load historical data to restore session state."""
        for event in history:
            self.add_request(event)

    def _make_header(self) -> Panel:
        """Create the header panel."""
        title = Text()
        title.append("SHERLOCK", style="bold cyan")
        title.append(" - LLM Traffic Inspector", style="dim")
        return Panel(title, style="cyan", height=3)

    def _make_fuel_gauge(self) -> Panel:
        """Create the token fuel gauge panel."""
        percentage = min(100, (self.total_tokens / self.token_limit) * 100)

        # Determine color based on usage
        if percentage < 50:
            bar_style = "green"
        elif percentage < 80:
            bar_style = "yellow"
        else:
            bar_style = "red"

        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(bar_width=50, complete_style=bar_style, finished_style=bar_style),
            TextColumn("{task.percentage:>3.0f}%"),
            TextColumn("({task.completed:,} / {task.total:,} tokens)"),
            expand=True,
        )
        progress.add_task("Context Usage", total=self.token_limit, completed=self.total_tokens)

        return Panel(
            progress,
            title="Context Fuel Gauge",
            border_style="blue",
            height=5,
        )

    def _make_request_table(self) -> Panel:
        """Create the request log table panel."""
        table = Table(expand=True, show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim", width=10)
        table.add_column("Provider", width=12)
        table.add_column("Model", width=30)
        table.add_column("Tokens", justify="right", width=10)

        # Show most recent requests
        display_requests = self.requests[-20:]
        for req in display_requests:
            tokens_str = f"{req['tokens']:,}"
            table.add_row(
                req["time"],
                req["provider"],
                req["model"],
                tokens_str,
            )

        return Panel(
            table,
            title="Request Log",
            border_style="green",
        )

    def _make_prompt_panel(self) -> Panel:
        """Create the last prompt preview panel."""
        if self.last_prompt:
            preview = self.last_prompt[:PROMPT_PREVIEW_LENGTH]
            if len(self.last_prompt) > PROMPT_PREVIEW_LENGTH:
                preview += "..."
            content = Text(preview)
        else:
            content = Text("No prompts intercepted yet...", style="dim italic")

        title = "Last Prompt"
        if self.last_provider:
            title += f" ({self.last_provider})"

        return Panel(
            content,
            title=title,
            border_style="yellow",
            height=8,
        )

    def render(self) -> Layout:
        """Generate the full dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="gauge", size=5),
            Layout(name="table"),
            Layout(name="prompt", size=8),
        )

        layout["header"].update(self._make_header())
        layout["gauge"].update(self._make_fuel_gauge())
        layout["table"].update(self._make_request_table())
        layout["prompt"].update(self._make_prompt_panel())

        return layout

    def run(self, poll_callback) -> None:
        """Run the dashboard with live updates.

        Args:
            poll_callback: Function to call that returns new events (list of dicts)
        """
        with Live(self.render(), console=self.console, refresh_per_second=4, screen=True) as live:
            try:
                while True:
                    # Poll for new events
                    new_events = poll_callback()
                    for event in new_events:
                        self.add_request(event)

                    # Update display
                    live.update(self.render())

            except KeyboardInterrupt:
                pass
