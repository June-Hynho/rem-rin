import json
from platformdirs import user_config_dir, user_cache_dir

from rem_rin import APP_NAME

cache_dir = user_cache_dir(APP_NAME)
config_dir = user_config_dir(APP_NAME)


