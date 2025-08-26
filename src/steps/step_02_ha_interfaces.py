"""
Step 2: Enable HA Interfaces for PA Firewalls

Extracts the enable_HA_interfaces logic from PaloAltoFirewall_HA class
and adapts it for Jenkins execution with discovery-based checking.
Uses HA interfaces directly from Jenkins form parameters.
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
    Enable HA interfaces dynamically based on Jenkins form parameters.
    User specifies which interfaces to use via Jenkins form.
    
    Uses discovery data to check current status instead of making API calls.
    """
    
    def __init__(self):
        """
        Initialize HA interfaces enablement step.
        """
        pass
    
    def execute(self):
        """
        Enable HA interfaces on all devices.
        Uses discovery data to check current status and avoid unnecessary changes.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load discovery data to check current status
            try:
                with open('discovery_data.pkl', 'rb') as f:
                    discovery_data = pickle.load(f)
                
                device_status = discovery_data['device_status']
                pa_credentials = discovery_data['pa_credentials']
                api_keys_list = discovery_data['api_keys_list']
                logger.info("Using discovery data for HA interface status")
                
            except FileNotFoundError:
                # Fallback to API keys data if no discovery data
                logger.warning("Discovery data not found, falling back to API keys data")
                with open('api_keys_data.pkl', 'rb') as f:
                    api_data = pickle.load(f)
                
                pa_credentials = api_data['pa_credentials']
                api_keys_list = api_data['api_keys_list']
                device_status = None
            
            # Get HA interfaces from Jenkins form parameters
            ha_interface_1 = os.getenv('HA1_INTERFACE')      # ← Changed from 'HA_INTERFACE_1'
            ha_interface_2 = os.getenv('HA2_INTERFACE')      # ← Changed from 'HA_INTERFACE_2'

            if not ha_interface_1 or not ha_interface_2:
                raise Exception("HA interfaces must be specified in Jenkins form parameters")

            interfaces = [ha_interface_1, ha_interface_2]
            logger.info(f"Using HA interfaces from Jenkins form: {interfaces}")
            
            changes_made = False
            
            # Configure HA interfaces on each device
            for device, headers in zip(pa_credentials, api_keys_list):
                host = device['host']
                device_changes = False
                
                try:
                    ha_interfaces_link_url = f"https://{device['host']}/api/"
                    
                    for interface in interfaces:
                        # Check status from discovery data if available
                        if device_status and host in device_status:
                            interface_configured = device_status[host]['ha_interfaces'].get(interface, False)
                            if interface_configured:
                                logger.info(f"Skipping {interface} on {host} - already configured for HA (from discovery)")
                                continue
                        else:
                            # Fallback to API check if no discovery data
                            if self._check_ha_interface_status(device, headers, interface):
                                logger.info(f"Skipping {interface} on {host} - already configured for HA")
                                continue
                        
                        # Configure interface for HA
                        logger.info(f"Configuring {interface} on {host} for HA")
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
                            logger.info(f"HA interface {interface} enabled on {host}")
                            logger.info(xml_response_control)
                            device_changes = True
                            changes_made = True
                        else:
                            logger.error(f"Failed to enable HA interface {interface} on {host}: {response_control.status_code}")
                            return False
                    
                    if device_changes:
                        logger.info(f"HA interfaces configuration completed for {host}")
                    else:
                        logger.info(f"No HA interface changes needed for {host}")
                        
                except Exception as e:
                    logger.error(f"Error in HA configuration for {host}: {e}")
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
                'ha_interfaces_used': interfaces,
                'changes_made': changes_made,
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list
            }
            
            with open('ha_interfaces_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info(f"HA interfaces enablement completed successfully using: {interfaces}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in HA interfaces enablement: {e}")
            return False
    
    def _check_ha_interface_status(self, device, headers, interface):
        """
        Fallback method to check if HA interface is already configured via API.
        Only used when discovery data is not available.
        
        Args:
            device: Device credentials
            headers: API headers with key
            interface: Interface name (e.g., 'ethernet1/6')
            
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