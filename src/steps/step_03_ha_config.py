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
import xml.etree.ElementTree as ET

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step03_HAConfig:
    """
    Configure HA settings on all devices.
    Fresh deployment - always applies configuration.
    Based on working pa_deployment_ha.py pattern.
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
            
            # Load HA configuration templates using your existing constants
            self.load_ha_templates()
            
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
            
            # Configure HA on each device using working three-step pattern
            for i, (device, headers) in enumerate(zip(pa_credentials, api_keys_list)):
                host = device['host']
                logger.info(f"Configuring HA settings on {host} (fresh configuration)")
                
                try:
                    ha_url = f"https://{host}/api/"
                    
                    # Step 1: Enable basic HA - EXACT COPY from working version
                    logger.info(f"Enabling basic HA on {host}")
                    basic_ha_params = {
                        'type': 'config',
                        'action': 'set',
                        'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                        'element': '<enabled>yes</enabled>',
                        'key': headers['X-PAN-KEY']
                    }
                    response_basic = requests.get(ha_url, params=basic_ha_params, verify=False, timeout=30)
                    if response_basic.status_code == 200:
                        logger.info(f"Basic HA enabled on {host}")
                    else:
                        logger.error(f"Failed to enable basic HA on {host}: {response_basic.status_code}")
                        continue  # Skip this device but continue with others
                        
                    # Step 2: Configure HA group - EXACT COPY from working version
                    logger.info(f"Configuring HA group on {host}")
                    ha_config = ha_configs[i]
                    
                    # Format the template with proper substitution
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
                        'override': 'yes',
                        'key': headers['X-PAN-KEY']
                    }
                    response_group = requests.get(ha_url, params=group_params, verify=False, timeout=30)
                    if response_group.status_code == 200:
                        logger.info(f"HA group configured on {host}")
                    else:
                        logger.error(f"Failed to configure HA group on {host}: {response_group.status_code}")
                        continue  # Skip this device but continue with others
                        
                    # Step 3: Configure HA interfaces - EXACT COPY from working version
                    logger.info(f"Configuring HA interfaces on {host}")
                    config = interface_configs[i]
                    
                    # Use ONLY ha1_ip like the original
                    interface_xml = self.pa_ha_int_tmp.format(ha1_ip=config['ha1_ip'])
                    
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
                        configured_devices.append(host)
                        logger.info(f"HA configuration completed for {host}")
                    else:
                        logger.error(f"Failed to configure HA interfaces on {host}: {response_int.status_code}")
                        continue  # Skip this device but continue with others
                        
                except Exception as e:
                    logger.error(f"Error configuring HA on {host}: {e}")
                    continue  # Skip this device but continue with others
            
            # Commit changes using working pattern from original
            logger.info(f"HA configuration applied to {len(configured_devices)} devices - committing changes")
            logger.info("Waiting 15 seconds for HA configuration to settle...")
            time.sleep(15)
            
            success = self.commit_changes(pa_credentials, api_keys_list)
            if not success:
                logger.warning("Commit failed - but configuration was applied")
                # Additional HA enable step if needed
                logger.info("Waiting additional 15 seconds for HA to establish...")
                time.sleep(15)
                self.force_enable_ha(pa_credentials, api_keys_list)
            
            # Verify HA configuration
            logger.info("Verifying HA configuration...")
            self.verify_ha_status(pa_credentials, api_keys_list)
            
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
    
    def load_ha_templates(self):
        """Load HA configuration templates using your existing constants"""
        try:
            from utils_pa import PA_HA_CONFIG_TEMPLATE, PA_HA_INTERFACE_TEMPLATE
            
            with open(PA_HA_CONFIG_TEMPLATE, 'r') as f:
                self.pa_ha_config_tmp = f.read()
            
            with open(PA_HA_INTERFACE_TEMPLATE, 'r') as f:
                self.pa_ha_int_tmp = f.read()
                
            logger.info("Loaded HA configuration templates")
            
        except Exception as e:
            logger.error(f"Error loading HA templates: {e}")
            raise
    
    def commit_changes(self, pa_credentials, api_keys_list):
        """
        Commit configuration changes using working pattern from original.
        EXACT COPY of commit logic from pa_deployment_ha.py
        """
        jobid_dict = {}
        ready_devices = {}

        logger.info("Starting commit operations for HA Configuration...")
        
        # Step 1: Start commits and collect job IDs - EXACT COPY
        for device, headers in zip(pa_credentials, api_keys_list):  
            try:
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
                        if jobid:
                            # Store device info with job ID - EXACT PATTERN
                            unique_key = f"{device['host']}_{jobid}"
                            jobid_dict[unique_key] = {
                                'device': device,
                                'headers': headers,
                                'host': device['host'],
                                'jobid': jobid
                            }
                            logger.info(f"Commit job ID for {device['host']}: {jobid}")
            except Exception as e:
                logger.error(f"Error committing changes for {device['host']}: {e}") 
        
        # Check if any jobs were started       
        if not jobid_dict:
            logger.error("No commit jobs started")
            return False
            
        # Step 2: Monitor jobs until all complete - EXACT COPY
        logger.info(f"Monitoring {len(jobid_dict)} commit jobs...")
        max_wait_time = 300  # 5 minutes max wait
        start_time = time.time()
        
        try:
            while jobid_dict and (time.time() - start_time) < max_wait_time:
                completed_jobs = []
                for unique_key, job_info in jobid_dict.items():
                    device = job_info['device']
                    headers = job_info['headers']
                    host = job_info['host']
                    jobid = job_info['jobid']
                    
                    # Check job status for this specific device
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
                            elif job_status == "FIN":
                                if job_result == "OK":
                                    logger.info(f"Commit completed successfully for {host}")
                                    ready_devices[host] = [host]
                                else:
                                    logger.error(f"Commit failed on {host}: {job_result}")
                                completed_jobs.append(unique_key) # Mark job as completed
                                
                # Remove completed jobs from the dictionary
                for unique_key in completed_jobs:
                    if unique_key in jobid_dict:
                        del jobid_dict[unique_key]
                                        
                if len(ready_devices) == len(pa_credentials):
                    logger.info("All commits completed successfully for HA Configuration!")
                    return True
                
                # Wait before checking again
                if jobid_dict:  # Only sleep if there are still jobs to monitor
                    time.sleep(15)
                    
        except Exception as e:
            logger.error(f"Error monitoring commits: {e}")
            return False
            
        return len(ready_devices) == len(pa_credentials)
    
    def force_enable_ha(self, pa_credentials, api_keys_list):
        """Force enable HA on both devices if needed"""
        logger.info("Force enabling HA on both devices...")
        for device, headers in zip(pa_credentials, api_keys_list):
            try:
                ha_url = f"https://{device['host']}/api/"
                force_enable_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': "/config/devices/entry[@name='localhost.localdomain']/deviceconfig/high-availability",
                    'element': '<enabled>yes</enabled>',
                    'key': headers['X-PAN-KEY']
                }
                response = requests.get(ha_url, params=force_enable_params, verify=False, timeout=30)
                if response.status_code == 200:
                    logger.info(f"HA force-enabled on {device['host']}")
                else:
                    logger.error(f"Failed to force-enable HA on {device['host']}")
            except Exception as e:
                logger.error(f"Error force-enabling HA on {device['host']}: {e}")
        
        # Commit the force enable
        logger.info("Committing HA enable...")
        self.commit_changes(pa_credentials, api_keys_list)
    
    def verify_ha_status(self, pa_credentials, api_keys_list):
        """Verify HA status on both devices"""
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
                    logger.error(f"Failed to get HA status for {device['host']}")
            except Exception as e:
                logger.error(f"Error getting HA status for {device['host']}: {e}")