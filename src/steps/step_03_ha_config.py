"""
Step 3: Configure HA Settings for PA Firewalls

Configures High Availability group settings and interface assignments for
both firewall devices. Establishes active-passive HA relationship with
proper priorities, peer IP addresses, and interface configurations.

Key Features:
- Configures HA group with device priorities and preemption settings
- Assigns unique HA1 IP addresses to each device (1.1.1.1/1.1.1.2)
- Commits configuration and verifies HA status establishment
- Uses Jenkins parameters for interface selection (HA1/HA2 ports)
"""

import requests
import logging
import pickle
import sys
import os
import time
import xml.etree.ElementTree as ET

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step03_HAConfig:
    
    def __init__(self):
        pass
    
    def execute(self):
        try:
            # Load data from previous step
            with open('ha_interfaces_data.pkl', 'rb') as f:
                step_data = pickle.load(f)
            
            pa_credentials = step_data['pa_credentials']
            api_keys_list = step_data['api_keys_list']
            logger.info("Fresh deployment - applying HA configuration")
            
            # Load templates 
            self.load_ha_templates()
            
            # Get environment variables for HA ports
            ha1_port = os.getenv('HA1_INTERFACE', 'ethernet1/4')
            ha2_port = os.getenv('HA2_INTERFACE', 'ethernet1/5')
            
            ha_configs = [
                {'device_priority': '100', 'preemptive': 'yes', 'peer_ip': '1.1.1.2'},
                {'device_priority': '110', 'preemptive': 'no', 'peer_ip': '1.1.1.1'}
            ]

            interface_configs = [
                {'ha1_ip': '1.1.1.1', 'ha1_port': ha1_port, 'ha2_port': ha2_port},
                {'ha1_ip': '1.1.1.2', 'ha1_port': ha1_port, 'ha2_port': ha2_port}
            ]
            
            for i, (device, headers) in enumerate(zip(pa_credentials, api_keys_list)):
                host = device['host']
                logger.info(f"Configuring HA settings on {host} (fresh configuration)")
                
                ha_url = f"https://{host}/api/"
                
                # Step 1: Enable basic HA
                logger.info(f"Enabling basic HA on {host}")
                basic_ha_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                    'element': '<enabled>yes</enabled>',
                    'key': headers['X-PAN-KEY']
                }
                response_basic = requests.get(ha_url, params=basic_ha_params, verify=False, timeout=30)
                logger.info(f"Basic HA enabled on {host}")
                    
                # Step 2: Configure HA group
                logger.info(f"Configuring HA group on {host}")
                ha_config = ha_configs[i]
                
                group_xml = self.pa_ha_config_tmp.format(
                    device_priority=ha_config['device_priority'],
                    preemptive=ha_config['preemptive'],
                    peer_ip=ha_config['peer_ip']
                )
                
                group_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/group",
                    'element': group_xml,
                    'key': headers['X-PAN-KEY']
                }
                response_group = requests.get(ha_url, params=group_params, verify=False, timeout=30)
                logger.info(f"HA group configured on {host}")
                    
                # Step 3: Configure HA interfaces
                logger.info(f"Configuring HA interfaces on {host}")
                config = interface_configs[i]
                logger.info(f"Device {host} (index {i}) getting HA1 IP: {config['ha1_ip']}")

                interface_xml = self.pa_ha_int_tmp.format(
                    ha1_ip=config['ha1_ip'],
                    ha1_port=config['ha1_port'],
                    ha2_port=config['ha2_port']
                )
                
                logger.info(f"Device {host} interface XML: {interface_xml}")

                interface_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability/interface",
                    'element': interface_xml,
                    'key': headers['X-PAN-KEY']
                }
                response_int = requests.get(ha_url, params=interface_params, verify=False, timeout=30)
                logger.info(f"HA interfaces configured on {host}")
                logger.info(f"HA configuration completed for {host}")
            
            # Commit - SINGLE COMMIT like working version
            logger.info(f"HA configuration applied to 2 devices - committing changes")
            logger.info("Waiting 15 seconds for HA configuration to settle...")
            time.sleep(15)
            
            self.commit_changes(pa_credentials, api_keys_list)
            
            # Verify HA
            logger.info("Verifying HA configuration...")
            self.verify_ha_status(pa_credentials, api_keys_list)
            
            # Save data for next step
            step_data = {
                'ha_config_applied': True,
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
    
    def load_ha_templates(self):
        from utils_pa import PA_HA_CONFIG_TEMPLATE, PA_HA_INTERFACE_TEMPLATE
        
        with open(PA_HA_CONFIG_TEMPLATE, 'r') as f:
            self.pa_ha_config_tmp = f.read()
        
        with open(PA_HA_INTERFACE_TEMPLATE, 'r') as f:
            self.pa_ha_int_tmp = f.read()
            
        logger.info("Loaded HA configuration templates")
    
    def commit_changes(self, pa_credentials, api_keys_list):
        jobid_dict = {}
        ready_devices = {}

        logger.info("Starting commit operations for HA Configuration...")
        
        for device, headers in zip(pa_credentials, api_keys_list):  
            commit_url = f"https://{device['host']}/api/"
            commit_params = {
                'type': 'commit',
                'cmd': '<commit></commit>',
                'key': headers['X-PAN-KEY']  
            }
            
            response = requests.get(commit_url, params=commit_params, verify=False, timeout=60)
            
            if response.status_code == 200:
                xml_response = response.text
                root = ET.fromstring(xml_response)
                result = root.find(".//result")
                if result is not None:
                    jobid = result.findtext("job")
                    unique_key = f"{device['host']}_{jobid}"
                    jobid_dict[unique_key] = {
                        'device': device,
                        'headers': headers,
                        'host': device['host'],
                        'jobid': jobid
                    }
                    logger.info(f"Commit job ID for {device['host']}: {jobid}")
        
        logger.info(f"Monitoring {len(jobid_dict)} commit jobs...")
        while jobid_dict:
            completed_jobs = []
            for unique_key, job_info in jobid_dict.items():
                host = job_info['host']
                jobid = job_info['jobid']
                headers = job_info['headers']
                
                job_url = f"https://{host}/api/"
                job_params = {
                    'type': 'op',
                    'cmd': f'<show><jobs><id>{jobid}</id></jobs></show>',
                    'key': headers['X-PAN-KEY']
                }
                job_response = requests.get(job_url, params=job_params, verify=False, timeout=30)
                
                if job_response.status_code == 200:
                    job_xml_response = job_response.text
                    root = ET.fromstring(job_xml_response)
                    job = root.find(".//job")
                    
                    if job is not None:
                        job_status = job.findtext("status")
                        job_progress = job.findtext("progress", "0")
                        job_result = job.findtext("result", "")
                        
                        if job_status == "ACT":
                            logger.info(f"Commit running for {host}, progress {job_progress}%")
                            time.sleep(15)
                        elif job_status == "FIN":
                            if job_result == "OK":
                                logger.info(f"Commit completed successfully for {host}")
                                ready_devices[host] = [host]
                            else:
                                logger.error(f"Commit failed on {host}: {job_result}")
                            completed_jobs.append(unique_key)
                            
            for unique_key in completed_jobs:
                if unique_key in jobid_dict:
                    del jobid_dict[unique_key]
                                    
            if len(ready_devices) == len(pa_credentials):
                logger.info("All commits completed successfully for HA Configuration!")
                break
    
    def verify_ha_status(self, pa_credentials, api_keys_list):
        for device, headers in zip(pa_credentials, api_keys_list):
            ha_status_url = f"https://{device['host']}/api/"
            ha_status_params = {
                'type': 'op',
                'cmd': '<show><high-availability><state></state></high-availability></show>',
                'key': headers['X-PAN-KEY']
            }
            response = requests.get(ha_status_url, params=ha_status_params, verify=False, timeout=30)
            if response.status_code == 200:
                logger.info(f"HA status for {device['host']}: {response.text}")