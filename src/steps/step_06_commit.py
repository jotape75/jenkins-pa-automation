"""
Step 6: Commit and Sync Configuration

For fresh deployments - always commits configuration and syncs to HA peer.
"""

import requests
import logging
import pickle
import xml.etree.ElementTree as ET
import sys
import os
import time

# Add the src directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()
logger = logging.getLogger()

class Step06_CommitSync:
    """
    Commit configuration changes and force HA synchronization.
    Fresh deployment - always commits and syncs.
    """
    
    def __init__(self):
        pass
    
    def execute(self):
        """
        Execute commit and sync operations.
        Fresh deployment - always commits and syncs configuration.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load firewall configuration data from previous step
            with open('firewall_config_data.pkl', 'rb') as f:
                config_data = pickle.load(f)
            
            active_fw_list = config_data['active_fw_list']
            active_fw_headers = config_data['active_fw_headers']
            config_results = config_data['config_results']
            
            active_host = active_fw_list[0]['host']
            logger.info(f"Fresh deployment - committing and syncing configuration on: {active_host}")
            logger.info(f"Configuration applied: {config_results}")
            
            commit_results = {}
            
            # Step 6.1: Commit Configuration Changes
            logger.info("=== STEP 6.1: Committing Configuration ===")
            if not self._commit_changes(active_fw_list, active_fw_headers, commit_results):
                return False
            
            # Step 6.2: Force HA Configuration Sync
            logger.info("=== STEP 6.2: Syncing to HA Peer ===")
            if not self._force_sync_config(active_fw_list, active_fw_headers, commit_results):
                logger.warning("HA sync failed, but configuration is committed")
                # Don't fail the entire deployment if sync fails
            
            # Save completion status
            step_data = {
                'commit_completed': True,
                'sync_completed': commit_results.get('ha_sync') == 'success',
                'commit_results': commit_results,
                'config_results': config_results,
                'deployment_completed': True,
                'configured_host': active_host
            }
            
            with open('commit_sync_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("=== DEPLOYMENT COMPLETED ===")
            logger.info(f"Commit result: {commit_results.get('commit', 'unknown')}")
            logger.info(f"Sync result: {commit_results.get('ha_sync', 'unknown')}")
            logger.info(f"Configuration deployed to: {active_host}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in commit and sync: {e}")
            return False
        
    def _commit_changes(self, active_fw_list, active_fw_headers, results):
        """Commit configuration changes on active firewall"""
        try:
            host = active_fw_list[0]['host']
            api_key = active_fw_headers[0]['X-PAN-KEY']
            
            logger.info(f"Starting configuration commit on {host}")
            
            # Start commit
            commit_url = f"https://{host}/api/"
            commit_params = {
                'type': 'commit',
                'cmd': '<commit></commit>',
                'key': api_key
            }
            
            response_commit = requests.get(commit_url, params=commit_params, verify=False, timeout=60)
            
            if response_commit.status_code != 200:
                logger.error(f"Failed to start commit on {host}: {response_commit.status_code}")
                logger.error(f"Response: {response_commit.text}")
                results['commit'] = 'failed'
                return False
            
            # Parse job ID
            xml_response = response_commit.text
            logger.debug(f"Commit response: {xml_response}")
            root = ET.fromstring(xml_response)
            result = root.find(".//result")
            
            if result is None:
                logger.error(f"Invalid commit response from {host}: {xml_response}")
                results['commit'] = 'failed'
                return False
            
            jobid = result.findtext("job")
            if not jobid:
                logger.error(f"No job ID found in commit response from {host}")
                results['commit'] = 'failed'
                return False
            
            logger.info(f"Commit job started on {host}, job ID: {jobid}")
            
            # Monitor commit progress
            max_wait_time = 300  # 5 minutes max
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                job_url = f"https://{host}/api/"
                job_params = {
                    'type': 'op',
                    'cmd': f'<show><jobs><id>{jobid}</id></jobs></show>',
                    'key': api_key
                }
                
                job_response = requests.get(job_url, params=job_params, verify=False, timeout=30)
                
                if job_response.status_code != 200:
                    logger.warning(f"Failed to check job status: {job_response.status_code}")
                    time.sleep(10)
                    continue
                
                job_xml = job_response.text
                logger.debug(f"Job status response: {job_xml}")
                root = ET.fromstring(job_xml)
                job = root.find(".//job")
                
                if job is None:
                    logger.warning(f"No job info found in response")
                    time.sleep(10)
                    continue
                
                job_status = job.findtext("status")
                job_progress = job.findtext("progress", "0")
                job_result = job.findtext("result", "")
                
                if job_status == "ACT":
                    logger.info(f"Commit in progress on {host}: {job_progress}%")
                    time.sleep(15)
                elif job_status == "FIN":
                    if job_result == "OK":
                        logger.info(f"Commit completed successfully on {host}")
                        results['commit'] = 'success'
                        return True
                    else:
                        logger.error(f"Commit failed on {host}: {job_result}")
                        logger.error(f"Job details: {job_xml}")
                        results['commit'] = 'failed'
                        return False
                else:
                    logger.warning(f"Unknown job status: {job_status}")
                    time.sleep(10)
            
            # Timeout
            logger.error(f"Commit timeout on {host} after {max_wait_time} seconds")
            results['commit'] = 'timeout'
            return False
            
        except Exception as e:
            logger.error(f"Error committing changes on {host}: {e}")
            results['commit'] = 'error'
            return False
    
    def _force_sync_config(self, active_fw_list, active_fw_headers, results):
        """Force HA configuration sync to passive firewall"""
        try:
            host = active_fw_list[0]['host']
            api_key = active_fw_headers[0]['X-PAN-KEY']
            
            logger.info(f"Checking HA sync status on {host}")
            
            sync_url = f"https://{host}/api/"
            
            # Check current sync status
            check_params = {
                'type': 'op',
                'cmd': '<show><high-availability><state></state></high-availability></show>',
                'key': api_key
            }
            
            response = requests.get(sync_url, params=check_params, verify=False, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Failed to check HA sync status on {host}: {response.status_code}")
                results['ha_sync'] = 'failed'
                return False
            
            xml_response = response.text
            logger.debug(f"HA state response: {xml_response}")
            root = ET.fromstring(xml_response)
            config_state = root.findtext(".//group/running-sync")
            
            logger.info(f"Current HA sync state: {config_state}")
            
            if config_state == "synchronized":
                logger.info(f"Configuration already synchronized on {host}")
                results['ha_sync'] = 'success'
                return True
            elif config_state == "synchronization in progress":
                logger.info(f"Synchronization already in progress on {host}")
                return self._wait_for_sync_completion(host, api_key, results)
            elif config_state == "not synchronized":
                logger.info(f"Initiating HA sync on {host}")
                
                # Start sync
                sync_params = {
                    'type': 'op',
                    'cmd': '<request><high-availability><sync-to-remote><running-config></running-config></sync-to-remote></high-availability></request>',
                    'key': api_key
                }
                
                sync_response = requests.get(sync_url, params=sync_params, verify=False, timeout=30)
                
                if sync_response.status_code != 200:
                    logger.error(f"Failed to initiate sync on {host}: {sync_response.status_code}")
                    logger.error(f"Response: {sync_response.text}")
                    results['ha_sync'] = 'failed'
                    return False
                
                logger.info(f"HA sync initiated on {host}")
                logger.debug(f"Sync response: {sync_response.text}")
                
                return self._wait_for_sync_completion(host, api_key, results)
            else:
                logger.warning(f"Unknown HA sync state: {config_state}")
                results['ha_sync'] = 'unknown'
                return False
                
        except Exception as e:
            logger.error(f"Error during HA sync: {e}")
            results['ha_sync'] = 'error'
            return False
    
    def _wait_for_sync_completion(self, host, api_key, results):
        """Wait for HA sync to complete"""
        try:
            logger.info(f"Waiting for HA sync completion on {host}")
            
            max_checks = 12  # 3 minutes max (12 * 15 seconds)
            sync_url = f"https://{host}/api/"
            
            for check in range(max_checks):
                time.sleep(15)  # Wait between checks
                
                check_params = {
                    'type': 'op',
                    'cmd': '<show><high-availability><state></state></high-availability></show>',
                    'key': api_key
                }
                
                response = requests.get(sync_url, params=check_params, verify=False, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to check sync status: {response.status_code}")
                    continue
                
                root = ET.fromstring(response.text)
                current_state = root.findtext(".//group/running-sync")
                
                logger.info(f"Sync check {check + 1}/{max_checks}: {current_state}")
                
                if current_state == "synchronized":
                    logger.info(f"HA synchronization completed successfully on {host}")
                    results['ha_sync'] = 'success'
                    return True
                elif current_state in ["synchronization in progress", "sync in progress", "syncing"]:
                    continue
                else:
                    logger.warning(f"Unexpected sync state: {current_state}")
                    continue
            
            # Timeout
            logger.warning(f"HA sync timeout on {host} - sync may still be in progress")
            results['ha_sync'] = 'timeout'
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for sync completion: {e}")
            results['ha_sync'] = 'error'
            return False