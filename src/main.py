"""
Main orchestrator for PA Firewall Jenkins Automation

Handles step-by-step execution based on command line arguments.
Each step can be called independently by Jenkins stages.
"""

import argparse
import sys
import logging
import datetime
import os
from pathlib import Path

# Get project root and define log file path
def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

PROJECT_ROOT = get_project_root()
LOG_DIR = PROJECT_ROOT / "log"

# Create log file with date
date_str = datetime.datetime.now().strftime("%Y-%m-%d")
LOG_FILE = LOG_DIR / f"jenkins_pa_automation_{date_str}.log"

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',  # Append mode instead of overwrite
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Log to console for Jenkins
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

logger = logging.getLogger()

def main():
    """
    Main function to handle Jenkins step execution.
    """
    parser = argparse.ArgumentParser(description='PA Firewall Jenkins Automation')
    parser.add_argument('--step', required=True, help='Step to execute')
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting PA Automation - Log file: {LOG_FILE}")
        logger.info(f"Executing step: {args.step}")
        
        if args.step == 'api_keys':
            from steps.step_01_api_keys import Step01_APIKeys
            step = Step01_APIKeys()
            success = step.execute()

        elif args.step == 'discovery':
            from steps.step_00_discovery import Step00_Discovery
            step = Step00_Discovery()
            success = step.execute()
            
        elif args.step == 'ha_interfaces':
            from steps.step_02_ha_interfaces import Step02_HAInterfaces
            step = Step02_HAInterfaces()
            success = step.execute()
            
        elif args.step == 'ha_config':
            from steps.step_03_ha_config import Step03_HAConfig
            step = Step03_HAConfig()
            success = step.execute()
        elif args.step == 'identify_active':
            from steps.step_04_identify_active import Step04_IdentifyActive
            step = Step04_IdentifyActive()
            success = step.execute()
            
        # ... will add more as we create them
        
        else:
            logger.error(f"Unknown step: {args.step}")
            available_steps = ['api_keys', 'ha_interfaces', 'ha_config']
            logger.info(f"Available steps: {', '.join(available_steps)}")
            sys.exit(1)
        
        if success:
            logger.info(f"Step {args.step} completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Step {args.step} failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error executing step {args.step}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()