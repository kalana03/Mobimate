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
Below is scraped content (HTML table data or tariff prose) from Mobitel's prepaid broadband page under the Tab Name: "{tab_name}".

Analyze the table intelligently and extract every distinct package into JSON.

Output shape (ONLY this JSON format):
{{
  "packages": [
    {{
      "carrier": "Mobitel",
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
- ALWAYS set "carrier": "Mobitel".

Rules:
- Parse prices, validity, GB allowances, voice minutes, and SMS counts from the text.
- If a value is absent, use defaults (0, false).
- Output ONLY valid JSON object.

TAB NAME: {tab_name}
TABLE CONTENT:
{body}
"""

def format_packages(body_text: str, tab_name: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(tab_name=tab_name, body=str(body_text))

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