"""
Step 2: Enable HA Interfaces for PA Firewalls

Extracts the enable_HA_interfaces logic from PaloAltoFirewall_HA class
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

class Step02_HAInterfaces:
    """
    Enable HA interfaces (ethernet1/4 and ethernet1/5) on all devices.
    
    Direct extraction from PaloAltoFirewall_HA.enable_HA_interfaces() method.
    """
    
    def __init__(self):
        """
        Initialize HA interfaces enablement step.
        """
        pass
    
    def execute(self):
        """
        Enable HA interfaces on all devices.
        Uses the exact logic from your original enable_HA_interfaces() method.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load API keys and credentials from Step 1
            with open('api_keys_data.pkl', 'rb') as f:
                api_data = pickle.load(f)
            
            pa_credentials = api_data['pa_credentials']
            api_keys_list = api_data['api_keys_list']
            
            logger.info(f"Enabling HA interfaces for {len(pa_credentials)} devices")
            
            # Your exact original logic from enable_HA_interfaces()
            for device, headers in zip(pa_credentials, api_keys_list):
                interfaces = ['ethernet1/4', 'ethernet1/5']
                try:
                    ha_interfaces_link_url = f"https://{device['host']}/api/"
                    for interface in interfaces:
                        interfaces_xml_parms = {
                            'type': 'config',
                            'action': 'set',
                            'xpath': f"/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet/entry[@name='{interface}']",
                            'element': '<ha/>',
                            'override': 'yes',
                            'key': headers['X-PAN-KEY']  # API key as parameter
                        }
                        response_control = requests.get(ha_interfaces_link_url, params=interfaces_xml_parms, verify=False, timeout=30)
                    
                    if response_control.status_code == 200:
                        xml_response_control = response_control.text
                        logger.info(f"HA interfaces enabled on {device['host']}")
                        logger.info(xml_response_control)
                    else:
                        logger.error(f"Failed to enable HA interfaces on {device['host']}: {response_control.status_code}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error in HA configuration for {device['host']}: {e}")
                    return False
            
            # Use shared commit utility from utils_pa
            from utils_pa import commit_changes
            success = commit_changes(pa_credentials, api_keys_list, "HA Interfaces")
            if not success:
                return False
            
            # Save completion status for next steps
            step_data = {
                'ha_interfaces_enabled': True,
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list
            }
            
            with open('ha_interfaces_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("HA interfaces enablement completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in HA interfaces enablement: {e}")
            return False