import re
from urllib.parse import urlparse

import emoji

PATTERN_BRACKET_LINK = r"\[([^\]|]+)\|([^\]]+)\]"
PATTERN_PROTOCOL_URL = r"https?://[^\s\]]+"


def normalize_links(text: str) -> str:
    def insert_zwsp_after_emoji_sequences(s: str) -> str:
        emjs = emoji.emoji_list(s)
        if not emjs:
            return s
        result = []
        last_idx = 0
        for e in emjs:
            start, end = e["match_start"], e["match_end"]
            result.append(s[last_idx:start])
            result.append(s[start:end] + "\u200b")
            last_idx = end
        result.append(s[last_idx:])
        return "".join(result)

    text = insert_zwsp_after_emoji_sequences(text)

    def replace_bracket_link(match):
        link = match.group(1).strip()
        label = match.group(2).strip()

        if re.fullmatch(r"(club\d+|id\d+)", link):
            return f"[{label}](vk.com/{link})"

        if link.startswith("vk.com/") and re.match(r"https?://", label):
            parsed = urlparse(label)
            return parsed.netloc + (parsed.path if parsed.path != "/" else "")

        if re.match(r"https?://", label):
            parsed = urlparse(label)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                return parsed.netloc + (parsed.path if parsed.path != "/" else "")

        if re.match(r"https?://", link):
            parsed = urlparse(link)
            if parsed.scheme in ("http", "https") and parsed.netloc:
                clean_link = parsed.netloc + (parsed.path if parsed.path != "/" else "")
                return f"[{label}]({clean_link})"
            else:
                return label

        if re.match(r"^[\w.-]+\.[a-z]{2,}", link):
            return f"[{label}]({link})"

        return label

    text = re.sub(PATTERN_BRACKET_LINK, replace_bracket_link, text)

    def strip_protocol(match):
        url = match.group(0)
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            return parsed.netloc + (parsed.path if parsed.path != "/" else "")
        return url

    text = re.sub(PATTERN_PROTOCOL_URL, strip_protocol, text)

    return text
