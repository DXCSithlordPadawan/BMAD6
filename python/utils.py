import yaml
import os
from django.conf import settings

def get_bmad_config():
    config_path = os.path.join(settings.BASE_DIR, 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f).get('app_settings', {})

def ensure_base_path():
    config = get_bmad_config()
    path = config.get('base_location', './bmad_output/')
    if not os.path.exists(path):
        os.makedirs(path)
    return path