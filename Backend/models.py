from sqlalchemy import Column, Integer, String, Float, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


package_apps = Table(
    "package_apps",
    Base.metadata,
    Column("package_id", Integer, ForeignKey("packages.package_id"), primary_key=True),
    Column("app_id", Integer, ForeignKey("apps.app_id"), primary_key=True),
)


class Package(Base):
    __tablename__ = "packages"

    package_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    carrier = Column(String, nullable=False)
    package_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    validity_days = Column(Integer, nullable=False)
    fup_gb = Column(Float, default=0)
    is_fup_per_day = Column(Boolean, default=False)
    anytime_data_gb = Column(Float, default=0)
    voice_mins = Column(Integer, default=0)
    sms_count = Column(Integer, default=0)
    is_data_rollover = Column(Boolean, default=False)
    is_active = Column(Integer, default=1)

    apps = relationship("App", secondary=package_apps, back_populates="packages")


class App(Base):
    __tablename__ = "apps"

    app_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    app_name = Column(String, unique=True, nullable=False)
    app_icon_url = Column(String, nullable=True)

    packages = relationship("Package", secondary=package_apps, back_populates="apps")
