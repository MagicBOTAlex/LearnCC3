import os
import re
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import ollama
from prompt_toolkit import prompt
from pypinyin import Style, pinyin
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

# Retrieve SYSTEM PROMPT from environment, with typo fallback, or use default
DEFAULT_SYSTEM_PROMPT = "Translate to Simplified Chinese (Mandarin). Use common Chinese words so it is easy to read."
SYSTEM_PROMPT = os.getenv(
    "TRANSLATION_PROMPT", os.getenv("TRANSLATION_PROMT", DEFAULT_SYSTEM_PROMPT)
)

console = Console()


def split_sentences(text: str) -> list[str]:
    """Splits Chinese text by sentence delimiters (。, ！, ？, \n) while keeping the original text clean."""
    # Split by common Chinese end-of-sentence delimiters and newlines
    raw_chunks = re.split(r"([。！？\n])", text)
    sentences = []

    # Recombine delimiter with the preceding text
    for i in range(0, len(raw_chunks) - 1, 2):
        chunk = raw_chunks[i] + raw_chunks[i + 1]
        chunk = chunk.strip()
        if chunk:
            sentences.append(chunk)

    # Add any remaining tail text without a delimiter
    if len(raw_chunks) % 2 != 0:
        tail = raw_chunks[-1].strip()
        if tail:
            sentences.append(tail)

    return sentences


def convert_to_pinyin(text: str) -> str:
    """Converts a Chinese string to Pinyin with tone marks."""
    py_list = pinyin(text, style=Style.TONE)
    return " ".join([item[0] for item in py_list])


def prompt_gemma_stream(prompt_text: str):
    start_time = time.perf_counter()

    stream = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text},
        ],
        stream=True,
        think="low",
        options={
            "temperature": 0,
            "num_ctx": 51200,
        },
    )

    full_thinking = ""
    full_text = ""
    output_token_count = 0
    input_token_count = 0

    # Rich Live context handles redrawing, wrapping, and clean terminal updating automatically
    with Live(console=console, refresh_per_second=12) as live:
        for chunk in stream:
            if getattr(chunk, "prompt_eval_count", None):
                input_token_count = chunk.prompt_eval_count

            thinking_delta = getattr(chunk.message, "thinking", None) or ""
            text_delta = chunk.message.content or ""

            full_thinking += thinking_delta
            full_text += text_delta

            if getattr(chunk, "eval_count", None):
                output_token_count = chunk.eval_count
            else:
                output_token_count += 1

            elapsed_time = time.perf_counter() - start_time

            if full_text:
                active_raw_lines = full_text.splitlines()
                is_thinking = False
            else:
                active_raw_lines = full_thinking.splitlines()
                is_thinking = True

            displayed_lines = (
                active_raw_lines[-3:] if len(active_raw_lines) > 3 else active_raw_lines
            )
            content_str = "\n".join(displayed_lines)

            text_style = "dim cyan" if is_thinking else "default"
            render_text = Text(content_str, style=text_style)

            status_state = "Thinking..." if is_thinking else "Generating..."
            title = f"[bold spinner] {status_state} | Model: {MODEL_NAME} | Output Tokens: {output_token_count} | Time: {elapsed_time:.2f}s"

            live.update(
                Panel(
                    render_text,
                    title=title,
                    border_style="dim white" if is_thinking else "green",
                    expand=True,
                )
            )

    total_time = time.perf_counter() - start_time
    tokens_per_sec = output_token_count / total_time if total_time > 0 else 0

    console.print(
        f"[bold blue]ℹ Input tokens:[/bold blue] {input_token_count} | "
        f"[bold green]✓ Output tokens:[/bold green] {output_token_count} "
        f"([bold cyan]{total_time:.2f}s[/bold cyan] @ [bold yellow]{tokens_per_sec:.1f} tok/s[/bold yellow])\n"
    )

    # Output formatted chunks and Pinyin
    sentences = split_sentences(full_text)

    for idx, chunk in enumerate(sentences, start=1):
        py_sentence = convert_to_pinyin(chunk)
        print(f"**{idx}**")
        print(chunk)
        print(py_sentence)
        print()


if __name__ == "__main__":
    console.print(
        "[bold yellow]Enter or paste text to translate (Press Alt+Enter or Esc then Enter to submit):[/bold yellow]"
    )

    try:
        user_input = prompt("> ", multiline=True).strip()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)

    if not user_input:
        console.print("[red]No input provided. Exiting...[/red]")
        sys.exit(0)

    console.print(
        f"\nSending prompt to local Ollama instance ({MODEL_NAME})...\n",
        style="bold blue",
    )
    prompt_gemma_stream(user_input)
