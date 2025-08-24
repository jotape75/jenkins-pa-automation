"""
Step 5: Configure Interfaces on Active Firewall

Extracts the act_fw_int_config logic from PaloAltoFirewall_config class
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

class Step05_Interfaces:
    """
    Configure physical interfaces on active firewall.
    
    Applies interface IP addressing, zone assignments, and Layer 3
    settings using predefined XML templates.
    """
    
    def __init__(self):
        """
        Initialize interface configuration step.
        """
        pass
    
    def execute(self):
        """
        Configure physical interfaces on active firewall.
        
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
                logger.info("Using active firewall data for interface configuration")
                
            except FileNotFoundError:
                logger.error("Active firewall data not found. Run identify_active step first.")
                return False
            
            # Load interface template
            try:
                from utils_pa import PA_INTERFACE_TEMPLATE
                with open(PA_INTERFACE_TEMPLATE, 'r') as f:
                    pa_interface_tmp = f.read()
                logger.info(f"Loaded interface template from {PA_INTERFACE_TEMPLATE}")
            except Exception as e:
                logger.error(f"Failed to load interface template: {e}")
                return False
            
            logger.info(f"Configuring interfaces on active firewall: {active_fw_list[0]['host']}")
            
            # Exact original logic from act_fw_int_config()
            try:
                interface_xpath = f"/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet"
                
                # Apply configuration to active firewall
                config_url = f"https://{active_fw_list[0]['host']}/api/"
                interface_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': interface_xpath,
                    'element': pa_interface_tmp,
                    'key': active_fw_headers[0]['X-PAN-KEY']
                }

                response_interface = requests.get(config_url, params=interface_params, verify=False)
                
                if response_interface.status_code == 200:
                    logger.info(f"Interfaces configured successfully on {active_fw_list[0]['host']}")
                    logger.info(f"Response: {response_interface.text}")
                else:
                    logger.error(f"Failed to configure interfaces on {active_fw_list[0]['host']}: {response_interface.status_code}")
                    logger.error(f"Response: {response_interface.text}")
                    return False

            except Exception as e:
                logger.error(f"Error in interface configuration process: {e}")
                return False
            
            # Save completion status for next steps
            step_data = {
                'interfaces_configured': True,
                'active_fw_list': active_fw_list,
                'active_fw_headers': active_fw_headers,
                'interface_configuration_completed': True
            }
            
            with open('interfaces_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("Interface configuration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in interface configuration: {e}")
            return False