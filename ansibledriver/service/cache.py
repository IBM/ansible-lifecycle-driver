import logging
from ignition.service.config import ConfigurationPropertiesGroup

logger = logging.getLogger(__name__)

class CacheProperties(ConfigurationPropertiesGroup):
    def __init__(self):
        super().__init__('response_cache')
        # apply defaults (correct settings will be picked up from config file or environment variables)
        self.cache_expiry = 300 # in seconds
        self.max_cache_capacity = 1000
