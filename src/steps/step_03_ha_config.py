"""
Step 3: Configure HA Settings for PA Firewalls

Extracts the HA configuration logic from PaloAltoFirewall_HA class
and adapts it for Jenkins execution with discovery-based checking.
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

class Step03_HAConfig:
    """
    Configure HA settings on all devices.
    
    Uses discovery data to check current status instead of making API calls.
    """
    
    def __init__(self):
        """
        Initialize HA configuration step.
        """
        pass
    
    def execute(self):
        """
        Configure HA settings on all devices.
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
                logger.info("Using discovery data for HA configuration status")
                
            except FileNotFoundError:
                # Fallback to previous step data if no discovery data
                logger.warning("Discovery data not found, falling back to previous step data")
                with open('ha_interfaces_data.pkl', 'rb') as f:
                    step_data = pickle.load(f)
                
                pa_credentials = step_data['pa_credentials']
                api_keys_list = step_data['api_keys_list']
                device_status = None
            
            logger.info(f"Configuring HA settings for {len(pa_credentials)} devices")
            
            # Load HA configuration template
            try:
                from utils_pa import PA_HA_CONFIG_TEMPLATE
                with open(PA_HA_CONFIG_TEMPLATE, 'r') as f:
                    ha_config_template = f.read()
                logger.info(f"Loaded HA config template from {PA_HA_CONFIG_TEMPLATE}")
            except Exception as e:
                logger.error(f"Failed to load HA config template: {e}")
                return False
            
            changes_made = False
            
            # Configure HA on each device
            for device, headers in zip(pa_credentials, api_keys_list):
                host = device['host']
                
                try:
                    # Check status from discovery data if available
                    if device_status and host in device_status:
                        ha_configured = device_status[host]['ha_config']
                        if ha_configured:
                            logger.info(f"Skipping HA configuration on {host} - already configured (from discovery)")
                            continue
                    else:
                        # Fallback to API check if no discovery data
                        if self._check_ha_config_status(device, headers):
                            logger.info(f"Skipping HA configuration on {host} - already configured")
                            continue
                    
                    # Apply HA configuration
                    logger.info(f"Configuring HA settings on {host}")
                    
                    ha_config_url = f"https://{device['host']}/api/"
                    ha_config_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                        'element': ha_config_template,
                        'key': headers['X-PAN-KEY']
                    }
                    
                    response = requests.get(ha_config_url, params=ha_config_params, verify=False, timeout=30)
                    
                    if response.status_code == 200:
                        xml_response = response.text
                        logger.info(f"HA configuration applied on {host}")
                        logger.info(xml_response)
                        changes_made = True
                    else:
                        logger.error(f"Failed to configure HA on {host}: {response.status_code}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error configuring HA on {host}: {e}")
                    return False
            
            # Only commit if changes were made
            if changes_made:
                logger.info("HA configuration changes made - proceeding with commit")
                from utils_pa import commit_changes
                success = commit_changes(pa_credentials, api_keys_list, "HA Configuration")
                if not success:
                    return False
            else:
                logger.info("No HA configuration changes needed - skipping commit")
            
            # Save completion status for next steps
            step_data = {
                'ha_config_applied': True,
                'changes_made': changes_made,
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list
            }
            
            with open('ha_config_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("HA configuration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in HA configuration: {e}")
            return False
    
    def _check_ha_config_status(self, device, headers):
        """
        Fallback method to check if HA configuration already exists via API.
        Only used when discovery data is not available.
        
        Args:
            device: Device credentials
            headers: API headers with key
            
        Returns:
            bool: True if HA is already configured, False otherwise
        """
        try:
            check_url = f"https://{device['host']}/api/"
            check_params = {
                'type': 'config',
                'action': 'get',
                'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                'key': headers['X-PAN-KEY']
            }
            
            response = requests.get(check_url, params=check_params, verify=False, timeout=30)
            
            if response.status_code == 200:
                xml_response = response.text
                root = ET.fromstring(xml_response)
                
                # Check if high-availability configuration exists and has content
                ha_config = root.find(".//high-availability")
                if ha_config is not None and len(ha_config) > 0:
                    # Check for key HA elements
                    enabled = ha_config.find(".//enabled")
                    group_id = ha_config.find(".//group-id")
                    
                    if enabled is not None or group_id is not None:
                        logger.info(f"HA configuration already exists on {device['host']}")
                        return True
                    else:
                        logger.info(f"HA configuration is empty on {device['host']}")
                        return False
                else:
                    logger.info(f"No HA configuration found on {device['host']}")
                    return False
            else:
                logger.warning(f"Could not check HA config status on {device['host']}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking HA configuration status on {device['host']}: {e}")
            return False