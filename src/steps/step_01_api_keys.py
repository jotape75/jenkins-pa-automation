"""
Step 1: API Key Generation for PA Firewalls

Extracts the get_api_key logic from PaloAltoFirewall_HA class
and adapts it for Jenkins execution without state manager.
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
    
    Direct extraction from PaloAltoFirewall_HA.get_api_key() method.
    """
    
    def __init__(self):
        """
        Initialize API key generation step.
        """
        self.rest_api_headers = {
            "Content-Type": "application/json",
        }
    
    def execute(self):
        """
        Execute API key generation for all devices.
        Uses the exact logic from your original get_api_key() method.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load configuration directly using constants - fix the import
            from utils_pa import PA_CREDS_FILE
            
            with open(PA_CREDS_FILE, 'r') as f:
                pa_credentials = json.load(f)
            
            # Initialize lists (from your original __init__)
            rest_api_keys_list = []
            api_keys_list = []
            
            logger.info(f"Generating API keys for {len(pa_credentials)} devices")
            
            # Your exact original logic from get_api_key()
            for device in pa_credentials:
                try:
                    # API key request URL
                    get_api_keys = f"https://{device['host']}/api/?type=keygen&user={device['username']}&password={device['password']}"

                    response_api_key = requests.get(get_api_keys, headers=self.rest_api_headers, verify=False)
                    if response_api_key.status_code == 200:
                        # Parse the XML response
                        xml_response = response_api_key.text
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
                        
                        logger.info(f"API key generated for {device['host']}")

                    else:
                        logger.error(f"Failed to get API key. Status code: {response_api_key.status_code}")
                        return False
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error occurred while making the API request: {e}")
                    return False
            
            # Save to simple file for next steps to use
            api_data = {
                'rest_api_keys_list': rest_api_keys_list,
                'api_keys_list': api_keys_list,
                'pa_credentials': pa_credentials
            }
            
            with open('api_keys_data.pkl', 'wb') as f:
                pickle.dump(api_data, f)
            
            logger.info(f"Successfully generated API keys for {len(api_keys_list)} devices")
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error in API key generation: {e}")
            return False