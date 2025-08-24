#!/usr/bin/env python3
"""
Update XML templates with Jenkins parameter values
"""

import os
import sys
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

class TemplateUpdater:
    """
    Updates XML templates with Jenkins parameter values
    """
    
    def __init__(self):
        self.data_dir = "data/payload"
        self.jenkins_params = self._get_jenkins_params()
    
    def _get_jenkins_params(self):
        """Get Jenkins parameters from environment variables"""
        return {
            # HA Interfaces
            'ha_interface_1': os.getenv('HA_INTERFACE_1', 'ethernet1/4'),
            'ha_interface_2': os.getenv('HA_INTERFACE_2', 'ethernet1/5'),
            
            # Data Interface IPs
            'ethernet1_1_ip': os.getenv('ETHERNET1_1_IP', '10.10.10.5/24'),
            'ethernet1_2_ip': os.getenv('ETHERNET1_2_IP', '200.200.200.2/24'),
            'ethernet1_3_ip': os.getenv('ETHERNET1_3_IP', '10.30.30.5/24'),
            
            # Gateway/Routing
            'default_gateway': os.getenv('DEFAULT_GATEWAY', '200.200.200.1'),
            'static_route_network': os.getenv('STATIC_ROUTE_NETWORK', '10.0.0.0/8'),
            'static_route_nexthop': os.getenv('STATIC_ROUTE_NEXTHOP', '10.10.10.1'),
            
            # NAT
            'source_nat_ip': os.getenv('SOURCE_NAT_IP', '200.200.200.10'),
            
            # Security Zones
            'internal_zone_interface': os.getenv('INTERNAL_ZONE_INTERFACE', 'ethernet1/1'),
            'external_zone_interface': os.getenv('EXTERNAL_ZONE_INTERFACE', 'ethernet1/2'),
            'dmz_zone_interface': os.getenv('DMZ_ZONE_INTERFACE', 'ethernet1/3')
        }
    
    def update_interface_template(self):
        """Update data_interface.xml with Jenkins parameters"""
        try:
            logger.info("Updating interface template...")
            
            # Create new interface XML with parameters
            interfaces_xml = f"""<entry name="ethernet1/1">
    <link-state>up</link-state>
    <layer3>
        <ip>
            <entry name="{self.jenkins_params['ethernet1_1_ip']}"/>
        </ip>
        <lldp>
            <enable>no</enable>
        </lldp>
        <ndp-proxy>
            <enabled>no</enabled>
        </ndp-proxy>
    </layer3>
</entry>
<entry name="ethernet1/2">
    <link-state>up</link-state>
    <layer3>
        <ip>
            <entry name="{self.jenkins_params['ethernet1_2_ip']}"/>
        </ip>
        <lldp>
            <enable>no</enable>
        </lldp>
        <ndp-proxy>
            <enabled>no</enabled>
        </ndp-proxy>
    </layer3>
</entry>
<entry name="ethernet1/3">
    <link-state>up</link-state>
    <layer3>
        <ip>
            <entry name="{self.jenkins_params['ethernet1_3_ip']}"/>
        </ip>
        <lldp>
            <enable>no</enable>
        </lldp>
        <ndp-proxy>
            <enabled>no</enabled>
        </ndp-proxy>
    </layer3>
</entry>"""
            
            # Write to file
            interface_file = f"{self.data_dir}/data_interface.xml"
            with open(interface_file, 'w') as f:
                f.write(interfaces_xml)
            
            logger.info(f"Updated {interface_file} with new IP addresses")
            
        except Exception as e:
            logger.error(f"Error updating interface template: {e}")
            raise
    
    def update_ha_interface_template(self):
        """Update HA interface template with Jenkins parameters"""
        try:
            logger.info("Updating HA interface template...")
            
            # Create HA interface XML with parameters
            ha_xml = f"""<entry name="{self.jenkins_params['ha_interface_1']}">
    <ha/>
</entry>
<entry name="{self.jenkins_params['ha_interface_2']}">
    <ha/>
</entry>"""
            
            # Write to file
            ha_file = f"{self.data_dir}/data_ha_interface.xml"
            with open(ha_file, 'w') as f:
                f.write(ha_xml)
            
            logger.info(f"Updated {ha_file} with HA interfaces: {self.jenkins_params['ha_interface_1']}, {self.jenkins_params['ha_interface_2']}")
            
        except Exception as e:
            logger.error(f"Error updating HA interface template: {e}")
            raise
    
    def update_routing_template(self):
        """Update routing template with Jenkins parameters"""
        try:
            logger.info("Updating routing template...")
            
            # Create static routes XML with parameters
            routes_xml = f"""<entry name="default-route">
    <destination>0.0.0.0/0</destination>
    <interface>{self.jenkins_params['external_zone_interface']}</interface>
    <nexthop>
        <ip-address>{self.jenkins_params['default_gateway']}</ip-address>
    </nexthop>
    <metric>10</metric>
</entry>
<entry name="internal-route">
    <destination>{self.jenkins_params['static_route_network']}</destination>
    <interface>{self.jenkins_params['internal_zone_interface']}</interface>
    <nexthop>
        <ip-address>{self.jenkins_params['static_route_nexthop']}</ip-address>
    </nexthop>
    <metric>10</metric>
</entry>"""
            
            # Write to file
            routes_file = f"{self.data_dir}/data_routes.xml"
            with open(routes_file, 'w') as f:
                f.write(routes_xml)
            
            logger.info(f"Updated {routes_file} with gateway: {self.jenkins_params['default_gateway']}")
            
        except Exception as e:
            logger.error(f"Error updating routing template: {e}")
            raise
    
    def update_nat_template(self):
        """Update NAT template with Jenkins parameters"""
        try:
            logger.info("Updating NAT template...")
            
            # Create NAT rules XML with parameters
            nat_xml = f"""<entry name="source-nat-rule">
    <from>
        <member>internal</member>
        <member>dmz</member>
    </from>
    <to>
        <member>external</member>
    </to>
    <source>
        <member>any</member>
    </source>
    <destination>
        <member>any</member>
    </destination>
    <service>any</service>
    <source-translation>
        <static-ip>
            <translated-address>{self.jenkins_params['source_nat_ip']}</translated-address>
        </static-ip>
    </source-translation>
</entry>"""
            
            # Write to file
            nat_file = f"{self.data_dir}/data_nat.xml"
            with open(nat_file, 'w') as f:
                f.write(nat_xml)
            
            logger.info(f"Updated {nat_file} with NAT IP: {self.jenkins_params['source_nat_ip']}")
            
        except Exception as e:
            logger.error(f"Error updating NAT template: {e}")
            raise
    
    def update_zones_template(self):
        """Update zones template with Jenkins parameters"""
        try:
            logger.info("Updating zones template...")
            
            # Create zones XML with parameters
            zones_xml = f"""<entry name="internal">
    <network>
        <layer3>
            <member>{self.jenkins_params['internal_zone_interface']}</member>
        </layer3>
    </network>
</entry>
<entry name="external">
    <network>
        <layer3>
            <member>{self.jenkins_params['external_zone_interface']}</member>
        </layer3>
    </network>
</entry>
<entry name="dmz">
    <network>
        <layer3>
            <member>{self.jenkins_params['dmz_zone_interface']}</member>
        </layer3>
    </network>
</entry>"""
            
            # Write to file
            zones_file = f"{self.data_dir}/data_zones.xml"
            with open(zones_file, 'w') as f:
                f.write(zones_xml)
            
            logger.info(f"Updated {zones_file} with zone interfaces")
            
        except Exception as e:
            logger.error(f"Error updating zones template: {e}")
            raise
    
    def execute(self):
        """Execute all template updates"""
        try:
            logger.info("Starting template updates with Jenkins parameters...")
            logger.info(f"Parameters: {self.jenkins_params}")
            
            # Create data directory if it doesn't exist
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Update all templates
            self.update_interface_template()
            self.update_ha_interface_template() 
            self.update_routing_template()
            self.update_nat_template()
            self.update_zones_template()
            
            logger.info("All templates updated successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error updating templates: {e}")
            return False

if __name__ == "__main__":
    updater = TemplateUpdater()
    success = updater.execute()
    sys.exit(0 if success else 1)