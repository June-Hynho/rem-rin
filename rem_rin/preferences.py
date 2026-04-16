import json
from pathlib import Path
from platformdirs import user_config_dir

from rem_rin import APP_NAME


file = Path(user_config_dir(APP_NAME)) / 'preferences.json'

def get_preference(prop):
    with open('preferences.json') as f:
        pref = json.load(f)
    return pref.get(prop, None)


def set_preference(prop, value):
    with open('preferences.json') as f:
        pref = json.load(f)
    pref[prop] = value
    with open('preferences.json', 'w') as f:
        json.dump(pref, f)

