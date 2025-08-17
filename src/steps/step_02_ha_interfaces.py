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
    
    def _check_ha_interface_status(self, device, headers, interface):
        """
        Check if HA interface is already configured.
        
        Args:
            device: Device credentials
            headers: API headers with key
            interface: Interface name (e.g., 'ethernet1/4')
            
        Returns:
            bool: True if already configured as HA, False otherwise
        """
        try:
            check_url = f"https://{device['host']}/api/"
            check_params = {
                'type': 'config',
                'action': 'get',
                'xpath': f"/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet/entry[@name='{interface}']",
                'key': headers['X-PAN-KEY']
            }
            
            response = requests.get(check_url, params=check_params, verify=False, timeout=30)
            
            if response.status_code == 200:
                xml_response = response.text
                root = ET.fromstring(xml_response)
                
                # Check if <ha/> element exists in the interface configuration
                ha_element = root.find(".//ha")
                if ha_element is not None:
                    logger.info(f"Interface {interface} on {device['host']} is already configured for HA")
                    return True
                else:
                    logger.info(f"Interface {interface} on {device['host']} is NOT configured for HA")
                    return False
            else:
                logger.warning(f"Could not check HA status for {interface} on {device['host']}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking HA interface status for {interface} on {device['host']}: {e}")
            return False
    
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
            
            changes_made = False
            
            # Your exact original logic from enable_HA_interfaces() with HA check
            for device, headers in zip(pa_credentials, api_keys_list):
                interfaces = ['ethernet1/4', 'ethernet1/5']
                device_changes = False
                
                try:
                    ha_interfaces_link_url = f"https://{device['host']}/api/"
                    
                    for interface in interfaces:
                        # Check if interface is already configured for HA
                        if self._check_ha_interface_status(device, headers, interface):
                            logger.info(f"Skipping {interface} on {device['host']} - already configured for HA")
                            continue
                        
                        # Configure interface for HA
                        logger.info(f"Configuring {interface} on {device['host']} for HA")
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
                            logger.info(f"HA interface {interface} enabled on {device['host']}")
                            logger.info(xml_response_control)
                            device_changes = True
                            changes_made = True
                        else:
                            logger.error(f"Failed to enable HA interface {interface} on {device['host']}: {response_control.status_code}")
                            return False
                    
                    if device_changes:
                        logger.info(f"HA interfaces configuration completed for {device['host']}")
                    else:
                        logger.info(f"No HA interface changes needed for {device['host']}")
                        
                except Exception as e:
                    logger.error(f"Error in HA configuration for {device['host']}: {e}")
                    return False
            
            # Only commit if changes were made
            if changes_made:
                logger.info("Changes made - proceeding with commit")
                from utils_pa import commit_changes
                success = commit_changes(pa_credentials, api_keys_list, "HA Interfaces")
                if not success:
                    return False
            else:
                logger.info("No changes made - skipping commit")
            
            # Save completion status for next steps
            step_data = {
                'ha_interfaces_enabled': True,
                'changes_made': changes_made,
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