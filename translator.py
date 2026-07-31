import time
import ollama
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from xhtml2pdf import pisa

from config import MODEL_NAME, OUTPUT_PDF, SYSTEM_PROMPT, console
from text_utils import convert_to_pinyin, split_sentences


def export_to_pdf(sentences: list[str], output_path: str):
    """Generates a clean PDF containing Chinese text and Pinyin using HTML/CSS rendering."""

    # Build HTML content with CSS for clean typography and CJK font fallback
    items_html = ""
    for idx, chunk in enumerate(sentences, start=1):
        py_sentence = convert_to_pinyin(chunk)
        items_html += f"""
        <div class="sentence-block">
            <div class="chinese"><span class="num">{idx}.</span> {chunk}</div>
            <div class="pinyin">{py_sentence}</div>
        </div>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: letter;
                margin: 0.6in;
            }}
            body {{
                font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "SimSun", sans-serif;
                color: #111111;
                font-size: 11pt;
                line-height: 1.5;
            }}
            .sentence-block {{
                margin-bottom: 14pt;
            }}
            .chinese {{
                font-size: 11pt;
                font-weight: normal;
                color: #111111;
                margin-bottom: 2pt;
                line-height: 1.6;
            }}
            .num {{
                font-weight: bold;
            }}
            .pinyin {{
                font-size: 9.5pt;
                color: #555555;
                font-style: italic;
                line-height: 1.4;
                font-family: "Helvetica", sans-serif;
            }}
        </style>
    </head>
    <body>
        {items_html}
    </body>
    </html>
    """

    with open(output_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)

    if pisa_status.err:
        console.print("[red]Error generating PDF document.[/red]")


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

    sentences = split_sentences(full_text)

    for idx, chunk in enumerate(sentences, start=1):
        py_sentence = convert_to_pinyin(chunk)
        print(f"**{idx}**")
        print(chunk)
        print(py_sentence)
        print()

    # Export cleanly formatted PDF
    export_to_pdf(sentences, OUTPUT_PDF)
    console.print(f"[bold green]✓ Exported PDF to:[/bold green] {OUTPUT_PDF}")
