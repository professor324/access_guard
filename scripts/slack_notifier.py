import requests
import json
import logging
from datetime import datetime
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

class SlackNotifier:
    def _init_(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL
    
    def validate_webhook(self):
        """Validate Slack webhook URL"""
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        # Check if it's a valid Slack webhook format
        if not self.webhook_url.startswith('https://hooks.slack.com/services/'):
            logger.error("Invalid Slack webhook format. Should start with: https://hooks.slack.com/services/")
            return False
        
        return True
    
    def create_slack_message(self, diff_report: dict) -> dict:
        """Create Slack message from diff report"""
        summary = diff_report.get('summary', {})
        details = diff_report.get('details', {})
        
        expired_count = len(details.get('expired', []))
        extra_count = len(details.get('extra', []))
        
        # Message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔍 Access Guard - Daily Drift Report"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"Total SoT Records:\n{summary.get('total_sot_records', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"Total Actual Records:\n{summary.get('total_actuals_records', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"Expired Access:\n{expired_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"Extra Access:\n{extra_count}"
                    }
                ]
            }
        ]
        
        # Add status indicator
        if expired_count == 0 and extra_count == 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ All access is clean! No drift detected."
                }
            })
        else:
            blocks.append({
                "type": "section", 
                "text": {
                    "type": "mrkdwn",
                    "text": "⚠ Access drift detected! Review the details below."
                }
            })
        
        # Add expired access section
        if expired_count > 0:
            expired_text = "\n".join([
                f"• {item['username']} ({item['system']}) - Expired: {item['expires_on']}"
                for item in details.get('expired', [])[:5]  # Show first 5
            ])
            if expired_count > 5:
                expired_text += f"\n• ... and {expired_count - 5} more"
                
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 Expired Access:\n{expired_text}"
                }
            })
        
        # Add extra access section
        if extra_count > 0:
            extra_text = "\n".join([
                f"• {item['username']} ({item['system']}) - Role: {item['role']}"
                for item in details.get('extra', [])[:5]  # Show first 5
            ])
            if extra_count > 5:
                extra_text += f"\n• ... and {extra_count - 5} more"
                
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠ Extra Access:\n{extra_text}"
                }
            })
        
        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dry Run: {settings.DRY_RUN}"
                }
            ]
        })
        
        return {"blocks": blocks}
    
    def send_report(self, diff_report: dict) -> bool:
        """Send diff report to Slack"""
        if not self.validate_webhook():
            return False
        
        try:
            message = self.create_slack_message(diff_report)
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Slack message sent successfully")
                return True
            else:
                logger.error(f"❌ Failed to send Slack message: {response.status_code} - {response.text}")
                # Print the message for manual testing
                print("\n=== SLACK MESSAGE (for manual testing) ===")
                print(json.dumps(message, indent=2))
                print("========================================\n")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Slack request timeout")
            return False
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return False

def main():
    notifier = SlackNotifier()
    
    # Load a sample diff report
    try:
        with open('out/diff_report_latest.json', 'r') as f:
            diff_report = json.load(f)
        notifier.send_report(diff_report)
    except FileNotFoundError:
        logger.error("No diff report found. Run diff engine first.")

if _name_ == "_main_":
    main()