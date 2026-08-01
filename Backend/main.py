from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select
import models
from database import get_db

app = FastAPI()


def package_to_dict(pkg: models.Package) -> Dict[str, Any]:
    return {
        "package_id": pkg.package_id,
        "carrier": pkg.carrier,
        "package_name": pkg.package_name,
        "price": pkg.price,
        "validity_days": pkg.validity_days,
        "fup_gb": pkg.fup_gb,
        "is_fup_per_day": pkg.is_fup_per_day,
        "anytime_data_gb": pkg.anytime_data_gb,
        "voice_mins": pkg.voice_mins,
        "sms_count": pkg.sms_count,
        "is_data_rollover": pkg.is_data_rollover,
        "is_active": pkg.is_active,
    }


class PackageIn(BaseModel):
    carrier: str
    package_name: str
    price: float
    validity_days: int
    fup_gb: int = 0
    is_fup_per_day: bool = False
    anytime_data_gb: int = 0
    voice_mins: int = 0
    sms_count: int = 0
    is_data_rollover: bool = False
    is_active: int = 1


class PackageAppIn(BaseModel):
    package_id: int
    app_id: int

@app.get("/packages/{carrier}")
def get_package_list(carrier: str, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    query = select(models.Package).where(
        models.Package.carrier == carrier,
        models.Package.is_active == True
    )
    result = db.execute(query)
    return [package_to_dict(pkg) for pkg in result.scalars()]


@app.post("/insert-packages/")
def insert_packages(packages: List[PackageIn], db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    db_items = [
        models.Package(
            carrier=pkg.carrier,
            package_name=pkg.package_name,
            price=pkg.price,
            validity_days=pkg.validity_days,
            fup_gb=pkg.fup_gb,
            is_fup_per_day=pkg.is_fup_per_day,
            anytime_data_gb=pkg.anytime_data_gb,
            voice_mins=pkg.voice_mins,
            sms_count=pkg.sms_count,
            is_data_rollover=pkg.is_data_rollover,
            is_active=pkg.is_active
        )
        for pkg in packages
    ]

    db.add_all(db_items)
    db.commit()

    return [package_to_dict(pkg) for pkg in db_items]


@app.put("/packages/{package_id}")
def update_package(package_id: int, pkg: PackageIn, db: Session = Depends(get_db)) -> Dict[str, Any]:
    record = db.get(models.Package, package_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Package not found")

    for field in PackageIn.model_fields:
        setattr(record, field, getattr(pkg, field))

    db.commit()
    db.refresh(record)
    return package_to_dict(record)


@app.put("/packages/deactivate/")
def deactivate_packages(package_ids: List[int], db: Session = Depends(get_db)) -> Dict[str, Any]:
    records = db.execute(
        select(models.Package).where(models.Package.package_id.in_(package_ids))
    ).scalars().all()

    for record in records:
        record.is_active = 0

    db.commit()
    return {"deactivated": len(records)}


@app.post("/insert-package-apps/")
def insert_package_apps(links: List[PackageAppIn], db: Session = Depends(get_db)) -> Dict[str, Any]:
    inserted = []
    for link in links:
        db.execute(
            models.package_apps.insert().values(package_id=link.package_id, app_id=link.app_id)
        )
        inserted.append({"package_id": link.package_id, "app_id": link.app_id})

    db.commit()
    return {"inserted": inserted, "count": len(inserted)}
