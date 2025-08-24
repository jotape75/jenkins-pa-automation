"""
Step 6: Configure Security Zones on Active Firewall

Extracts the act_fw_zone_config logic from PaloAltoFirewall_config class
and adapts it for Jenkins execution.
"""

import requests
import logging
import pickle
import json
import xml.etree.ElementTree as ET
import sys
import os

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step06_Zones:
    """
    Configure security zones on active firewall.
    
    Applies zone definitions and interface assignments
    using predefined XML templates.
    """
    
    def __init__(self):
        """
        Initialize zone configuration step.
        """
        pass
    
    def execute(self):
        """
        Configure security zones on active firewall.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load active firewall data from previous step
            try:
                with open('active_fw_data.pkl', 'rb') as f:
                    active_fw_data = pickle.load(f)
                
                active_fw_list = active_fw_data['active_fw_list']
                active_fw_headers = active_fw_data['active_fw_headers']
                logger.info("Using active firewall data for zone configuration")
                
            except FileNotFoundError:
                logger.error("Active firewall data not found. Run identify_active step first.")
                return False
            
            # Check discovery data for existing zones
            try:
                with open('discovery_data.pkl', 'rb') as f:
                    discovery_data = pickle.load(f)
                
                device_status = discovery_data['device_status']
                active_host = active_fw_list[0]['host']
                
                if active_host in device_status:
                    existing_zones = device_status[active_host]['zones']
                    if existing_zones:
                        logger.info(f"Existing zones found on {active_host}: {list(existing_zones.keys())}")
                        logger.info("Zones already configured - skipping configuration")
                        
                        # Save completion status anyway
                        step_data = {
                            'zones_configured': True,
                            'zones_skipped': True,
                            'existing_zones': existing_zones,
                            'active_fw_list': active_fw_list,
                            'active_fw_headers': active_fw_headers,
                            'zone_configuration_completed': True
                        }
                        
                        with open('zones_data.pkl', 'wb') as f:
                            pickle.dump(step_data, f)
                        
                        logger.info("Zone configuration completed (skipped - already configured)")
                        return True
                        
            except FileNotFoundError:
                logger.warning("Discovery data not found, proceeding with zone configuration")
            
            # Load zone template
            try:
                from utils_pa import PA_ZONES_TEMPLATE
                with open(PA_ZONES_TEMPLATE, 'r') as f:
                    pa_zones_tmp = f.read()
                logger.info(f"Loaded zones template from {PA_ZONES_TEMPLATE}")
            except Exception as e:
                logger.error(f"Failed to load zones template: {e}")
                return False
            
            logger.info(f"Configuring zones on active firewall: {active_fw_list[0]['host']}")
            
            # Exact original logic from act_fw_zone_config()
            try:
                zones_xpath = f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/zone"
                
                # Apply configuration to active firewall
                config_url = f"https://{active_fw_list[0]['host']}/api/"
                zones_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': zones_xpath,
                    'element': pa_zones_tmp,
                    'key': active_fw_headers[0]['X-PAN-KEY']
                }

                response_zones = requests.get(config_url, params=zones_params, verify=False)
                
                if response_zones.status_code == 200:
                    logger.info(f"Zones configured successfully on {active_fw_list[0]['host']}")
                    logger.info(f"Response: {response_zones.text}")
                else:
                    logger.error(f"Failed to configure zones on {active_fw_list[0]['host']}: {response_zones.status_code}")
                    logger.error(f"Response: {response_zones.text}")
                    return False

            except Exception as e:
                logger.error(f"Error in zone configuration process: {e}")
                return False
            
            # Save completion status for next steps
            step_data = {
                'zones_configured': True,
                'zones_skipped': False,
                'active_fw_list': active_fw_list,
                'active_fw_headers': active_fw_headers,
                'zone_configuration_completed': True
            }
            
            with open('zones_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("Zone configuration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in zone configuration: {e}")
            return False