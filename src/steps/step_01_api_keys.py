"""
Step 1: API Key Generation for PA Firewalls

Generates API keys for multiple Palo Alto firewall devices using credentials
provided through Jenkins form parameters. This step authenticates with each
firewall device and creates the necessary API keys for subsequent automation
steps. The generated keys are saved to a pickle file for use by other steps.

Key Features:
- Dynamic credential loading from Jenkins environment variables
- Multi-device API key generation with error handling
- Saves API keys and credentials for downstream automation steps
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

class Step01_APIKeys:
    """
    Generate API keys for all PA firewall devices.
    
    Uses credentials and firewall hosts from Jenkins form parameters.
    """
    
    def __init__(self):
        """
        Initialize API key generation step.
        """
        self.rest_api_headers = {
            "Content-Type": "application/json",
        }
    
    def _get_credentials_from_jenkins(self):
        """
        Get firewall credentials from Jenkins environment variables.
        
        Returns:
            list: List of firewall credentials
        """
        try:
            # Get credentials from Jenkins form parameters
            username = os.getenv('USERNAME')
            password = os.getenv('PASSWORD')
            firewall_hosts = os.getenv('FIREWALL_HOSTS')
            
            if not username or not password or not firewall_hosts:
                raise Exception("USERNAME, PASSWORD, and FIREWALL_HOSTS must be specified in Jenkins form")
            
            # Parse firewall hosts
            hosts = [host.strip() for host in firewall_hosts.split(',')]
            
            # Create credentials list
            pa_credentials = []
            for host in hosts:
                pa_credentials.append({
                    'host': host,
                    'username': username,
                    'password': password
                })
            
            logger.info(f"Loaded credentials for {len(pa_credentials)} firewalls from Jenkins parameters")
            logger.info(f"Firewall hosts: {[cred['host'] for cred in pa_credentials]}")
            logger.info(f"Username: {username}")
            
            return pa_credentials
            
        except Exception as e:
            logger.error(f"Error getting credentials from Jenkins: {e}")
            raise
    
    def execute(self):
        """
        Execute API key generation for all devices.
        Uses credentials from Jenkins form parameters.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get credentials from Jenkins form parameters
            pa_credentials = self._get_credentials_from_jenkins()
            
            # Initialize lists 
            rest_api_keys_list = []
            api_keys_list = []
            
            logger.info(f"Generating API keys for {len(pa_credentials)} devices")
            
            
            for device in pa_credentials:
                try:
                    # API key request URL
                    get_api_keys = f"https://{device['host']}/api/?type=keygen&user={device['username']}&password={device['password']}"

                    logger.info(f"Requesting API key for {device['host']} with user {device['username']}")
                    
                    response_api_key = requests.get(get_api_keys, headers=self.rest_api_headers, verify=False, timeout=30)
                    
                    if response_api_key.status_code == 200:
                        # Parse the XML response
                        xml_response = response_api_key.text
                        logger.info(f"API key response for {device['host']}: {xml_response}")
                        
                        # Check if response contains an error
                        if "<key>" in xml_response and "</key>" in xml_response:
                            PA_api_key = xml_response.split("<key>")[1].split("</key>")[0]
                            
                            rest_headers = {
                                "Content-Type": "application/json",
                                "X-PAN-KEY": PA_api_key
                            }
                            xml_headers = {
                                "Content-Type": "application/xml",
                                "X-PAN-KEY": PA_api_key
                            }
                            rest_api_keys_list.append(rest_headers)
                            api_keys_list.append(xml_headers)
                            
                            logger.info(f"API key generated successfully for {device['host']}")
                        else:
                            logger.error(f"No API key found in response for {device['host']}: {xml_response}")
                            return False

                    else:
                        logger.error(f"Failed to get API key for {device['host']}. Status code: {response_api_key.status_code}")
                        logger.error(f"Response text: {response_api_key.text}")
                        return False
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error occurred while making API request to {device['host']}: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error processing {device['host']}: {e}")
                    return False
            
            # Save to simple file for next steps to use
            api_data = {
                'rest_api_keys_list': rest_api_keys_list,
                'api_keys_list': api_keys_list,
                'pa_credentials': pa_credentials
            }
            
            with open('api_keys_data.pkl', 'wb') as f:
                pickle.dump(api_data, f)
            
            logger.info(f"Successfully generated and saved API keys for {len(api_keys_list)} devices")
            logger.info(f"API keys saved to api_keys_data.pkl")
            
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in API key generation: {e}")
            return False