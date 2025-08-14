import os
import json
from pathlib import Path

def get_project_root():
    """
    Get the project root directory (where Jenkinsfile is located).
    Works in both local development and Jenkins containers.
    """
    current_file = Path(__file__).resolve()
    # Navigate up from src/utils_pa.py to project root
    project_root = current_file.parent.parent
    return project_root

# Project paths (hardcoded constants - more reliable)
PROJECT_ROOT = get_project_root()
DATA_DIR = PROJECT_ROOT / "data" # navigate to data directory
PAYLOAD_DIR = DATA_DIR / "payload" # navigate to payload directory

# File paths as constants (no external JSON dependency)
PA_CREDS_FILE = DATA_DIR / "dev_creds_pa.json"
PA_HA_CONFIG_TEMPLATE = PAYLOAD_DIR / "paloalto_ha_template_config.xml"
PA_HA_INT_TEMPLATE = PAYLOAD_DIR / "paloalto_interface_ha_template.xml"
PA_INTERFACE_TEMPLATE = PAYLOAD_DIR / "data_interface.xml"
PA_ZONES_TEMPLATE = PAYLOAD_DIR / "zones.xml"
PA_ROUTER_TEMPLATE = PAYLOAD_DIR / "virtual_router_template.xml"
PA_ROUTES_TEMPLATE = PAYLOAD_DIR / "static_route_template.xml"
PA_SECURITY_TEMPLATE = PAYLOAD_DIR / "security_policy_template.xml"
PA_NAT_TEMPLATE = PAYLOAD_DIR / "source_nat_template.xml"

def file_path():
    """
    Load configurations and return file paths.
    No external JSON dependency - more reliable for Jenkins.
    """
    # Load PA credentials directly
    with open(PA_CREDS_FILE, 'r') as f:
        pa_credentials = json.load(f)
    
    return (
        pa_credentials,
        str(PA_HA_CONFIG_TEMPLATE),
        str(PA_HA_INT_TEMPLATE),
        str(PA_INTERFACE_TEMPLATE),
        str(PA_ZONES_TEMPLATE),
        str(PA_ROUTER_TEMPLATE),
        str(PA_ROUTES_TEMPLATE),
        str(PA_SECURITY_TEMPLATE),
        str(PA_NAT_TEMPLATE)
    )