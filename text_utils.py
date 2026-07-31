import re
from pypinyin import Style, pinyin


def split_sentences(text: str) -> list[str]:
    """Splits Chinese text by sentence delimiters (。, ！, ？, \n) while keeping the original text clean."""
    raw_chunks = re.split(r"([。！？\n])", text)
    sentences = []

    for i in range(0, len(raw_chunks) - 1, 2):
        chunk = raw_chunks[i] + raw_chunks[i + 1]
        chunk = chunk.strip()
        if chunk:
            sentences.append(chunk)

    if len(raw_chunks) % 2 != 0:
        tail = raw_chunks[-1].strip()
        if tail:
            sentences.append(tail)

    return sentences


def convert_to_pinyin(text: str) -> str:
    """Converts a Chinese string to Pinyin with tone marks."""
    py_list = pinyin(text, style=Style.TONE)
    return " ".join([item[0] for item in py_list])
