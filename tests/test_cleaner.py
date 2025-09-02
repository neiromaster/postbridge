import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from cleaner import normalize_links

# Atomic test cases to isolate functionality
TEST_CASES = [
    # 1. Test just an emoji
    ("emoji_only", "Hello 👍 World", "Hello 👍\u200b World"),
    # 2. Test just a junk link
    ("junk_link", "Link: [vk.com/junk|http://real.com/page]", "Link: real.com/page"),
    # 3. Test just a club link
    ("club_link", "Group: [club123|My Club]", "Group: [My Club](vk.com/club123)"),
    # 4. Test just an ID link
    ("id_link", "User: [id456|My Name]", "User: [My Name](vk.com/id456)"),
    # 5. Test a valid URL link
    ("url_link", "Site: [https://example.com|My Site]", "Site: [My Site](example.com)"),
    # 6. Test a broken URL link
    ("broken_url_link", "Broken: [httpd://broken|Do not show link]", "Broken: Do not show link"),
    # 7. Test stripping protocol from a raw link
    ("protocol_strip", "Raw link: https://raw.link/path", "Raw link: raw.link/path"),
    # 8. Test emoji and a simple link
    ("emoji_and_link", "Pointer 👉[club123|My Club]", "Pointer 👉\u200b[My Club](vk.com/club123)"),
    # 9. Flag as a single emoji
    ("flag_emoji", "Country: 🇷🇺Russia", "Country: 🇷🇺\u200bRussia"),
    # 10. Family Emoji Combination
    ("family_emoji", "Family: 👩‍👩‍👧‍👦Happy", "Family: 👩‍👩‍👧‍👦\u200bHappy"),
    # 11. Real broken link
    (
        "real_broken_link",
        "👉[vk.comhttps://vk.com/@donut-android|http://vk.com/donut/dublikkk]",
        "👉\u200bvk.com/donut/dublikkk",
    ),
]


@pytest.mark.parametrize("test_id, input_text, expected_text", TEST_CASES)
def test_atomic_cases(test_id, input_text, expected_text):
    result = normalize_links(input_text)
    assert result == expected_text
