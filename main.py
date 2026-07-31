import sys
from prompt_toolkit import prompt

from config import MODEL_NAME, console
from translator import ollama_stream


def main():
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
    ollama_stream(user_input)


if __name__ == "__main__":
    main()
