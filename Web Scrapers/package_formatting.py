import json
import os
import re
from openai import OpenAI
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

PROMPT_TEMPLATE = """You are a data extraction engine for Sri Lankan telecom mobile data packages.
Below is scraped content (HTML table data or tariff prose) from the "{carrier}" carrier's prepaid broadband page under the Tab Name: "{tab_name}".

Analyze the table intelligently and extract every distinct package into JSON.

Output shape (ONLY this JSON format):
{{
  "packages": [
    {{
      "carrier": "{carrier}",
      "package_name": "...",
      "price": 0.0,
      "validity_days": 0,
      "fup_gb": 0,
      "is_fup_per_day": false,
      "anytime_data_gb": 0,
      "voice_mins": 0,
      "sms_count": 0,
      "is_data_rollover": false,
      "is_active": 1,
      "app_names": []
    }}
  ]
}}

NAMING RULES FOR 'package_name':
- Use the Tab Name "{tab_name}" as the primary package name.
- If the table contains multiple sub-packages (e.g., "7 Days", "30 Days", "Daily"), combine the Tab Name with the sub-plan column title.
  * Example: Tab Name = "Social Combo", Column = "30 Days Package" -> package_name = "Social Combo 30 Days"
  * Example: Tab Name = "NONSTOP TIKTOK", Column = "7 Day Pack" -> package_name = "NONSTOP TIKTOK 7 Days"
  * Example: Tab Name = "MOBITEL 1598", Single Plan -> package_name = "MOBITEL 1598"
  * Example: Tab Name = "MOBITEL 1278 & 368", "Mobitel 1278" is one package and "Mobitel 368" is another package
- ALWAYS set "carrier" to the actual carrier name: "{carrier}".

ALLOWED APPS: {apps}

Rules:
- "app_names" should use the exact app names from the ALLOWED APPS list above wherever possible. Do NOT invent, paraphrase, or abbreviate app names; use the exact names as written.
- If a bonus app mentioned in the content is NOT in the ALLOWED APPS list, you MAY still include it, using the exact name as written in the content.


Rules:
- Parse prices, validity, GB allowances, voice minutes, and SMS counts from the text.
- If a value is absent, use defaults (0, false).
- Output ONLY valid JSON object.
- Some sections could contain more than one package, in those instances, intelligently seperate them to 2 different packages
- can have duplicates of the same package throughout the body, be mindful.

TAB NAME: {tab_name}
CARRIER: {carrier}
TABLE CONTENT:
{body}
"""

def format_packages(body_text: str, tab_name: str, carrier: str, apps_list: list) -> dict:
    prompt = PROMPT_TEMPLATE.format(tab_name=tab_name, carrier=carrier, apps=", ".join(app["app_name"] for app in apps_list), body=str(body_text))

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a specialized JSON extraction engine."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        return json.loads(raw_content)
    except Exception as e:
        print(f"Error formatting package [{tab_name}]: {e}")
        return {"packages": []}