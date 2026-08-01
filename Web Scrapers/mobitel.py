import scraper
import package_formatting
import common

CARRIER = "Mobitel"
SCRAPE_URL = "https://www.mobitel.lk/broadband/plans-and-rates-prepaid"


def get_plan_tabs(soup):
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
    return plans


def extract_tab_text(soup, index):
    body = soup.find('div', class_='tab_content_{}'.format(index))
    if body is None:
        return None

    topic = body.find(string="Package Details")
    if topic is not None:
        table = topic.find_next('table')
    else:
        table = body.find('table')

    if table is not None:
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(" | ".join(cells))
        table_text = "\n".join(rows)
    else:
        table_text = body.get_text("\n", strip=True)

    if not table_text.strip():
        return None
    return table_text


def extract_packages(soup, plans, apps_list):
    all_extracted_packages = []

    for i, plan in enumerate(plans, start=1):
        tab_name = plan[0]

        table_text = extract_tab_text(soup, i)
        if table_text is None:
            continue

        print(f"Extracting package [{i}/{len(plans)}]: {tab_name}...")
        extracted_data = package_formatting.format_packages(
            table_text, tab_name=tab_name, carrier=CARRIER, apps_list=apps_list
        )

        if extracted_data and "packages" in extracted_data:
            all_extracted_packages.extend(extracted_data["packages"])

    print("\n=== EXTRACTED PACKAGES ===")
    for pkg in all_extracted_packages:
        print(pkg)

    return all_extracted_packages


def main():
    soup = scraper.scrape(SCRAPE_URL)
    plans = get_plan_tabs(soup)
    apps = common.get_apps()
    all_extracted_packages = extract_packages(soup, plans, apps)
    common.sync_packages(all_extracted_packages, CARRIER)
    common.sync_package_apps(all_extracted_packages, apps, CARRIER)


if __name__ == "__main__":
    main()
