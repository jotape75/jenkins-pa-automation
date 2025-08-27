"""
Step 4: Identify Active Firewall in HA Pair

For fresh deployments - waits for HA to establish and identifies active firewall.
"""

import requests
import logging
import pickle
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
    Fresh deployment - waits for HA to establish before proceeding.
    """
    
    def __init__(self):
        pass
    
    def execute(self):
        """
        Identify active firewall from HA pair.
        Fresh deployment - includes wait time for HA establishment.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load data from previous step
            with open('ha_config_data.pkl', 'rb') as f:
                step_data = pickle.load(f)
            
            pa_credentials = step_data['pa_credentials']
            api_keys_list = step_data['api_keys_list']
            logger.info("Fresh deployment - waiting for HA to establish before identifying active firewall")
            
            # Wait for HA to establish (fresh deployment needs time)
            logger.info("Waiting 30 seconds for HA to establish...")
            time.sleep(30)
            
            active_fw_list = []
            active_fw_headers = []
            
            # Try to identify active firewall with retries
            max_attempts = 5
            for attempt in range(max_attempts):
                logger.info(f"Attempt {attempt + 1}/{max_attempts} to identify active firewall")
                
                active_fw_list = []
                active_fw_headers = []
                
                for device, headers in zip(pa_credentials, api_keys_list):
                    try:
                        host = device['host']
                        logger.info(f"Checking HA state on {host}")
                        
                        ha_state_url = f"https://{host}/api/"
                        ha_state_params = {
                            'type': 'op',
                            'cmd': '<show><high-availability><state></state></high-availability></show>',
                            'key': headers['X-PAN-KEY']
                        }
                        
                        response = requests.get(ha_state_url, params=ha_state_params, verify=False, timeout=30)
                        
                        if response.status_code == 200:
                            xml_response = response.text
                            logger.debug(f"HA state response from {host}: {xml_response}")
                            
                            root = ET.fromstring(xml_response)
                            ha_state_element = root.find(".//state")
                            
                            if ha_state_element is not None:
                                ha_state = ha_state_element.text.strip()
                                logger.info(f"HA state for {host}: {ha_state}")
                                
                                if ha_state.lower() == "active":
                                    active_fw_list.append(device)
                                    active_fw_headers.append(headers)
                                    logger.info(f"Found active firewall: {host}")
                                    break
                                elif ha_state.lower() in ["passive", "standby"]:
                                    logger.info(f"{host} is in {ha_state} state")
                                else:
                                    logger.warning(f"{host} has unexpected HA state: {ha_state}")
                            else:
                                logger.warning(f"No HA state found in response from {host}")
                        else:
                            logger.warning(f"Failed to get HA state from {host}: {response.status_code}")
                            logger.debug(f"Response: {response.text}")
                            
                    except Exception as e:
                        logger.warning(f"Error checking HA state on {host}: {e}")
                        continue
                
                # If we found an active firewall, we're done
                if active_fw_list:
                    logger.info(f"Active firewall identified: {active_fw_list[0]['host']}")
                    break
                
                # If no active firewall found and not the last attempt, wait and retry
                if attempt < max_attempts - 1:
                    wait_time = 15
                    logger.info(f"No active firewall found, waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
            
            # If still no active firewall, use first device as fallback
            if not active_fw_list:
                logger.warning("No active firewall found after all attempts")
                logger.info("Fresh deployment fallback: using first firewall as active")
                active_fw_list.append(pa_credentials[0])
                active_fw_headers.append(api_keys_list[0])
                logger.info(f"Fallback active firewall: {active_fw_list[0]['host']}")
            
            # Save active firewall info for next steps
            step_data = {
                'active_fw_list': active_fw_list,
                'active_fw_headers': active_fw_headers,
                'active_fw_device': active_fw_list[0],
                'active_fw_key': active_fw_headers[0]['X-PAN-KEY'],
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list,
                'identification_completed': True,
                'is_fresh_deployment': True
            }
            
            with open('active_fw_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info(f"Active firewall identification completed: {active_fw_list[0]['host']}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in active firewall identification: {e}")
            return False