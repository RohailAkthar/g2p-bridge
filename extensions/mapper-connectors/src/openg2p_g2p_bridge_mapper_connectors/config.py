from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="g2p_bridge_mapper_connectors_", env_file=".env", extra="allow"
    )

    # SPAR Mapper configuration
    spar_mapper_url: str = "http://localhost:8080/mapper/resolve"
    spar_mapper_api_sign_enabled: bool = False
    spar_mapper_api_sign_crypto_helper_name: str = "spar_mapper_crypto"

    mapper_type: str = "registry"

    # Registry database connection settings
    db_driver_registry: str = "postgresql"
    db_username_registry: str = "odoo_user"
    db_password_registry: str = "odoo123"
    db_hostname_registry: str = "localhost"
    db_port_registry: int = 5434
    db_dbname_registry: str = "odoo_SR"
