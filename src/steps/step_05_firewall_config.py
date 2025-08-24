"""
Step 5: Complete Firewall Configuration on Active Device

Combines interface, zone, routing, security policy, and NAT configuration
into a single comprehensive step for cleaner Jenkins pipeline view.
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

class Step05_FirewallConfig:
    """
    Complete firewall configuration on active device.
    
    Performs all configuration steps in sequence:
    - Interface configuration
    - Zone configuration  
    - Routing configuration
    - Security policy configuration
    - Source NAT configuration
    """
    
    def __init__(self):
        """
        Initialize firewall configuration step.
        """
        pass
    
    def execute(self):
        """
        Execute complete firewall configuration.
        
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
                logger.info("Using active firewall data for complete configuration")
                
            except FileNotFoundError:
                logger.error("Active firewall data not found. Run identify_active step first.")
                return False
            
            active_host = active_fw_list[0]['host']
            active_key = active_fw_headers[0]['X-PAN-KEY']
            logger.info(f"Configuring firewall: {active_host}")
            
            # Execute all configuration steps in sequence
            config_results = {}
            
            # Step 5.1: Interface Configuration
            if not self._configure_interfaces(active_host, active_key, config_results):
                return False
                
            # Step 5.2: Zone Configuration
            if not self._configure_zones(active_host, active_key, config_results):
                return False
                
            # Step 5.3: Routing Configuration
            if not self._configure_routing(active_host, active_key, config_results):
                return False
                
            # Step 5.4: Security Policy Configuration
            if not self._configure_security_policies(active_host, active_key, config_results):
                return False
                
            # Step 5.5: Source NAT Configuration
            if not self._configure_source_nat(active_host, active_key, config_results):
                return False
            
            # Save completion status for next steps
            step_data = {
                'firewall_configured': True,
                'config_results': config_results,
                'active_fw_list': active_fw_list,
                'active_fw_headers': active_fw_headers,
                'firewall_configuration_completed': True
            }
            
            with open('firewall_config_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("Complete firewall configuration completed successfully")
            logger.info(f"Configuration summary: {config_results}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in firewall configuration: {e}")
            return False
    
    def _configure_interfaces(self, host, api_key, results):
        """Configure interfaces - exact logic from act_fw_int_config()"""
        try:
            logger.info("Configuring interfaces...")
            
            # Load interface template
            from utils_pa import PA_INTERFACE_TEMPLATE
            with open(PA_INTERFACE_TEMPLATE, 'r') as f:
                pa_interface_tmp = f.read()
            
            interface_xpath = f"/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet"
            config_url = f"https://{host}/api/"
            interface_params = {
                'type': 'config',
                'action': 'set',
                'xpath': interface_xpath,
                'element': pa_interface_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=interface_params, verify=False)
            
            if response.status_code == 200:
                logger.info(f"Interfaces configured successfully")
                results['interfaces'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure interfaces: {response.status_code}")
                results['interfaces'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring interfaces: {e}")
            results['interfaces'] = 'error'
            return False
    
    def _configure_zones(self, host, api_key, results):
        """Configure zones - exact logic from act_fw_zone_config()"""
        try:
            logger.info("Configuring zones...")
            
            # Load zones template
            from utils_pa import PA_ZONES_TEMPLATE
            with open(PA_ZONES_TEMPLATE, 'r') as f:
                pa_zones_tmp = f.read()
            
            zones_xpath = f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/zone"
            config_url = f"https://{host}/api/"
            zones_params = {
                'type': 'config',
                'action': 'set',
                'xpath': zones_xpath,
                'element': pa_zones_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=zones_params, verify=False)
            
            if response.status_code == 200:
                logger.info(f"Zones configured successfully")
                results['zones'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure zones: {response.status_code}")
                results['zones'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring zones: {e}")
            results['zones'] = 'error'
            return False
    
    def _configure_routing(self, host, api_key, results):
        """Configure routing - exact logic from act_fw_route_config()"""
        try:
            logger.info("Configuring routing...")
            
            # Load routing templates
            from utils_pa import PA_ROUTE_SETTINGS_TEMPLATE, PA_STATIC_ROUTES_TEMPLATE
            with open(PA_ROUTE_SETTINGS_TEMPLATE, 'r') as f:
                pa_route_settings_tmp = f.read()
            with open(PA_STATIC_ROUTES_TEMPLATE, 'r') as f:
                pa_static_routes_tmp = f.read()
            
            config_url = f"https://{host}/api/"
            
            # Configure route settings
            route_settings_xpath = f"/config/devices/entry[@name='localhost.localdomain']/network/virtual-router"
            route_settings_params = {
                'type': 'config',
                'action': 'set',
                'xpath': route_settings_xpath,
                'element': pa_route_settings_tmp,
                'key': api_key
            }

            response_settings = requests.get(config_url, params=route_settings_params, verify=False)
            
            if response_settings.status_code != 200:
                logger.error(f"Failed to configure route settings: {response_settings.status_code}")
                results['routing'] = 'failed'
                return False
            
            # Configure static routes
            static_routes_xpath = f"/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry[@name='default']/routing-table/ip/static-route"
            static_routes_params = {
                'type': 'config',
                'action': 'set',
                'xpath': static_routes_xpath,
                'element': pa_static_routes_tmp,
                'key': api_key
            }

            response_routes = requests.get(config_url, params=static_routes_params, verify=False)
            
            if response_routes.status_code == 200:
                logger.info(f"Routing configured successfully")
                results['routing'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure static routes: {response_routes.status_code}")
                results['routing'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring routing: {e}")
            results['routing'] = 'error'
            return False
    
    def _configure_security_policies(self, host, api_key, results):
        """Configure security policies - exact logic from act_fw_security_policy_config()"""
        try:
            logger.info("Configuring security policies...")
            
            # Load security policy template
            from utils_pa import PA_SECURITY_POLICY_TEMPLATE
            with open(PA_SECURITY_POLICY_TEMPLATE, 'r') as f:
                pa_security_policy_tmp = f.read()
            
            security_policy_xpath = f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/security/rules"
            config_url = f"https://{host}/api/"
            security_policy_params = {
                'type': 'config',
                'action': 'set',
                'xpath': security_policy_xpath,
                'element': pa_security_policy_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=security_policy_params, verify=False)
            
            if response.status_code == 200:
                logger.info(f"Security policies configured successfully")
                results['security_policies'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure security policies: {response.status_code}")
                results['security_policies'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring security policies: {e}")
            results['security_policies'] = 'error'
            return False
    
    def _configure_source_nat(self, host, api_key, results):
        """Configure source NAT - exact logic from act_fw_source_nat_config()"""
        try:
            logger.info("Configuring source NAT...")
            
            # Load source NAT template
            from utils_pa import PA_SOURCE_NAT_TEMPLATE
            with open(PA_SOURCE_NAT_TEMPLATE, 'r') as f:
                pa_source_nat_tmp = f.read()
            
            source_nat_xpath = f"/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
            config_url = f"https://{host}/api/"
            source_nat_params = {
                'type': 'config',
                'action': 'set',
                'xpath': source_nat_xpath,
                'element': pa_source_nat_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=source_nat_params, verify=False)
            
            if response.status_code == 200:
                logger.info(f"Source NAT configured successfully")
                results['source_nat'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure source NAT: {response.status_code}")
                results['source_nat'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring source NAT: {e}")
            results['source_nat'] = 'error'
            return False