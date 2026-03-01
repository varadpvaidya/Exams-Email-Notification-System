import os
import re
import requests
import unicodedata
from dotenv import load_dotenv
from elements import ELEMENTS



# =====================================================
# CONFIG
# =====================================================
emoji_url = "https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{ecode}.png"


# =====================================================
# LOAD ENV
# =====================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL")

if not SECRET_KEY or not WEBAPP_URL:
    raise ValueError("SECRET_KEY or WEBAPP_URL missing in .env")


# =====================================================
# EMOJI CONVERSION
# =====================================================
def emoji_to_twemoji(text: str, size_px: int) -> str:
    """
    Converts emojis into perfectly inline Twemoji images
    (email-client safe, no line break).
    """

    def replace(match):
        char = match.group(0)
        codepoints = [f"{ord(c):x}" for c in char]
        ecode = "-".join(codepoints)
        url = emoji_url.format(ecode=ecode)

        return (
            f'<img src="{url}" '
            f'width="{size_px}" '
            f'height="{size_px}" '
            f'style="display:inline;vertical-align:middle;'
            f'margin:0 2px;border:0;line-height:1;font-size:inherit;" '
            f'alt="{char}">'
        )

    emoji_pattern = re.compile(
        "["
        "\U0001F1E6-\U0001F1FF"
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )

    return emoji_pattern.sub(replace, text)

def strip_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001F1E6-\U0001F1FF"
        "\U0001F300-\U0001F5FF"
        "\U0001F600-\U0001F64F"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)


# =====================================================
# SAFE DIV REMOVAL
# =====================================================
def remove_section(html: str, class_name: str) -> str:
    pattern = rf'<div\s+class="{class_name}">'
    match = re.search(pattern, html)

    if not match:
        return html

    start_index = match.start()
    index = match.end()
    open_divs = 1

    while open_divs > 0 and index < len(html):
        next_open = html.find("<div", index)
        next_close = html.find("</div>", index)

        if next_close == -1:
            break

        if next_open != -1 and next_open < next_close:
            open_divs += 1
            index = next_open + 4
        else:
            open_divs -= 1
            index = next_close + 6

    return html[:start_index] + html[index:]


# =====================================================
# BUILD EMAIL
# =====================================================
def build_email(ai_data: dict) -> str:

    with open("emailtemplate.html", "r", encoding="utf-8") as f:
        final_html = f.read()

    # ---- Emoji allowed sections ----
    welcome = emoji_to_twemoji(ai_data.get("welcome_text", ""), 18)
    summary = emoji_to_twemoji(ai_data.get("quick_summary", ""), 16)
    exit_line = emoji_to_twemoji(ai_data.get("exit_message", ""), 18)

    final_html = final_html.replace("{{{!WELCOME TEXT HERE}}}", welcome)
    final_html = final_html.replace("{{{!QUICK SUMMARY HERE}}}", summary)
    final_html = final_html.replace("{{{!EXIT LINE HERE}}}", exit_line)

    # ---- Execution Tasks (strip emojis) ----
    execution_tasks = ai_data.get("execution_tasks", [])

    if execution_tasks:
        block = ""
        for task in execution_tasks:
            task = strip_emojis(task)
            element = ELEMENTS["EXECUTION TASK ELEMENT"]
            element = element.replace("{{{!EXECUTION TASK}}}", task)
            block += element

        final_html = final_html.replace("{{{!EXECUTION TASKS HERE}}}", block)
    else:
        final_html = remove_section(final_html, "EXECUTION_SECTION")

    # ---- Upcoming Exams (strip emojis) ----
    upcoming_exams = ai_data.get("upcoming_exams", [])

    if upcoming_exams:
        block = ""
        for exam in upcoming_exams:
            element = ELEMENTS["UPCOMING EXAM ELEMENT"]
            element = element.replace(
                "{{{!UPCOMING EXAM NAME}}}",
                strip_emojis(exam.get("exam_name", ""))
            )
            element = element.replace(
                "{{{!UPCOMING EXAM DATE}}}",
                strip_emojis(exam.get("exam_date", ""))
            )
            element = element.replace(
                "{{{!UPCOMING EXAM DESCRIPTION}}}",
                strip_emojis(exam.get("description", ""))
            )
            block += element

        final_html = final_html.replace("{{{!UPCOMING EXAMS HERE}}}", block)
    else:
        final_html = remove_section(final_html, "UPCOMING_SECTION")

    # ---- Application Updates ----
    app_updates = ai_data.get("application_updates", [])

    if app_updates:
        deadline_block = ""
        opening_block = ""

        for app in app_updates:
            if app.get("type") == "Deadline":
                element = ELEMENTS["APPLICATION DEADLINE ELEMENT"]
                element = element.replace(
                    "{{{!DEADLINE APPLICATION EXAM NAME}}}",
                    strip_emojis(app.get("exam_name", ""))
                )
                element = element.replace(
                    "{{{!DEADLINE APPLICATION EXAM DATE}}}",
                    strip_emojis(app.get("date", ""))
                )
                deadline_block += element

            elif app.get("type") == "Opening":
                element = ELEMENTS["APPLICATION OPENING ELEMENT"]
                element = element.replace(
                    "{{{!UPCOMING APPLICATION EXAM NAME}}}",
                    strip_emojis(app.get("exam_name", ""))
                )
                element = element.replace(
                    "{{{!UPCOMING APPLICATION EXAM DATE}}}",
                    strip_emojis(app.get("date", ""))
                )
                opening_block += element

        final_html = final_html.replace("{{{!DEADLINE APPLICATION UPDATES HERE}}}", deadline_block)
        final_html = final_html.replace("{{{!UPCOMING APPLICATION UPDATES HERE}}}", opening_block)
    else:
        final_html = remove_section(final_html, "APPLICATION_SECTION")

    return final_html


# =====================================================
# SEND EMAIL
# =====================================================
def send_email(html: str):

    payload = {
        "query": "sendmail",
        "key": SECRET_KEY,
        "html": html
    }

    response = requests.post(WEBAPP_URL, data=payload, timeout=30)

    print("Status Code:", response.status_code)
    print("Server Response:", response.text)


