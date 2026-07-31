import re
from pypinyin import Style, pinyin

# Pairs to treat as unbreakable blocks when splitting sentences
PAIR_MAP = {
    "(": ")",
    "（": "）",
    "[": "]",
    "【": "】",
    "{": "}",
    "“": "”",
    "«": "»",
    "“": "”",
}


def split_sentences(text: str) -> list[str]:
    """Splits Chinese text by sentence delimiters (。, ！, ？, \n) while respecting

    nested brackets, quotes, and parentheses.
    """
    # Find punctuation delimiters only when stack depth is 0
    delimiters = set("。！？\n")
    open_pairs = set(PAIR_MAP.keys())
    close_pairs = {v: k for k, v in PAIR_MAP.items()}

    stack = []
    sentences = []
    current_chunk = []

    for char in text:
        current_chunk.append(char)

        if char in open_pairs:
            stack.append(char)
        elif char in close_pairs:
            if stack and stack[-1] == close_pairs[char]:
                stack.pop()

        # If we hit a sentence delimiter and we aren't inside parentheses/quotes
        elif char in delimiters and not stack:
            sentence = "".join(current_chunk).strip()
            if sentence:
                sentences.append(sentence)
            current_chunk = []

    # Handle any remaining trailing text
    if current_chunk:
        sentence = "".join(current_chunk).strip()
        if sentence:
            sentences.append(sentence)

    return sentences


def convert_to_pinyin(text: str) -> str:
    """Converts a Chinese string to Pinyin with tone marks."""
    py_list = pinyin(text, style=Style.TONE)
    return " ".join([item[0] for item in py_list])
