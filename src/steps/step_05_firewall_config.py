"""
Step 5: Complete Firewall Configuration on Active Device

For fresh deployments - always applies all configuration without checking existing status.
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

class Step05_FirewallConfig:
    """
    Complete firewall configuration on active device.
    Fresh deployment - always applies all configuration.
    """
    
    def __init__(self):
        pass
    
    def execute(self):
        """
        Execute complete firewall configuration.
        Fresh start - no status checks, always apply all configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load active firewall data from previous step
            with open('active_fw_data.pkl', 'rb') as f:
                active_fw_data = pickle.load(f)
            
            active_fw_list = active_fw_data['active_fw_list']
            active_fw_headers = active_fw_data['active_fw_headers']
            logger.info("Fresh deployment - applying complete firewall configuration")
            
            active_host = active_fw_list[0]['host']
            active_key = active_fw_headers[0]['X-PAN-KEY']
            logger.info(f"Configuring firewall: {active_host} (fresh configuration)")
            
            # Execute all configuration steps in sequence
            config_results = {}
            
            # Step 5.1: Interface Configuration
            logger.info("=== STEP 5.1: Interface Configuration ===")
            if not self._configure_interfaces(active_host, active_key, config_results):
                return False
                
            # Step 5.2: Zone Configuration
            logger.info("=== STEP 5.2: Zone Configuration ===")
            if not self._configure_zones(active_host, active_key, config_results):
                return False
                
            # Step 5.3: Routing Configuration
            logger.info("=== STEP 5.3: Routing Configuration ===")
            if not self._configure_routing(active_host, active_key, config_results):
                return False
                
            # Step 5.4: Security Policy Configuration
            logger.info("=== STEP 5.4: Security Policy Configuration ===")
            if not self._configure_security_policies(active_host, active_key, config_results):
                return False
                
            # Step 5.5: Source NAT Configuration
            logger.info("=== STEP 5.5: Source NAT Configuration ===")
            if not self._configure_source_nat(active_host, active_key, config_results):
                return False
            
            # Save completion status for next steps
            step_data = {
                'firewall_configured': True,
                'config_results': config_results,
                'active_fw_list': active_fw_list,
                'active_fw_headers': active_fw_headers,
                'firewall_configuration_completed': True,
                'configured_host': active_host
            }
            
            with open('firewall_config_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("=== FIREWALL CONFIGURATION COMPLETED ===")
            logger.info(f"Configuration summary: {config_results}")
            logger.info(f"Configured firewall: {active_host}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in firewall configuration: {e}")
            return False
    
    def _configure_interfaces(self, host, api_key, results):
        """Configure interfaces - fresh deployment, always apply"""
        try:
            logger.info("Configuring interfaces (fresh deployment)...")
            
            # Load interface template
            from utils_pa import PA_INTERFACE_TEMPLATE
            with open(PA_INTERFACE_TEMPLATE, 'r') as f:
                pa_interface_tmp = f.read()
            
            logger.info(f"Loaded interface template: {len(pa_interface_tmp)} characters")
            
            interface_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet"
            config_url = f"https://{host}/api/"
            interface_params = {
                'type': 'config',
                'action': 'set',
                'xpath': interface_xpath,
                'element': pa_interface_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=interface_params, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.info("Interfaces configured successfully")
                logger.debug(f"Response: {response.text}")
                results['interfaces'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure interfaces: {response.status_code}")
                logger.error(f"Response: {response.text}")
                results['interfaces'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring interfaces: {e}")
            results['interfaces'] = 'error'
            return False
    
    def _configure_zones(self, host, api_key, results):
        """Configure zones - fresh deployment, always apply"""
        try:
            logger.info("Configuring zones (fresh deployment)...")
            
            # Load zones template
            from utils_pa import PA_ZONES_TEMPLATE
            with open(PA_ZONES_TEMPLATE, 'r') as f:
                pa_zones_tmp = f.read()
            
            logger.info(f"Loaded zones template: {len(pa_zones_tmp)} characters")
            
            zones_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/zone"
            config_url = f"https://{host}/api/"
            zones_params = {
                'type': 'config',
                'action': 'set',
                'xpath': zones_xpath,
                'element': pa_zones_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=zones_params, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.info("Zones configured successfully")
                logger.debug(f"Response: {response.text}")
                results['zones'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure zones: {response.status_code}")
                logger.error(f"Response: {response.text}")
                results['zones'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring zones: {e}")
            results['zones'] = 'error'
            return False
    
    def _configure_routing(self, host, api_key, results):
        """Configure routing - fresh deployment, always apply"""
        try:
            logger.info("Configuring routing (fresh deployment)...")
            
            # Load routing templates
            from utils_pa import PA_ROUTER_TEMPLATE, PA_ROUTES_TEMPLATE
            with open(PA_ROUTER_TEMPLATE, 'r') as f:
                pa_route_settings_tmp = f.read()
            with open(PA_ROUTES_TEMPLATE, 'r') as f:
                pa_static_routes_tmp = f.read()
            
            logger.info(f"Loaded router template: {len(pa_route_settings_tmp)} characters")
            logger.info(f"Loaded routes template: {len(pa_static_routes_tmp)} characters")
            
            config_url = f"https://{host}/api/"
            
            # Configure route settings
            route_settings_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/virtual-router"
            route_settings_params = {
                'type': 'config',
                'action': 'set',
                'xpath': route_settings_xpath,
                'element': pa_route_settings_tmp,
                'key': api_key
            }

            response_settings = requests.get(config_url, params=route_settings_params, verify=False, timeout=30)
            
            if response_settings.status_code != 200:
                logger.error(f"Failed to configure route settings: {response_settings.status_code}")
                logger.error(f"Response: {response_settings.text}")
                results['routing'] = 'failed'
                return False
            
            logger.info("Virtual router configured successfully")
            
            # Configure static routes
            static_routes_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry[@name='default']/routing-table/ip/static-route"
            static_routes_params = {
                'type': 'config',
                'action': 'set',
                'xpath': static_routes_xpath,
                'element': pa_static_routes_tmp,
                'key': api_key
            }

            response_routes = requests.get(config_url, params=static_routes_params, verify=False, timeout=30)
            
            if response_routes.status_code == 200:
                logger.info("Static routes configured successfully")
                logger.debug(f"Response: {response_routes.text}")
                results['routing'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure static routes: {response_routes.status_code}")
                logger.error(f"Response: {response_routes.text}")
                results['routing'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring routing: {e}")
            results['routing'] = 'error'
            return False
    
    def _configure_security_policies(self, host, api_key, results):
        """Configure security policies - fresh deployment, always apply"""
        try:
            logger.info("Configuring security policies (fresh deployment)...")
            
            # Load security policy template
            from utils_pa import PA_SECURITY_TEMPLATE
            with open(PA_SECURITY_TEMPLATE, 'r') as f:
                pa_security_policy_tmp = f.read()
            
            logger.info(f"Loaded security template: {len(pa_security_policy_tmp)} characters")
            
            security_policy_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/security/rules"
            config_url = f"https://{host}/api/"
            security_policy_params = {
                'type': 'config',
                'action': 'set',
                'xpath': security_policy_xpath,
                'element': pa_security_policy_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=security_policy_params, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.info("Security policies configured successfully")
                logger.debug(f"Response: {response.text}")
                results['security_policies'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure security policies: {response.status_code}")
                logger.error(f"Response: {response.text}")
                results['security_policies'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring security policies: {e}")
            results['security_policies'] = 'error'
            return False
    
    def _configure_source_nat(self, host, api_key, results):
        """Configure source NAT - fresh deployment, always apply"""
        try:
            logger.info("Configuring source NAT (fresh deployment)...")
            
            # Load source NAT template
            from utils_pa import PA_NAT_TEMPLATE
            with open(PA_NAT_TEMPLATE, 'r') as f:
                pa_source_nat_tmp = f.read()
            
            logger.info(f"Loaded NAT template: {len(pa_source_nat_tmp)} characters")
            
            source_nat_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
            config_url = f"https://{host}/api/"
            source_nat_params = {
                'type': 'config',
                'action': 'set',
                'xpath': source_nat_xpath,
                'element': pa_source_nat_tmp,
                'key': api_key
            }

            response = requests.get(config_url, params=source_nat_params, verify=False, timeout=30)
            
            if response.status_code == 200:
                logger.info("Source NAT configured successfully")
                logger.debug(f"Response: {response.text}")
                results['source_nat'] = 'success'
                return True
            else:
                logger.error(f"Failed to configure source NAT: {response.status_code}")
                logger.error(f"Response: {response.text}")
                results['source_nat'] = 'failed'
                return False
                
        except Exception as e:
            logger.error(f"Error configuring source NAT: {e}")
            results['source_nat'] = 'error'
            return False