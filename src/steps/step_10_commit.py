"""
Step 6: Commit and Sync Configuration

Extracts commit_changes and force_sync_config logic from PaloAltoFirewall_config class
and adapts it for Jenkins execution.
"""

import requests
import logging
import pickle
import json
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
    
    Performs final deployment steps exactly like the original working class.
    """
    
    def __init__(self):
        """
        Initialize commit and sync step.
        """
        pass
    
    def execute(self):
        """
        Execute commit and sync operations.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load firewall configuration data from previous step
            try:
                with open('firewall_config_data.pkl', 'rb') as f:
                    config_data = pickle.load(f)
                
                active_fw_list = config_data['active_fw_list']
                active_fw_headers = config_data['active_fw_headers']
                config_results = config_data['config_results']
                logger.info("Using firewall configuration data for commit and sync")
                
            except FileNotFoundError:
                # Fallback to active firewall data if firewall config data not available
                logger.warning("Firewall config data not found, using active firewall data")
                with open('active_fw_data.pkl', 'rb') as f:
                    active_fw_data = pickle.load(f)
                
                active_fw_list = active_fw_data['active_fw_list']
                active_fw_headers = active_fw_data['active_fw_headers']
                config_results = {}
            
            active_host = active_fw_list[0]['host']
            logger.info(f"Committing and syncing configuration on: {active_host}")
            
            # Check if any configuration changes were made
            changes_made = any(result in ['success'] for result in config_results.values())
            if not changes_made:
                logger.info("No configuration changes were made - skipping commit and sync")
                
                # Save completion status anyway
                step_data = {
                    'commit_completed': True,
                    'sync_completed': True,
                    'commit_skipped': True,
                    'sync_skipped': True,
                    'config_results': config_results
                }
                
                with open('commit_sync_data.pkl', 'wb') as f:
                    pickle.dump(step_data, f)
                
                logger.info("Commit and sync completed (skipped - no changes)")
                return True
            
            commit_results = {}
            
            # Step 6.1: Commit Configuration Changes - EXACT original logic
            if not self._commit_changes(active_fw_list, active_fw_headers, commit_results):
                return False
            
            # Step 6.2: Force HA Configuration Sync - EXACT original logic
            if not self._force_sync_config(active_fw_list, active_fw_headers, commit_results):
                return False
            
            # Save completion status for audit
            step_data = {
                'commit_completed': True,
                'sync_completed': True,
                'commit_skipped': False,
                'sync_skipped': False,
                'commit_results': commit_results,
                'config_results': config_results,
                'deployment_completed': True
            }
            
            with open('commit_sync_data.pkl', 'wb') as f:
                pickle.dump(step_data, f)
            
            logger.info("Commit and sync configuration completed successfully")
            logger.info(f"Final deployment summary: {commit_results}")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in commit and sync: {e}")
            return False
    
    def _commit_changes(self, active_fw_list, active_fw_headers, results):
        """Commit configuration changes - EXACT logic from original commit_changes()"""
        # Step 1: Start commits and collect job IDs
        try:
            commit_url = f"https://{active_fw_list[0]['host']}/api/"
            commit_params = {
                'type': 'commit',
                'cmd': '<commit></commit>',
                'key': active_fw_headers[0]['X-PAN-KEY']  
            }
            
            response_commit = requests.get(commit_url, params=commit_params, verify=False, timeout=60)
            
            if response_commit.status_code == 200:
                xml_response_commit = response_commit.text
                root = ET.fromstring(xml_response_commit)
                result = root.find(".//result")
                if result is not None:
                    jobid = result.findtext("job")
                    if jobid:
                        logger.info(f"Commit job ID for {active_fw_list[0]['host']}: {jobid}")
                    else:
                        logger.error(f"No job ID found in commit response for {active_fw_list[0]['host']}")
                        results['commit'] = 'failed'
                        return False
                else:
                    logger.error(f"Invalid commit response for {active_fw_list[0]['host']}: {xml_response_commit}")
                    results['commit'] = 'failed'
                    return False
            else:
                logger.error(f"Failed to start commit for {active_fw_list[0]['host']}: {response_commit.status_code}")
                results['commit'] = 'failed'
                return False
        except Exception as e:
            logger.debug(f"Error committing changes for {active_fw_list[0]['host']}: {e}")
            results['commit'] = 'error'
            return False
        
        # Check if any jobs were started       
        if not jobid:
            logger.error("No commit jobs started")
            results['commit'] = 'failed'
            return False
            
        # Step 2: Monitor jobs until all complete - EXACT original logic
        try:
            while jobid:
                # Check job status for this specific device
                job_url = f"https://{active_fw_list[0]['host']}/api/"
                job_params = {
                    'type': 'op',
                    'cmd': f'<show><jobs><id>{jobid}</id></jobs></show>',
                    'key': active_fw_headers[0]['X-PAN-KEY']
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
                            logger.info(f"Commit running for {active_fw_list[0]['host']}, progress {job_progress}% - job ID: {jobid}")
                            logger.info(f"logging job XML response for {active_fw_list[0]['host']}: {job_xml_response}")
                            time.sleep(15)  # Wait before checking again
                        elif job_status == "FIN":
                            if job_result == "OK":
                                logger.info(f"Commit completed successfully for {active_fw_list[0]['host']} - job ID: {jobid}")
                                logger.info(f"logging job XML response for {active_fw_list[0]['host']}: {job_xml_response}")
                                results['commit'] = 'success'
                                return True
                            else:
                                logger.error(f"Job {jobid} failed on {active_fw_list[0]['host']}: {job_result}")
                                logger.error(f"logging job XML response for {active_fw_list[0]['host']}: {job_xml_response}")
                                results['commit'] = 'failed'
                                return False
        except Exception as e:
            logger.error(f"Error committing changes for {active_fw_list[0]['host']}: {e}")
            results['commit'] = 'error'
            return False
    
    def _force_sync_config(self, active_fw_list, active_fw_headers, results):
        """Force HA configuration sync - EXACT logic from original force_sync_config()"""
        try:
            check_sync_url = f"https://{active_fw_list[0]['host']}/api/"
            check_sync_params = {
                'type': 'op',
                'cmd': '<show><high-availability><state></state></high-availability></show>',
                'key': active_fw_headers[0]['X-PAN-KEY']
            }
            response_sync = requests.get(check_sync_url, params=check_sync_params, verify=False, timeout=30)
            logger.info(f"Response: {response_sync.status_code}")
            if response_sync.status_code == 200:
                xml_response_sync = response_sync.text
                root = ET.fromstring(xml_response_sync)
                config_state = root.findtext(".//group/running-sync")
                if config_state == "synchronized":
                    logger.info(f"Configuration is already synced on {active_fw_list[0]['host']}")
                    results['ha_sync'] = 'success'
                    return True
                elif config_state == "synchronization in progress":
                    if self._wait_for_sync_completion(active_fw_list, active_fw_headers):
                        results['ha_sync'] = 'success'
                        return True
                    else:
                        results['ha_sync'] = 'failed'
                        return False
                elif config_state == "not synchronized":
                    sync_params = {
                        'type': 'op',
                        'cmd': '<request><high-availability><sync-to-remote><running-config></running-config></sync-to-remote></high-availability></request>',
                        'key': active_fw_headers[0]['X-PAN-KEY']
                    }
                    response_sync = requests.get(check_sync_url, params=sync_params, verify=False, timeout=30)
                    if response_sync.status_code == 200:
                        logger.info(f"Configuration sync initiated on {active_fw_list[0]['host']}")
                        logger.info(f"Response: {response_sync.text}")
                        if self._wait_for_sync_completion(active_fw_list, active_fw_headers):
                            results['ha_sync'] = 'success'
                            return True
                        else:
                            results['ha_sync'] = 'failed'
                            return False
                    else:
                        logger.error(f"Failed to initiate configuration sync on {active_fw_list[0]['host']}: {response_sync.status_code}")
                        logger.error(f"Response: {response_sync.text}")
                        results['ha_sync'] = 'failed'
                        return False
            else:
                logger.error(f"Failed to sync configuration on {active_fw_list[0]['host']}: {response_sync.status_code}")
                results['ha_sync'] = 'failed'
                return False
        except Exception as e:
            logger.error(f"Error during configuration sync: {e}")
            results['ha_sync'] = 'error'
            return False
    
    def _wait_for_sync_completion(self, active_fw_list, active_fw_headers):
        """Monitor HA sync completion - EXACT logic from original wait_for_sync_completion()"""
        try:
            max_checks = 8  # Check each 15 seconds for a maximum of 2 minutes
            check_sync_url = f"https://{active_fw_list[0]['host']}/api/"

            for check in range(max_checks):
                time.sleep(15)  # Wait between checks
                
                check_params = {
                    'type': 'op',
                    'cmd': '<show><high-availability><state></state></high-availability></show>',
                    'key': active_fw_headers[0]['X-PAN-KEY']
                }
                
                response = requests.get(check_sync_url, params=check_params, verify=False)
                
                if response.status_code == 200:
                    root = ET.fromstring(response.text)
                    current_state = root.findtext(".//group/running-sync")
                    
                    logger.info(f" Sync check {check + 1}/{max_checks}: Status = {current_state}")
                    
                    if current_state == "synchronized":
                        logger.info(f"Running Config synchronization completed successfully!")
                        return True
                        
                    elif current_state in ["synchronization in progress", "sync in progress", "syncing"]:
                        continue
            
            # If we get here, sync didn't complete in time
            logger.warning("Sync monitoring timed out, but sync may still be in progress")
            return False
            
        except Exception as e:
            logger.error(f"Error monitoring sync completion: {e}")
            return False