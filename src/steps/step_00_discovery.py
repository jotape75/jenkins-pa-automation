"""
Step 0: Discovery - Gather Current Configuration Status

Collects current state of all devices before any configuration changes.
This avoids multiple API calls and provides a baseline for all subsequent steps.
"""

import requests
import logging
import pickle
import json
import xml.etree.ElementTree as ET
import sys
import os
import datetime

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step00_Discovery:
    """
    Discover current configuration state of all devices.
    Creates a baseline configuration status file.
    """
    
    def __init__(self):
        """
        Initialize discovery step.
        """
        pass
    
    def _check_ha_interfaces(self, device, headers):
        """Check HA interface configuration for a device."""
        interfaces_status = {}
        interfaces = ['ethernet1/4', 'ethernet1/5']
        
        for interface in interfaces:
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
                    ha_element = root.find(".//ha")
                    interfaces_status[interface] = ha_element is not None
                else:
                    interfaces_status[interface] = False
                    
            except Exception as e:
                logger.warning(f"Error checking interface {interface} on {device['host']}: {e}")
                interfaces_status[interface] = False
        
        return interfaces_status
    
    def _check_ha_config(self, device, headers):
        """Check HA configuration for a device - improved detection."""
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
                
                if ha_config is not None:
                    # Check for multiple indicators of HA configuration
                    enabled = ha_config.find(".//enabled")
                    group = ha_config.find(".//group")
                    interface = ha_config.find(".//interface")
                    
                    # More comprehensive check
                    has_enabled = enabled is not None and enabled.text == "yes"
                    has_group = group is not None and len(group) > 0
                    has_interface = interface is not None and len(interface) > 0
                    
                    if has_enabled or has_group or has_interface:
                        logger.info(f"HA config found on {device['host']}: enabled={has_enabled}, group={has_group}, interface={has_interface}")
                        return True
                
                logger.info(f"No HA configuration found on {device['host']}")
                return False
                
            return False
            
        except Exception as e:
            logger.warning(f"Error checking HA config on {device['host']}: {e}")
            return False

    def _check_interfaces_config(self, device, headers):
        """Check general interface configuration."""
        try:
            interfaces_status = {}
            
            # Check common interfaces (ethernet1/1, ethernet1/2, ethernet1/3)
            interfaces = ['ethernet1/1', 'ethernet1/2', 'ethernet1/3']
            
            for interface in interfaces:
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
                        
                        # Check if interface has Layer 3 configuration
                        layer3 = root.find(".//layer3")
                        has_ip = layer3 is not None and layer3.find(".//ip") is not None
                        has_zone = layer3 is not None and layer3.find(".//zone") is not None
                        
                        interfaces_status[interface] = {
                            'configured': layer3 is not None,
                            'has_ip': has_ip,
                            'has_zone': has_zone
                        }
                    else:
                        interfaces_status[interface] = {
                            'configured': False,
                            'has_ip': False,
                            'has_zone': False
                        }
                        
                except Exception as e:
                    logger.warning(f"Error checking interface {interface} on {device['host']}: {e}")
                    interfaces_status[interface] = {
                        'configured': False,
                        'has_ip': False,
                        'has_zone': False
                    }
            
            return interfaces_status
            
        except Exception as e:
            logger.warning(f"Error checking interfaces config on {device['host']}: {e}")
            return {}
    
    def _check_zones_config(self, device, headers):
        """Check zones configuration."""
        # Add zones checking logic
        return {}
    
    def _check_routing_config(self, device, headers):
        """Check routing configuration."""
        # Add routing checking logic
        return {}
    
    def _check_security_policies(self, device, headers):
        """Check security policies configuration."""
        # Add security policies checking logic
        return {}
    
    def _check_nat_rules(self, device, headers):
        """Check NAT rules configuration."""
        # Add NAT rules checking logic
        return {}
    
    def execute(self):
        """
        Discover current configuration state of all devices.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load API keys and credentials
            with open('api_keys_data.pkl', 'rb') as f:
                api_data = pickle.load(f)
            
            pa_credentials = api_data['pa_credentials']
            api_keys_list = api_data['api_keys_list']
            
            logger.info(f"Starting configuration discovery for {len(pa_credentials)} devices")
            
            device_status = {}
            
            # Discover configuration for each device
            for device, headers in zip(pa_credentials, api_keys_list):
                host = device['host']
                logger.info(f"Discovering configuration for {host}")
                
                device_status[host] = {
                    'ha_interfaces': self._check_ha_interfaces(device, headers),
                    'ha_config': self._check_ha_config(device, headers),
                    'interfaces': self._check_interfaces_config(device, headers),
                    'zones': self._check_zones_config(device, headers),
                    'routing': self._check_routing_config(device, headers),
                    'security_policies': self._check_security_policies(device, headers),
                    'nat_rules': self._check_nat_rules(device, headers),
                    'discovery_timestamp': str(datetime.datetime.now())
                }
                
                logger.info(f"Discovery completed for {host}")
                logger.info(f"  HA Interfaces: {device_status[host]['ha_interfaces']}")
                logger.info(f"  HA Config: {device_status[host]['ha_config']}")
            
            # Save discovery results
            discovery_data = {
                'device_status': device_status,
                'pa_credentials': pa_credentials,
                'api_keys_list': api_keys_list,
                'discovery_completed': True
            }
            
            with open('discovery_data.pkl', 'wb') as f:
                pickle.dump(discovery_data, f)
            
            logger.info("Configuration discovery completed successfully")
            logger.info("Discovery data saved to discovery_data.pkl")
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in configuration discovery: {e}")
            return False