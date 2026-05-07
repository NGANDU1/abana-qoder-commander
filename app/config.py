import os

from dotenv import load_dotenv


class AppConfig:
    """
    Central configuration object.
    Uses .env for local development to keep secrets out of source.
    """

    def __init__(self) -> None:
        load_dotenv()

        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
        self.SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///smart_waste.db")
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        self.DEPOT_LAT = float(os.getenv("DEPOT_LAT", "51.5074"))
        self.DEPOT_LON = float(os.getenv("DEPOT_LON", "-0.1278"))

        # Optional: allow admin self-signup when a code is provided.
        # If unset/empty, admin accounts should be created by an existing admin.
        self.ADMIN_SIGNUP_CODE = os.getenv("ADMIN_SIGNUP_CODE", "").strip() or None
