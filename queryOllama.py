import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import ollama
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Load environment variables (.env first, then .env.example if .env is missing)
env_path = Path(".env")
env_example_path = Path(".env.example")

if env_path.is_file():
    load_dotenv(dotenv_path=env_path)
elif env_example_path.is_file():
    load_dotenv(dotenv_path=env_example_path)

# Retrieve MODEL from environment with default fallback
MODEL_NAME = os.getenv("MODEL", "gemma4:12b")

console = Console()


def prompt_gemma_stream(prompt_text: str):
    start_time = time.perf_counter()

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt_text}],
        stream=True,
        think="low",
        options={
            "temperature": 0,
            "num_ctx": 51200,
        },
    )

    full_thinking = ""
    full_text = ""
    token_count = 0

    # Rich Live context handles redrawing, wrapping, and clean terminal updating automatically
    with Live(console=console, refresh_per_second=12) as live:
        for chunk in stream:
            # Check if chunk contains thinking or standard output content
            thinking_delta = getattr(chunk.message, "thinking", None) or ""
            text_delta = chunk.message.content or ""

            full_thinking += thinking_delta
            full_text += text_delta

            if getattr(chunk, "eval_count", None):
                token_count = chunk.eval_count
            else:
                token_count += 1

            # Calculate time spent so far
            elapsed_time = time.perf_counter() - start_time

            # Decide whether we are displaying thinking or final response
            if full_text:
                active_raw_lines = full_text.splitlines()
                is_thinking = False
            else:
                active_raw_lines = full_thinking.splitlines()
                is_thinking = True

            # Keep maximum 3 lines of output text
            displayed_lines = (
                active_raw_lines[-3:] if len(active_raw_lines) > 3 else active_raw_lines
            )
            content_str = "\n".join(displayed_lines)

            # Style the text (dim grey when thinking)
            text_style = "dim cyan" if is_thinking else "default"
            render_text = Text(content_str, style=text_style)

            # Build status header with animated spinner, model name, tokens, and time spent
            status_state = "Thinking..." if is_thinking else "Generating..."
            title = f"[bold spinner] {status_state} | Model: {MODEL_NAME} | Tokens: {token_count} | Time: {elapsed_time:.2f}s"

            # Update the panel dynamically
            live.update(
                Panel(
                    render_text,
                    title=title,
                    border_style="dim white" if is_thinking else "green",
                    expand=True,
                )
            )

    total_time = time.perf_counter() - start_time
    tokens_per_sec = token_count / total_time if total_time > 0 else 0

    console.print(
        f"[bold green]✓ Total tokens generated:[/bold green] {token_count} "
        f"([bold cyan]{total_time:.2f}s[/bold cyan] @ [bold yellow]{tokens_per_sec:.1f} tok/s[/bold yellow])"
    )


if __name__ == "__main__":
    prompt = "Explain quantum computing in three clear bullet points."

    console.print(
        f"Sending prompt to local Ollama instance ({MODEL_NAME})...\n",
        style="bold blue",
    )
    prompt_gemma_stream(prompt)
