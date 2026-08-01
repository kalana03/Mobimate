import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

BASE_URL = "http://localhost:8000"
NEW_APP_NOTIFY_EMAIL = "knbabeysundara@gmail.com"
DEFAULT_APP_ICON_URL = "https://mobimate.lk/default-app-icon.png"

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


def get_apps():
    response = requests.get(f"{BASE_URL}/apps")
    response.raise_for_status()
    return response.json()


def sync_packages(all_extracted_packages, carrier):
    response = requests.get(f"{BASE_URL}/packages/{carrier}")
    response.raise_for_status()
    existing_active_packages = response.json()

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


def insert_new_app(app_name, package_name, app_by_name, carrier):
    insert_resp = requests.post(
        f"{BASE_URL}/insert-apps/",
        json=[{"app_name": app_name, "app_icon_url": DEFAULT_APP_ICON_URL}],
    )
    insert_resp.raise_for_status()
    result = insert_resp.json()

    app_id = None
    if result.get("inserted"):
        app_id = result["inserted"][0]["app_id"]
    elif result.get("skipped"):
        app_id = result["skipped"][0]["app_id"]

    if app_id is not None:
        app_by_name[app_name.lower()] = app_id
        send_new_app_email(app_name, package_name, carrier)
    return app_id


def send_new_app_email(app_name, package_name, carrier):
    mail_user = os.environ.get("MAIL_USER")
    mail_pass = os.environ.get("MAIL_PASS")
    if not mail_user or not mail_pass:
        print(f"Mail credentials missing; skipped new-app notification for '{app_name}'.")
        return

    smtp_host = os.environ.get("MAIL_SMTP", "smtp.gmail.com")
    smtp_port = int(os.environ.get("MAIL_SMTP_PORT", "587"))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[MobiMate] New app entered: {app_name}"
    msg["From"] = mail_user
    msg["To"] = NEW_APP_NOTIFY_EMAIL

    body = (
        f"A new app has been entered into the MobiMate database.\n\n"
        f"App name: {app_name}\n"
        f"App icon: {DEFAULT_APP_ICON_URL}\n"
        f"Linked to package: {package_name} ({carrier})\n\n"
        f"The app '{app_name}' was not found in the apps table, so a new record was inserted."
    )
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_user, NEW_APP_NOTIFY_EMAIL, msg.as_string())
        print(f"New-app email sent for '{app_name}'.")
    except Exception as e:
        print(f"Failed to send new-app email for '{app_name}': {e}")


def sync_package_apps(all_extracted_packages, apps, carrier):
    app_by_name = {app["app_name"].lower(): app["app_id"] for app in apps}

    response = requests.get(f"{BASE_URL}/packages/{carrier}")
    response.raise_for_status()
    packages = response.json()

    links = []
    for pkg in all_extracted_packages:
        app_names = pkg.get("app_names") or []
        if not app_names:
            continue

        match = next(
            (existing for existing in packages if existing["price"] == pkg.get("price")),
            None,
        )
        if match is None:
            continue

        package_id = match["package_id"]
        for app_name in app_names:
            app_id = app_by_name.get(app_name.lower())
            if app_id is None:
                app_id = insert_new_app(app_name, pkg.get("package_name", ""), app_by_name, carrier)
            if app_id is not None:
                links.append({"package_id": package_id, "app_id": app_id})

    if links:
        link_resp = requests.post(f"{BASE_URL}/insert-package-apps/", json=links)
        link_resp.raise_for_status()
        print(f"Linked {len(links)} package-app pairs.")

    return links
