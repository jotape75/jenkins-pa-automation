"""
Step 4: Identify Active Firewall in HA Pair

Extracts the get_active_fw logic from PaloAltoFirewall_config class
and adapts it for Jenkins execution.
"""

import requests
import logging
import pickle
import json
import xml.etree.ElementTree as ET
import sys
import os
import time

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step04_IdentifyActive:
    """
    Identify active firewall from HA pair.
    
    Queries HA status on all devices to find the active firewall
    for configuration deployment.
    """
    
    def __init__(self):
        """
        Initialize active firewall identification step.
        """
        self.active_fw_list = []
        self.active_fw_headers = []
    
    def execute(self):
        """
        Identify active firewall from HA pair.        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load discovery data or previous step data
            try:
                with open('discovery_data.pkl', 'rb') as f:
                    discovery_data = pickle.load(f)
                
                pa_credentials = discovery_data['pa_credentials']
                api_keys_list = discovery_data['api_keys_list']
                logger.info("Using discovery data for active firewall identification")
                
            except FileNotFoundError:
                # Fallback to previous step data if no discovery data
                logger.warning("Discovery data not found, falling back to previous step data")
                with open('ha_config_data.pkl', 'rb') as f:
                    step_data = pickle.load(f)
                
                pa_credentials = step_data['pa_credentials']
                api_keys_list = step_data['api_keys_list']
            
            logger.info(f"Identifying active firewall from {len(pa_credentials)} devices")
            
            # Add retry logic for HA state stability
            for attempt in range(3):
                logger.info(f"Attempt {attempt + 1} to identify active firewall")
                
                try:
                    self.active_fw_list = []
                    self.active_fw_headers = []
                    
                    for device, headers in zip(pa_credentials, api_keys_list):
                        ha_state_link = f"https://{device['host']}/api/"
                        ha_state_api = f"{ha_state_link}?type=op&cmd=<show><high-availability><state></state></high-availability></show>"
                        response_ha_state = requests.get(ha_state_api, headers=headers, verify=False)
                        if response_ha_state.status_code == 200:
                            xml_response_state = response_ha_state.text
                            root = ET.fromstring(xml_response_state)
                            ha_state_element = root.find(".//state")
                            
                            if ha_state_element is not None:
                                ha_state = ha_state_element.text
                                logger.info(f"HA state for {device['host']}: {ha_state}")
                                
                                if ha_state == "active":
                                    self.active_fw_list.append(device)
                                    self.active_fw_headers.append(headers)
                                    break
                            else:
                                logger.warning(f"No HA state element found in response from {device['host']}")
                        else:
                            logger.error(f"Failed to get HA state for {device['host']}: {response_ha_state.status_code}")
                            
                    logger.info(f"Active firewall: {self.active_fw_list}")
                    
                    # If we found an active firewall, break out of retry loop
                    if self.active_fw_list:
                        break
                    
                    # If this is not the last attempt, wait before retrying
                    if attempt < 2:
                        logger.info(f"No active firewall found, waiting 5 seconds before retry...")
                        time.sleep(5)
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"RequestException: {e}")
                    if attempt < 2:
                        logger.info(f"Request failed, waiting 5 seconds before retry...")
                        time.sleep(5)
                    else:
                        return False
            
            # Validate that we found an active firewall
            if not self.active_fw_list:
                logger.error("No active firewall found in HA pair after 3 attempts")
                return False
            
            # Save active firewall info for next steps
            step_data = {
                'active_fw_list': self.active_fw_list,
                'active_fw_headers': self.active_fw_headers,
                'active_fw_device': self.active_fw_list[0],
                'active_fw_key': self.active_fw_headers[0]['X-PAN-KEY'],
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list,
                'identification_completed': True
            }
            
            with open('active_fw_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("Active firewall identification completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in active firewall identification: {e}")
            return False