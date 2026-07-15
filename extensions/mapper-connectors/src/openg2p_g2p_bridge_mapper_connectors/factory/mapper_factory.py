from openg2p_fastapi_common.service import BaseService

from ..implementations.spar_mapper import SPARMapper
from ..implementations.registry_mapper import RegistryMapper
from ..interface.mapper_interface import MapperInterface
from ..config import Settings

_config = Settings.get_config()


class MapperFactory(BaseService):
    @staticmethod
    def get_mapper() -> MapperInterface:
        if _config.mapper_type == "registry":
            return RegistryMapper.get_component()
        return SPARMapper.get_component()
