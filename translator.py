import time
import ollama
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from config import MODEL_NAME, SYSTEM_PROMPT, console
from text_utils import convert_to_pinyin, split_sentences


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
