from typing import List

class ConfigHandler:

    _instance = None

    @classmethod
    def instance(cls) -> 'ConfigHandler':
        if cls._instance is None:
            cls._instance = ConfigHandler()
        return cls._instance

    def set_config_variables(self, var_list: List[str]):
        for var_str in var_list:
            k, v = var_str.split(':=')
            self.__dict__[k] = v
            
        