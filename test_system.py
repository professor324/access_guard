#!/usr/bin/env python3
"""
Test script for Access Guard system
"""

import os
import json
from scripts.github_collector import GitHubCollector
from scripts.diff_engine import DiffEngine
from scripts.slack_notifier import SlackNotifier

def test_github_connection():
    """Test GitHub connection"""
    print("🔗 Testing GitHub connection...")
    collector = GitHubCollector()
    user_info = collector.get_user_info()
    
    if user_info:
        print(f"✅ Connected as: {user_info['login']}")
        print(f"   Name: {user_info.get('name', 'N/A')}")
        print(f"   Email: {user_info.get('email', 'N/A')}")
        return True
    else:
        print("❌ Failed to connect to GitHub")
        return False

def test_slack_webhook():
    """Test Slack webhook"""
    print("\n🔗 Testing Slack webhook...")
    notifier = SlackNotifier()
    
    if notifier.validate_webhook():
        print("✅ Slack webhook URL format is valid")
        
        # Test with a simple message
        test_report = {
            "summary": {
                "total_sot_records": 4,
                "total_actuals_records": 1,
                "expired_count": 0,
                "extra_count": 1,
                "drift_found": True
            },
            "details": {
                "extra": [{"username": "testuser", "system": "github", "role": "collaborator"}],
                "expired": []
            }
        }
        
        success = notifier.send_report(test_report)
        if success:
            print("✅ Slack message sent successfully!")
        else:
            print("❌ Failed to send Slack message (check webhook URL)")
        
        return success
    else:
        print("❌ Slack webhook not configured properly")
        return False

def test_full_flow():
    """Test the complete flow"""
    print("\n🚀 Testing complete flow...")
    
    # Collect data
    collector = GitHubCollector()
    actuals = collector.collect_actuals()
    print(f"✅ Collected {len(actuals)} access records")
    
    # Check drift
    engine = DiffEngine()
    report = engine.generate_diff()
    print(f"✅ Drift check complete: {report['summary']['drift_found']}")
    
    # Save report
    with open('out/test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("📊 Report summary:")
    print(f"   - SoT records: {report['summary']['total_sot_records']}")
    print(f"   - Actual records: {report['summary']['total_actuals_records']}")
    print(f"   - Expired access: {report['summary']['expired_count']}")
    print(f"   - Extra access: {report['summary']['extra_count']}")
    
    return report

if __name__ == "__main__":
    print("🧪 Access Guard System Test")
    print("=" * 50)
    
    # Test individual components
    github_ok = test_github_connection()
    slack_ok = test_slack_webhook()
    
    if github_ok:
        report = test_full_flow()
        
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print(f"   GitHub: {'✅' if github_ok else '❌'}")
    print(f"   Slack: {'✅' if slack_ok else '❌'}")
    
    if github_ok:
        print("\n💡 Next steps:")
        print("   1. Check out/test_report.json for detailed results")
        print("   2. Review sot/access_matrix.csv to match your actual access")
        print("   3. Run: python main.py --nightly")
