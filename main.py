import os
import json
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from mailing import build_email, send_email

# ==========================
# LOAD ENV VARIABLES
# ==========================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

# ==========================
# FETCH DATA FROM APPS SCRIPT
# ==========================
BASE_URL = os.getenv("WEBAPP_URL")


params = {
    "query": "getdata",
    "key": SECRET_KEY
}

response = requests.get(BASE_URL, params=params)

if response.status_code != 200:
    raise Exception("Failed to fetch data from Apps Script")

exam_data = response.json()

# ==========================
# VALIDATION CONFIG
# ==========================

ALLOWED_HTML_TAGS = {"a", "strong"}
ALLOWED_APPLICATION_TYPES = {"Deadline", "Opening"}
DATE_FORMAT = "%d-%b-%Y"

REQUIRED_TOP_KEYS = [
    "today_date",
    "welcome_text",
    "quick_summary",
    "execution_tasks",
    "upcoming_exams",
    "application_updates",
    "exit_message",
]

REQUIRED_EXAM_KEYS = ["exam_name", "exam_date", "description"]
REQUIRED_APP_KEYS = ["exam_name", "date", "type"]


def validate_date(date_str):
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except ValueError:
        return False


def validate_html(description):
    tags = re.findall(r"<(/?)(\w+)[^>]*>", description)
    for _, tag in tags:
        if tag not in ALLOWED_HTML_TAGS:
            return False

    anchor_matches = re.findall(r'<a href="([^"]+)">View Sample Papers</a>', description)
    for url in anchor_matches:
        if not url.startswith("http"):
            return False

    return True


def validate_exact_keys(obj, required_keys):
    return list(obj.keys()) == required_keys


def validate_output_json(json_string):
    try:
        data = json.loads(json_string)
    except:
        return False

    if not validate_exact_keys(data, REQUIRED_TOP_KEYS):
        return False

    if not validate_date(data["today_date"]):
        return False

    if not isinstance(data["execution_tasks"], list):
        return False

    if not (1 <= len(data["execution_tasks"]) <= 6):
        return False

    for exam in data["upcoming_exams"]:
        if not validate_exact_keys(exam, REQUIRED_EXAM_KEYS):
            return False
        if not validate_date(exam["exam_date"]):
            return False
        if not validate_html(exam["description"]):
            return False

    for app in data["application_updates"]:
        if not validate_exact_keys(app, REQUIRED_APP_KEYS):
            return False
        if not validate_date(app["date"]):
            return False
        if app["type"] not in ALLOWED_APPLICATION_TYPES:
            return False

    return True


# ==========================
# PREPARE PROMPT
# ==========================

MAIN_PROMPT = """
You are VARAD AI — an advanced academic intelligence engine that generates structured daily academic email content.

Your task is to convert the provided structured exam JSON into the REQUIRED DAILY EMAIL JSON FORMAT.

--------------------------------------------------
CRITICAL RULES (NON-NEGOTIABLE)
--------------------------------------------------

1. Output MUST be valid JSON only.
2. Do NOT include explanations.
3. Do NOT wrap output in markdown.
4. Do NOT change key names.
5. Do NOT change JSON structure.
6. Maintain EXACT key order as defined below.
7. Do NOT add extra fields.
8. Do NOT remove any fields.
9. Respect maximum limits strictly.
10. Do NOT escape HTML.
11. Only allowed HTML tags inside description: <a>, <strong>
12. No other HTML tags are permitted.
13. Ignore any missing or empty fields from input. Use only available data.
14. Use emojis but they should only be used in welcom_text, quick_summary & exit_message only.
15. You should definitely give study_sources links if present in upcoming_exams description using <a> format.
16. application_updates.type MUST strictly be either:
    - "Deadline"
    - "Opening"

--------------------------------------------------
REQUIRED OUTPUT STRUCTURE (DO NOT MODIFY)
--------------------------------------------------

{
  "today_date": "",
  "welcome_text": "",
  "quick_summary": "",
  "execution_tasks": [
    ""
  ],
  "upcoming_exams": [
    {
      "exam_name": "",
      "exam_date": "",
      "description": ""
    }
  ],
  "application_updates": [
    {
      "exam_name": "",
      "date": "",
      "type": ""
    }
  ],
  "exit_message": ""
}

--------------------------------------------------
STRICT BEHAVIOR RULES
--------------------------------------------------

TODAY_DATE:
- Must be taken EXACTLY from input context.
- Use same date format as provided.
- Do NOT generate or infer today's real date.

WELCOME_TEXT:
- Short premium greeting.
- Confident.
- Execution-focused.
- In VARAD AI voice.

QUICK_SUMMARY:
- 2–4 lines.
- Analyze ALL exams, deadlines, openings.
- Do NOT skip any item.
- Do NOT label everything urgent.
- If an exam is scheduled TODAY:
    - After the summary, add a separate final line wishing good luck.
- If an exam is scheduled TOMORROW:
    - Mention final preparation focus.
- If no data exists at all:
    - Light strategic tone.

EXECUTION_TASKS:
- Minimum 1 task.
- Maximum 6 tasks.
- Must be specific and actionable.
- Derived from:
    - upcoming exams
    - additional_remarks (if available)
    - deadlines
    - openings
- Avoid generic phrases like “Study well”.
- If no data exists at all:
    ["NO TASK TODAY"]

UPCOMING_EXAMS:
- Always return an array.
- If none exist → return []
- Mapping:
    name → exam_name
    start_date → exam_date
- description:
    - AI-generated
    - Maximum 4 sentences
    - May use <strong>
    - You should definitely give study_sources links if present in upcoming_exams description using <a> format.
    - Do NOT modify URL
    - No other HTML tags allowed

APPLICATION_UPDATES:
- Always return an array.
- Combine:
    "Form Filling Deadlines" → type = "Deadline"
    "Forms Opening" → type = "Opening"
- If none exist → return []
- type MUST be exactly:
    "Deadline"
    or
    "Opening"

EMPTY DATA RULE:
If ALL sections empty:
- execution_tasks → ["NO TASK TODAY"]
- upcoming_exams → []
- application_updates → []
- quick_summary → light strategic summary
- exit_message → encourage skill-building & long-term prep

EXIT_MESSAGE:
- 1–2 lines.
- Motivational.
- Context-aware.

--------------------------------------------------
INPUT DATA:
--------------------------------------------------
"""

today_date = datetime.now().strftime("%d-%b-%Y")

final_prompt = f"""
{MAIN_PROMPT}

Today's Date: {today_date}

Exam Data:
{json.dumps(exam_data, indent=2)}

Return JSON only
"""

# ==========================
# RETRY LOOP
# ==========================

MAX_RETRIES = 3
attempt = 0
valid_output = None

while attempt < MAX_RETRIES:
    attempt += 1
    print(f"\nAttempt {attempt}...")

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0
    )

    llm_output = completion.choices[0].message.content.strip()

    if validate_output_json(llm_output):
        print("✅ Valid JSON received.")
        valid_output = llm_output
        break
    else:
        print("❌ Invalid output. Retrying...")

if valid_output:
    print("✅ Valid JSON received. Sending email...")

    ai_response_json = json.loads(valid_output)

    final_html = build_email(ai_response_json)

    send_email(final_html)
else:
    print("\n❌ Failed after 3 attempts. No valid JSON generated.")