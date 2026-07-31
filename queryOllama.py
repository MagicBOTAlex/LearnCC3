import ollama


def prompt_gemma(prompt_text: str) -> str:
    response = ollama.chat(
        model="gemma4:26b",
        messages=[
            {
                "role": "user",
                "content": prompt_text,
            }
        ],
        stream=False,  # Disable streaming
        think="low",  # Set reasoning effort / thinking level to "low"
        options={
            "temperature": 0,  # Set temperature to 0 for deterministic outputs
            "num_ctx": 51200,  # Set context window size to 51,200 tokens
        },
    )

    # Access response content
    return response.message.content


if __name__ == "__main__":
    prompt = "Explain quantum computing in three clear bullet points."

    print("Sending prompt to local Ollama instance...")
    result = prompt_gemma(prompt)

    print("\nResponse:")
    print(result)
