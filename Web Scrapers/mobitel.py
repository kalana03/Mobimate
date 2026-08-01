import scraper
from bs4 import BeautifulSoup
import package_formatting
import requests

url = "https://www.mobitel.lk/broadband/plans-and-rates-prepaid"
soup = scraper.scrape(url)

plans_section = soup.find('div', class_='page_tabing_title_area')
if plans_section is None:
    raise ValueError('Could not find plans section in HTML')

plan_btns = plans_section.find_all('div', class_='title_parent')

plans = []
for plan in plan_btns:
    pln = plan.find('a')
    if pln is None:
        continue
    plans.append([pln.get_text(strip=True), pln.get('href')])

print(f"Found {len(plans)} plan tabs.")

all_extracted_packages = []

for i, plan in enumerate(plans, start=1):
    tab_name = plan[0]  # 👈 Tab name (e.g., "NONSTOP TIKTOK", "Social Combo")
    
    body = soup.find('div', class_='tab_content_{}'.format(i))
    if body is None:
        continue
    
    topic = body.find(string="Package Details")
    if topic is not None:
        table = topic.find_next('table')
    else:
        table = body.find('table')
        
    if table is not None:
        # 🧹 Convert table HTML tags into clean, human-readable text
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(" | ".join(cells))
        table_text = "\n".join(rows)
    else:
        # Prose-based tabs (e.g. MOBITEL 1278) have no <table>; use full body text
        table_text = body.get_text("\n", strip=True)

    if not table_text.strip():
        continue

    # 🚀 Pass both table_text AND tab_name to the formatting function
    print(f"Extracting package [{i}/{len(plans)}]: {tab_name}...")
    extracted_data = package_formatting.format_packages(table_text, tab_name=tab_name)
    
    if extracted_data and "packages" in extracted_data:
        all_extracted_packages.extend(extracted_data["packages"])

# 🖨️ Print final extracted package results
print("\n=== EXTRACTED PACKAGES ===")
for pkg in all_extracted_packages:
    print(pkg)


BASE_URL = "http://localhost:8000"

response = requests.get(f"{BASE_URL}/packages/Mobitel")
response.raise_for_status()
existing_active_packages = response.json()

COMPARE_FIELDS = [
    "package_name",
    "price",
    "validity_days",
    "fup_gb",
    "is_fup_per_day",
    "anytime_data_gb",
    "voice_mins",
    "sms_count",
    "is_data_rollover",
]

packages_to_insert = []
packages_to_update = []

for pkg in all_extracted_packages:
    match = next(
        (existing for existing in existing_active_packages if existing["price"] == pkg.get("price")),
        None,
    )

    if match is None:
        packages_to_insert.append(pkg)
        continue

    fields_differ = any(match.get(field) != pkg.get(field) for field in COMPARE_FIELDS)
    if fields_differ:
        packages_to_update.append((match["package_id"], pkg))

    existing_active_packages.remove(match)

if packages_to_insert:
    insert_resp = requests.post(f"{BASE_URL}/insert-packages/", json=packages_to_insert)
    insert_resp.raise_for_status()
    print(f"Inserted {len(packages_to_insert)} new packages.")

for package_id, pkg in packages_to_update:
    update_resp = requests.put(f"{BASE_URL}/packages/{package_id}", json=pkg)
    update_resp.raise_for_status()
    print(f"Updated package {package_id}: {pkg.get('package_name')}")

if existing_active_packages:
    stale_ids = [existing["package_id"] for existing in existing_active_packages]
    deact_resp = requests.put(f"{BASE_URL}/packages/deactivate/", json=stale_ids)
    deact_resp.raise_for_status()
    print(f"Deactivated {len(stale_ids)} stale packages.")