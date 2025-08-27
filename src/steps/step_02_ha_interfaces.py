"""
Step 2: Enable HA Interfaces for PA Firewalls

For fresh deployments - always applies HA interface configuration
without checking existing status.
"""

import requests
import logging
import pickle
import sys
import os

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step02_HAInterfaces:
    """
    Enable HA interfaces based on Jenkins form parameters.
    Fresh deployment - always applies configuration.
    """
    
    def __init__(self):
        pass
    
    def execute(self):
        """
        Enable HA interfaces on all devices.
        Fresh start - no status checks, always apply configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load API keys data (fresh deployment)
            with open('api_keys_data.pkl', 'rb') as f:
                api_data = pickle.load(f)
            
            pa_credentials = api_data['pa_credentials']
            api_keys_list = api_data['api_keys_list']
            logger.info("Fresh deployment - applying HA interface configuration")
            
            # Get HA interfaces from Jenkins form parameters
            ha_interface_1 = os.getenv('HA1_INTERFACE')
            ha_interface_2 = os.getenv('HA2_INTERFACE')
            
            if not ha_interface_1 or not ha_interface_2:
                raise Exception("HA interfaces must be specified in Jenkins form parameters")
            
            interfaces = [ha_interface_1, ha_interface_2]
            logger.info(f"Configuring HA interfaces: {interfaces}")
            
            # Configure HA interfaces on each device
            for device, headers in zip(pa_credentials, api_keys_list):
                host = device['host']
                logger.info(f"Configuring HA interfaces for {host}")
                
                try:
                    ha_api_url = f"https://{host}/api/"
                    
                    for interface in interfaces:
                        logger.info(f"Enabling HA on {interface} for {host}")
                        
                        params = {
                            'type': 'config',
                            'action': 'set',
                            'xpath': f"/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet/entry[@name='{interface}']",
                            'element': '<ha/>',
                            'override': 'yes',
                            'key': headers['X-PAN-KEY']
                        }
                        
                        response = requests.get(ha_api_url, params=params, verify=False, timeout=30)
                        
                        if response.status_code == 200:
                            logger.info(f"HA interface {interface} configured successfully on {host}")
                            logger.debug(f"Response: {response.text}")
                        else:
                            logger.error(f"Failed to configure HA interface {interface} on {host}: {response.status_code}")
                            logger.error(f"Response: {response.text}")
                            return False
                    
                    logger.info(f"All HA interfaces configured for {host}")
                        
                except Exception as e:
                    logger.error(f"Error configuring HA interfaces for {host}: {e}")
                    return False
            
            # Commit changes
            logger.info("Committing HA interface configuration")
            from utils_pa import commit_changes
            success = commit_changes(pa_credentials, api_keys_list, "HA Interfaces")
            if not success:
                return False
            
            # Save completion status for next steps
            step_data = {
                'ha_interfaces_enabled': True,
                'ha_interfaces_used': interfaces,
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list
            }
            
            with open('ha_interfaces_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info(f"HA interfaces configuration completed successfully: {interfaces}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in HA interfaces configuration: {e}")
            return False