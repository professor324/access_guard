#!/usr/bin/env python3
"""
ArSa Nexus - Access Guard Main Entry Point
Professional Access Hygiene & JML Automation
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from scripts.github_collector import GitHubCollector
from scripts.diff_engine import DiffEngine
from scripts.slack_notifier import SlackNotifier
from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/access_guard.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(_name_)

class AccessGuard:
    def _init_(self):
        self.github_collector = GitHubCollector()
        self.diff_engine = DiffEngine()
        self.slack_notifier = SlackNotifier()
    
    def collect_data(self):
        """Collect data from all systems"""
        logger.info("Starting data collection...")
        
        # Collect from GitHub
        github_actuals = self.github_collector.collect_actuals()
        self.github_collector.save_actuals(github_actuals, "out/github_actuals_latest.json")
        
        logger.info("Data collection completed")
    
    def check_drift(self):
        """Check for access drift"""
        logger.info("Checking for access drift...")
        
        report = self.diff_engine.generate_diff()
        self.diff_engine.save_diff_report(report, "out/diff_report_latest.json")
        
        if report['summary'].get('drift_found', False):
            logger.warning("Access drift detected!")
        else:
            logger.info("No access drift found")
        
        return report
    
    def send_report(self, report):
        """Send report to Slack"""
        logger.info("Sending report to Slack...")
        success = self.slack_notifier.send_report(report)
        
        if success:
            logger.info("Report sent successfully")
        else:
            logger.error("Failed to send report")
        
        return success
    
    def run_nightly(self):
        """Run nightly collection and reporting"""
        logger.info("Starting nightly access guard run...")
        
        try:
            # Step 1: Collect data
            self.collect_data()
            
            # Step 2: Check drift
            report = self.check_drift()
            
            # Step 3: Send report
            if settings.SLACK_WEBHOOK_URL:
                self.send_report(report)
            else:
                logger.info("Slack webhook not configured - skipping notification")
            
            logger.info("Nightly run completed successfully")
            
        except Exception as e:
            logger.error(f"Nightly run failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='ArSa Nexus Access Guard')
    parser.add_argument('--collect', action='store_true', help='Collect access data')
    parser.add_argument('--diff', action='store_true', help='Check for access drift')
    parser.add_argument('--report', action='store_true', help='Send report to Slack')
    parser.add_argument('--nightly', action='store_true', help='Run full nightly process')
    
    args = parser.parse_args()
    
    # Create necessary directories
    Path("out").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    guard = AccessGuard()
    
    if args.collect:
        guard.collect_data()
    elif args.diff:
        guard.check_drift()
    elif args.report:
        report = json.load(open('out/diff_report_latest.json'))
        guard.send_report(report)
    elif args.nightly:
        guard.run_nightly()
    else:
        parser.print_help()

if _name_ == "_main_":
    main()