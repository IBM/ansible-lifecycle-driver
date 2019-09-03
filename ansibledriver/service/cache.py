import logging
from common_cache import Cache
from ignition.model.lifecycle import LifecycleExecution, STATUS_IN_PROGRESS
from ignition.service.config import ConfigurationPropertiesGroup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_RESPONSE = LifecycleExecution(None, STATUS_IN_PROGRESS, None, {})

class CacheProperties(ConfigurationPropertiesGroup):
    def __init__(self):
        super().__init__('response_cache')
        # apply defaults (correct settings will be picked up from config file or environment variables)
        self.cache_expiry = 300 # in seconds
        self.max_cache_capacity = 1000

class ResponseCache(object):
    def __init__(self, configuration):
      cache_properties = configuration.property_groups.get_property_group(CacheProperties)
      self.cache = Cache(capacity=cache_properties.max_cache_capacity, expire=cache_properties.cache_expiry)
      self.active = True

    def update_response(self, response):
      # if self.active:
      logger.info('update_response: ' + str(response))
      self.cache[response.request_id] = response

    def get_response(self, request_id):
      return self.cache[request_id]

    def close(self):
      self.active = False
      self.cache.shutdown_thread_pool()
