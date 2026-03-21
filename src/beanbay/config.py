from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Parameters
    ----------
    database_url : str
        SQLAlchemy database URL. Defaults to a local SQLite file.
    default_person_name : str
        Name used for the default person record.
    """

    database_url: str = "sqlite:///beanbay.db"
    default_person_name: str = "Default"

    model_config = SettingsConfigDict(env_prefix="BEANBAY_")


settings = Settings()
