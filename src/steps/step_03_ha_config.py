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
    
    Uses discovery data and follows original ha_configuration() method pattern.
    """
    
    def __init__(self):
        """
        Initialize HA configuration step.
        """
        pass
    
    def execute(self):
        """
        Configure HA settings on all devices.
        Uses discovery data and original 3-step HA configuration pattern.
        
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
            
            # Load HA configuration templates
            try:
                from utils_pa import PA_HA_CONFIG_TEMPLATE, PA_HA_INT_TEMPLATE
                with open(PA_HA_CONFIG_TEMPLATE, 'r') as f:
                    ha_config_template = f.read()
                with open(PA_HA_INT_TEMPLATE, 'r') as f:
                    ha_int_template = f.read()
                logger.info(f"Loaded HA config templates")
            except Exception as e:
                logger.error(f"Failed to load HA config templates: {e}")
                return False
            
            # HA configurations (matching your original code)
            ha_configs = [
                {'device_priority': '100', 'preemptive': 'yes', 'peer_ip': '1.1.1.2'}, # ha config for first device
                {'device_priority': '110', 'preemptive': 'no', 'peer_ip': '1.1.1.1'} # ha config for second device
            ]

            interface_configs = [
                {'ha1_ip': '1.1.1.1'}, # ha interface config for first device
                {'ha1_ip': '1.1.1.2'} # ha interface config for second device
            ]
            
            changes_made = False
            
            # Configure HA on each device (following original 3-step pattern)
            for i, (device, headers) in enumerate(zip(pa_credentials, api_keys_list)):
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
                    
                    logger.info(f"Configuring HA settings on {host}")
                    ha_url = f"https://{device['host']}/api/"
                    
                    # Step 1: Enable basic HA (exactly like original)
                    basic_ha_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': f"/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                        'element': '<enabled>yes</enabled>',
                        'key': headers['X-PAN-KEY']
                    }
                    response_basic = requests.get(ha_url, params=basic_ha_params, verify=False, timeout=30)
                    if response_basic.status_code == 200:
                        logger.info(f"Basic HA enabled on {host}")
                        logger.info(response_basic.text)
                    else:
                        logger.error(f"Failed to enable basic HA on {host}: {response_basic.status_code}")
                        continue
                        
                    # Step 2: Configure group (exactly like original)
                    ha_config = ha_configs[i]
                    group_xml = ha_config_template.format(
                        device_priority=ha_config['device_priority'],
                        preemptive=ha_config['preemptive'],
                        peer_ip=ha_config['peer_ip']
                    )
                    group_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': f"/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/group",
                        'element': group_xml,
                        'override': 'yes',
                        'key': headers['X-PAN-KEY']
                    }
                    response_group = requests.get(ha_url, params=group_params, verify=False, timeout=30)
                    if response_group.status_code == 200:
                        logger.info(f"HA group configured on {host}")
                        logger.info(response_group.text)
                    else:
                        logger.error(f"Failed to configure HA group on {host}: {response_group.status_code}")
                        continue
                        
                    # Step 3: Configure HA interfaces (exactly like original)
                    config = interface_configs[i]
                    interface_xml = ha_int_template.format(ha1_ip=config['ha1_ip'])                
                    interface_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': f"/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/interface",
                        'override': 'yes',
                        'element': interface_xml,
                        'key': headers['X-PAN-KEY']
                    }
                    response_int = requests.get(ha_url, params=interface_params, verify=False, timeout=30)
                    if response_int.status_code == 200:
                        logger.info(f"HA interfaces configured on {host}")
                        logger.info(response_int.text)
                        changes_made = True
                    else:
                        logger.error(f"Failed to configure HA interfaces on {host}: {response_int.status_code}")
                        continue
                        
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
                ha_config = root.find(".//high-availability")
                
                if ha_config is not None and len(ha_config) > 0:
                    enabled = ha_config.find(".//enabled")
                    group_id = ha_config.find(".//group-id")
                    
                    if enabled is not None or group_id is not None:
                        logger.info(f"HA configuration already exists on {device['host']}")
                        return True
                
                return False
            else:
                logger.warning(f"Could not check HA config status on {device['host']}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking HA configuration status on {device['host']}: {e}")
            return False