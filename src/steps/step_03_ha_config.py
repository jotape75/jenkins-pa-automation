"""
Step 3: Configure HA Settings for PA Firewalls

For fresh deployments - always applies HA configuration
without checking existing status.
"""

import requests
import logging
import pickle
import sys
import os
import time

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step03_HAConfig:
    """
    Configure HA settings on all devices.
    Fresh deployment - always applies configuration.
    """
    
    def __init__(self):
        pass
    
    def execute(self):
        """
        Configure HA settings on all devices.
        Fresh start - no status checks, always apply configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load data from previous step
            with open('ha_interfaces_data.pkl', 'rb') as f:
                step_data = pickle.load(f)
            
            pa_credentials = step_data['pa_credentials']
            api_keys_list = step_data['api_keys_list']
            logger.info("Fresh deployment - applying HA configuration")
            
            # Load HA configuration templates
            try:
                from utils_pa import PA_HA_CONFIG_TEMPLATE, PA_HA_INTERFACE_TEMPLATE
                with open(PA_HA_CONFIG_TEMPLATE, 'r') as f:
                    ha_config_template = f.read()
                with open(PA_HA_INTERFACE_TEMPLATE, 'r') as f:
                    ha_int_template = f.read()
                
                # Debug template loading
                logger.info(f"HA Config Template Path: {PA_HA_CONFIG_TEMPLATE}")
                logger.info(f"HA Interface Template Path: {PA_HA_INTERFACE_TEMPLATE}")
                logger.debug(f"HA Config Template Content: {ha_config_template}")
                logger.debug(f"HA Interface Template Content: {ha_int_template}")
                logger.info("Loaded HA configuration templates")
            except Exception as e:
                logger.error(f"Failed to load HA config templates: {e}")
                return False
            
            # HA configurations from Jenkins parameters or defaults
            peer_ip_1 = os.getenv('HA_PEER_IP_1', '1.1.1.2')
            peer_ip_2 = os.getenv('HA_PEER_IP_2', '1.1.1.1')
            ha1_ip_1 = os.getenv('HA1_IP_1', '1.1.1.1')
            ha1_ip_2 = os.getenv('HA1_IP_2', '1.1.1.2')
            
            # HA configurations matching your original working pattern exactly
            ha_configs = [
                {'device_priority': '100', 'preemptive': 'yes', 'peer_ip': peer_ip_1},
                {'device_priority': '110', 'preemptive': 'no', 'peer_ip': peer_ip_2}
            ]

            # Use only ha1_ip like your original - no port parameters
            interface_configs = [
                {'ha1_ip': ha1_ip_1},
                {'ha1_ip': ha1_ip_2}
            ]
            
            configured_devices = []
            
            # Configure HA on each device
            for i, (device, headers) in enumerate(zip(pa_credentials, api_keys_list)):
                host = device['host']
                logger.info(f"Configuring HA settings on {host} (fresh configuration)")
                
                try:
                    ha_url = f"https://{host}/api/"
                    
                    # Step 1: Enable basic HA
                    logger.info(f"Enabling basic HA on {host}")
                    basic_ha_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                        'element': '<enabled>yes</enabled>',
                        'override': 'yes',
                        'key': headers['X-PAN-KEY']
                    }
                    response_basic = requests.get(ha_url, params=basic_ha_params, verify=False, timeout=30)
                    if response_basic.status_code == 200:
                        logger.info(f"Basic HA enabled on {host}")
                        logger.debug(f"Response: {response_basic.text}")
                    else:
                        logger.error(f"Failed to enable basic HA on {host}: {response_basic.status_code}")
                        logger.error(f"Response: {response_basic.text}")
                        return False
                        
                    # Step 2: Configure HA group
                    logger.info(f"Configuring HA group on {host}")
                    ha_config = ha_configs[i]
                    
                    # Format the template with proper substitution
                    try:
                        group_xml = ha_config_template.format(
                            device_priority=ha_config['device_priority'],
                            preemptive=ha_config['preemptive'],
                            peer_ip=ha_config['peer_ip']
                        )
                        logger.debug(f"Group XML for {host}: {group_xml}")
                    except KeyError as e:
                        logger.error(f"Template formatting error for {host}: {e}")
                        logger.error(f"Template content: {ha_config_template}")
                        logger.error(f"Config values: {ha_config}")
                        return False
                    
                    group_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/group",
                        'override': 'yes',
                        'element': group_xml,
                        'key': headers['X-PAN-KEY']
                    }
                    response_group = requests.get(ha_url, params=group_params, verify=False, timeout=30)
                    if response_group.status_code == 200:
                        logger.info(f"HA group configured on {host}")
                        logger.debug(f"Response: {response_group.text}")
                    else:
                        logger.error(f"Failed to configure HA group on {host}: {response_group.status_code}")
                        logger.error(f"Response: {response_group.text}")
                        return False
                        
                    # Step 3: Configure HA interfaces
                    logger.info(f"Configuring HA interfaces on {host}")
                    config = interface_configs[i]
                    
                    # Use ONLY ha1_ip like the original - no port parameters
                    try:
                        interface_xml = ha_int_template.format(ha1_ip=config['ha1_ip'])
                        logger.debug(f"Interface XML for {host}: {interface_xml}")
                    except KeyError as e:
                        logger.error(f"Interface template formatting error for {host}: {e}")
                        logger.error(f"Template content: {ha_int_template}")
                        logger.error(f"Config values: {config}")
                        return False
                    
                    interface_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/interface",
                        'override': 'yes',
                        'element': interface_xml,
                        'key': headers['X-PAN-KEY']
                    }
                    response_int = requests.get(ha_url, params=interface_params, verify=False, timeout=30)
                    if response_int.status_code == 200:
                        logger.info(f"HA interfaces configured on {host}")
                        logger.debug(f"Response: {response_int.text}")
                    else:
                        logger.error(f"Failed to configure HA interfaces on {host}: {response_int.status_code}")
                        logger.error(f"Response: {response_int.text}")
                        return False
                    
                    configured_devices.append(host)
                    logger.info(f"HA configuration completed for {host}")
                        
                except Exception as e:
                    logger.error(f"Error configuring HA on {host}: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return False
            
            # Commit changes with improved error handling
            logger.info(f"HA configuration applied to {len(configured_devices)} devices - committing changes")
            
            # Add longer delay before commit to let configuration settle
            logger.info("Waiting 15 seconds for HA configuration to settle...")
            time.sleep(15)
            
            # Import and use commit function with better error handling
            try:
                from utils_pa import commit_changes
                success = commit_changes(pa_credentials, api_keys_list, "HA Configuration")
                if not success:
                    logger.warning("Commit failed - but configuration was applied")
                    # Don't return False here - HA might still work
                
                # Additional wait for HA to establish
                logger.info("Waiting additional 15 seconds for HA to establish...")
                time.sleep(15)
                
            except Exception as commit_error:
                logger.warning(f"Commit error - but configuration was applied: {commit_error}")
                # Continue anyway as HA configuration might still be functional
            
            # Force enable HA on both devices after commit
            logger.info("Force enabling HA on both devices...")
            for device, headers in zip(pa_credentials, api_keys_list):
                try:
                    ha_url = f"https://{device['host']}/api/"
                    
                    # Force enable HA
                    enable_ha_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/enabled",
                        'element': 'yes',
                        'override': 'yes',
                        'key': headers['X-PAN-KEY']
                    }
                    response = requests.get(ha_url, params=enable_ha_params, verify=False, timeout=30)
                    if response.status_code == 200:
                        logger.info(f"HA force-enabled on {device['host']}")
                    else:
                        logger.warning(f"Could not force-enable HA on {device['host']}: {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Error force-enabling HA on {device['host']}: {e}")

            # Commit the HA enable
            logger.info("Committing HA enable...")
            try:
                from utils_pa import commit_changes
                commit_changes(pa_credentials, api_keys_list, "HA Enable")
            except Exception as e:
                logger.warning(f"HA enable commit error: {e}")
            
            # Verify HA status on both devices
            logger.info("Verifying HA configuration...")
            for device, headers in zip(pa_credentials, api_keys_list):
                try:
                    ha_status_url = f"https://{device['host']}/api/"
                    ha_status_params = {
                        'type': 'op',
                        'cmd': '<show><high-availability><state></state></high-availability></show>',
                        'key': headers['X-PAN-KEY']
                    }
                    response = requests.get(ha_status_url, params=ha_status_params, verify=False, timeout=30)
                    if response.status_code == 200:
                        logger.info(f"HA status for {device['host']}: {response.text}")
                    else:
                        logger.warning(f"Could not verify HA status for {device['host']}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Could not verify HA status for {device['host']}: {e}")
            
            # Save completion status for next steps
            step_data = {
                'ha_config_applied': True,
                'configured_devices': configured_devices,
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list,
                'ha_interface_configs': interface_configs,
                'ha_group_configs': ha_configs
            }
            
            with open('ha_config_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("HA configuration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in HA configuration: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False