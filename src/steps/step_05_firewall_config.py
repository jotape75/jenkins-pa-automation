"""
Step 5: Complete Firewall Configuration

Configure interfaces, zones, routing, security policies, and NAT
on the active firewall only.
"""

import requests
import logging
import pickle
import sys
import os

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils_pa import (PA_INTERFACE_TEMPLATE, PA_ZONES_TEMPLATE, PA_ROUTER_TEMPLATE, 
                     PA_ROUTES_TEMPLATE, PA_SECURITY_TEMPLATE, PA_NAT_TEMPLATE)

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step05_FirewallConfig:
    """
    Complete firewall configuration on active device only.
    Fresh deployment - always applies configuration.
    """
    
    def __init__(self):
        pass
    
    def execute(self):
        """
        Apply complete firewall configuration to active device.
        Fresh deployment - no status checks, always apply configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load data from previous step
            with open('active_fw_data.pkl', 'rb') as f:
                step_data = pickle.load(f)
            
            self.active_fw_list = step_data['active_fw_list']
            self.active_fw_headers = step_data['active_fw_headers']
            
            # Load templates like the original
            self.load_templates()
            
            logger.info("Fresh deployment - applying complete firewall configuration")
            logger.info(f"Configuring firewall: {self.active_fw_list[0]['host']} (fresh configuration)")
            
            # Execute configuration steps in original order
            logger.info("=== STEP 5.1: Interface Configuration ===")
            self.act_fw_int_config()
            
            logger.info("=== STEP 5.2: Zone Configuration ===")
            self.act_fw_zone_config()
            
            logger.info("=== STEP 5.3: Routing Configuration ===")
            self.act_fw_route_config()
            
            logger.info("=== STEP 5.4: Security Policy Configuration ===")
            self.act_fw_security_policy_config()
            
            logger.info("=== STEP 5.5: Source NAT Configuration ===")
            self.act_fw_source_nat_config()
            
            # Save data for next step (commit)
            step_data = {
                'firewall_config_applied': True,
                'active_fw_list': self.active_fw_list,
                'active_fw_headers': self.active_fw_headers,
                'config_summary': {
                    'interfaces': 'success',
                    'zones': 'success', 
                    'routing': 'success',
                    'security_policies': 'success',
                    'source_nat': 'success'
                }
            }
            
            with open('firewall_config_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("=== FIREWALL CONFIGURATION COMPLETED ===")
            logger.info(f"Configured firewall: {self.active_fw_list[0]['host']}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in firewall configuration: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def load_templates(self):
        """Load all configuration templates with environment variables"""
        try:
            # Load interface template and format it
            with open(PA_INTERFACE_TEMPLATE, 'r') as f:
                interface_tmp = f.read()
            
            # Format interface template with environment variables
            ethernet1_1_ip = os.getenv('ETHERNET1_1_IP_TRUST', '10.10.10.5/24')
            ethernet1_2_ip = os.getenv('ETHERNET1_2_IP_UNTRUST', '200.200.200.2/24')
            ethernet1_3_ip = os.getenv('ETHERNET1_3_IP_DMZ', '10.30.30.5/24')
            
            self.pa_interface_tmp = interface_tmp.format(
                ETHERNET1_1_IP_TRUST=ethernet1_1_ip,
                ETHERNET1_2_IP_UNTRUST=ethernet1_2_ip,
                ETHERNET1_3_IP_DMZ=ethernet1_3_ip
            )
            
            # Load zones template and format it
            with open(PA_ZONES_TEMPLATE, 'r') as f:
                zones_tmp = f.read()
                
            trust_interface = os.getenv('TRUST', 'ethernet1/1')
            untrust_interface = os.getenv('UNTRUST', 'ethernet1/2')
            dmz_interface = os.getenv('DMZ', 'ethernet1/3')
            
            self.pa_zones_tmp = zones_tmp.format(
                TRUST=trust_interface,
                UNTRUST=untrust_interface,
                DMZ=dmz_interface
            )
            
            # Load router settings template and format it
            with open(PA_ROUTER_TEMPLATE, 'r') as f:
                router_tmp = f.read()
                
            self.pa_route_settings_tmp = router_tmp.format(
                trust_interface=trust_interface,
                untrust_interface=untrust_interface,
                dmz_interface=dmz_interface
            )
            
            # Load static routes template and format it
            with open(PA_ROUTES_TEMPLATE, 'r') as f:
                routes_tmp = f.read()
                
            default_gateway = os.getenv('DEFAULT_GATEWAY', '200.200.200.1')
            static_route_network = os.getenv('STATIC_ROUTE_NETWORK', '10.0.0.0/8')
            static_route_nexthop = os.getenv('STATIC_ROUTE_NEXTHOP', '10.10.10.1')
            
            self.pa_static_routes_tmp = routes_tmp.format(
                STATIC_ROUTE_NETWORK=static_route_network,
                STATIC_ROUTE_NEXTHOP=static_route_nexthop,
                untrust=untrust_interface
            )
            
            # Load security template (no formatting needed)
            with open(PA_SECURITY_TEMPLATE, 'r') as f:
                self.pa_security_policy_tmp = f.read()
            
            # Load NAT template (will be formatted in the method)
            with open(PA_NAT_TEMPLATE, 'r') as f:
                self.pa_source_nat_tmp = f.read()
                
            logger.info("All configuration templates loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            raise
    
    def act_fw_int_config(self):
        """Configure physical interfaces on active firewall - matching original"""
        try:
            interface_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/interface/ethernet"
            
            # Apply configuration to active firewall
            config_url = f"https://{self.active_fw_list[0]['host']}/api/"
            interface_params = {
                'type': 'config',
                'action': 'set',
                'xpath': interface_xpath,
                'element': self.pa_interface_tmp,
                'key': self.active_fw_headers[0]['X-PAN-KEY']
            }

            response_interface = requests.get(config_url, params=interface_params, verify=False, timeout=30)
            
            if response_interface.status_code == 200:
                logger.info(f"Interfaces configured successfully on {self.active_fw_list[0]['host']}")
                logger.info(f"Response: {response_interface.text}")
            else:
                logger.error(f"Failed to configure interfaces on {self.active_fw_list[0]['host']}: {response_interface.status_code}")
                logger.error(f"Response: {response_interface.text}")
                raise Exception("Interface configuration failed")

        except Exception as e:
            logger.error(f"Error in interface configuration process: {e}")
            raise

    def act_fw_zone_config(self):
        """Configure security zones on active firewall - matching original"""
        try:
            zone_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/zone"
            zone_config_url = f"https://{self.active_fw_list[0]['host']}/api/"
            zone_params = {
                'type': 'config',
                'action': 'set',
                'xpath': zone_xpath,
                'element': self.pa_zones_tmp,
                'key': self.active_fw_headers[0]['X-PAN-KEY']
            }
            response_zone = requests.get(zone_config_url, params=zone_params, verify=False, timeout=30)
            if response_zone.status_code == 200:
                logger.info(f"Zones configured successfully on {self.active_fw_list[0]['host']}")
                logger.info(f"Response: {response_zone.text}")
            else:
                logger.error(f"Failed to configure zones on {self.active_fw_list[0]['host']}: {response_zone.status_code}")
                logger.error(f"Response: {response_zone.text}")
                raise Exception("Zone configuration failed")
            
        except Exception as e:
            logger.error(f"Error configuring zones: {e}")
            raise
            
    def act_fw_route_config(self):
        """Configure virtual router and static routes - EXACT COPY of original"""
        try:
            # Step 1: Configure virtual router settings (original line ~200)
            route_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry[@name='default']"
            route_config_url = f"https://{self.active_fw_list[0]['host']}/api/"
            route_params = {
                'type': 'config',
                'action': 'set',
                'xpath': route_xpath,
                'element': self.pa_route_settings_tmp,
                'key': self.active_fw_headers[0]['X-PAN-KEY']
            }
            response_route = requests.get(route_config_url, params=route_params, verify=False, timeout=30)
            if response_route.status_code == 200:
                logger.info(f"Route settings configured successfully on {self.active_fw_list[0]['host']}")
                logger.info(f"Response: {response_route.text}")
            else:
                logger.error(f"Failed to configure route settings on {self.active_fw_list[0]['host']}: {response_route.status_code}")
                logger.error(f"Response: {response_route.text}")
                raise Exception("Virtual router configuration failed")
            
            # Step 2: Configure default route (original line ~215)
            default_route_xpath = "/config/devices/entry[@name='localhost.localdomain']/network/virtual-router/entry[@name='default']/routing-table/ip/static-route/entry[@name='default_route']"
            default_route_config_url = f"https://{self.active_fw_list[0]['host']}/api/"
            default_route_params = {
                'type': 'config',
                'action': 'set',
                'xpath': default_route_xpath,
                'element': self.pa_static_routes_tmp,
                'key': self.active_fw_headers[0]['X-PAN-KEY']
            }
            response_default_route = requests.get(default_route_config_url, params=default_route_params, verify=False, timeout=30)
            if response_default_route.status_code == 200:
                logger.info(f"Default route configured successfully on {self.active_fw_list[0]['host']}")
                logger.info(f"Response: {response_default_route.text}")
            else:
                logger.error(f"Failed to configure default route on {self.active_fw_list[0]['host']}: {response_default_route.status_code}")
                logger.error(f"Response: {response_default_route.text}")
                raise Exception("Static route configuration failed")
                
        except Exception as e:
            logger.error(f"Error configuring routes {self.active_fw_list[0]['host']}: {e}")
            raise

    def act_fw_security_policy_config(self):
        """Configure security policies - matching original"""
        try:
            security_policy_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/security/rules"
            security_policy_config_url = f"https://{self.active_fw_list[0]['host']}/api/"
            security_policy_params = {
                'type': 'config',
                'action': 'set',
                'xpath': security_policy_xpath,
                'element': self.pa_security_policy_tmp,
                'key': self.active_fw_headers[0]['X-PAN-KEY']
            }
            response_security_policy = requests.get(security_policy_config_url, params=security_policy_params, verify=False, timeout=30)
            if response_security_policy.status_code == 200:
                logger.info(f"Security policies configured successfully on {self.active_fw_list[0]['host']}")
                logger.info(f"Response: {response_security_policy.text}")
            else:
                logger.error(f"Failed to configure security policies on {self.active_fw_list[0]['host']}: {response_security_policy.status_code}")
                logger.error(f"Response: {response_security_policy.text}")
                raise Exception("Security policy configuration failed")
                
        except Exception as e:
            logger.error(f"Error configuring security policies: {e}")
            raise
            
    def act_fw_source_nat_config(self):
        """Configure source NAT rules - matching original xpath and your working template"""
        try:
            # Get environment variables to match template placeholders
            ethernet1_2_ip_untrust = os.getenv('ETHERNET1_2_IP_UNTRUST', '200.200.200.2/24')
            # Remove the /24 subnet mask for NAT IP
            ethernet1_2_ip_clean = ethernet1_2_ip_untrust.split('/')[0]
            
            # Get interface name for untrust (template expects interface name)
            untrust_interface = os.getenv('UNTRUST', 'ethernet1/2')
            
            # Format NAT template with correct variables
            formatted_nat_xml = self.pa_source_nat_tmp.format(
                ETHERNET1_2_IP_UNTRUST=ethernet1_2_ip_clean,
                UNTRUST=untrust_interface  
            )
            
            logger.debug(f"Formatted NAT XML: {formatted_nat_xml}")
            
            # Use original xpath - configure NAT rules collection
            source_nat_xpath = "/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/rulebase/nat/rules"
            source_nat_config_url = f"https://{self.active_fw_list[0]['host']}/api/"
            source_nat_params = {
                'type': 'config',
                'action': 'set',
                'xpath': source_nat_xpath,
                'element': formatted_nat_xml,
                'key': self.active_fw_headers[0]['X-PAN-KEY']
            }
            response_source_nat = requests.get(source_nat_config_url, params=source_nat_params, verify=False, timeout=30)
            if response_source_nat.status_code == 200:
                logger.info(f"Source NAT configured successfully on {self.active_fw_list[0]['host']}")
                logger.info(f"Response: {response_source_nat.text}")
            else:
                logger.error(f"Failed to configure source NAT on {self.active_fw_list[0]['host']}: {response_source_nat.status_code}")
                logger.error(f"Response: {response_source_nat.text}")
                raise Exception("Source NAT configuration failed")
                
        except Exception as e:
            logger.error(f"Error configuring source NAT: {e}")
            raise