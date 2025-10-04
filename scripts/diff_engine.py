import pandas as pd
import json
from datetime import datetime
import logging
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

class DiffEngine:
    def _init_(self):
        self.drift_found = False
        self.drift_report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "details": {
                "extra": [],
                "missing": [],
                "wrong_role": [],
                "expired": []
            }
        }
    
    def load_sot(self, sot_path: str = "sot/access_matrix.csv") -> pd.DataFrame:
        """Load Source of Truth CSV"""
        try:
            sot = pd.read_csv(sot_path)
            sot['expires_on'] = pd.to_datetime(sot['expires_on'])
            logger.info(f"Loaded SoT with {len(sot)} records")
            return sot
        except Exception as e:
            logger.error(f"Error loading SoT: {e}")
            return pd.DataFrame()
    
    def load_actuals(self, actuals_path: str) -> List[Dict]:
        """Load actuals from JSON file"""
        try:
            with open(actuals_path, 'r') as f:
                actuals = json.load(f)
            logger.info(f"Loaded actuals with {len(actuals)} records")
            return actuals
        except Exception as e:
            logger.error(f"Error loading actuals: {e}")
            return []
    
    def check_expired(self, sot: pd.DataFrame) -> List[Dict]:
        """Check for expired access"""
        expired = []
        today = pd.Timestamp.now()
        
        for _, row in sot.iterrows():
            if pd.notna(row['expires_on']) and row['expires_on'] < today:
                expired.append({
                    "system": row['system'],
                    "username": row['username'],
                    "email": row['email'],
                    "role": row['role'],
                    "scope": row['scope'],
                    "expires_on": row['expires_on'].strftime('%Y-%m-%d'),
                    "reason": "Access expired"
                })
        
        return expired
    
    def find_extra_access(self, sot: pd.DataFrame, actuals: List[Dict]) -> List[Dict]:
        """Find access in actuals but not in SoT"""
        extra = []
        sot_usernames = set(sot['username'].str.lower())
        
        for actual in actuals:
            if actual['username'].lower() not in sot_usernames:
                extra.append({
                    "system": actual['system'],
                    "username": actual['username'],
                    "email": actual.get('email', ''),
                    "role": actual.get('role', 'unknown'),
                    "scope": actual.get('scope', []),
                    "reason": "User not found in SoT"
                })
        
        return extra
    
    def generate_diff(self, sot_path: str = "sot/access_matrix.csv", 
                     actuals_path: str = "out/github_actuals_latest.json"):
        """Generate diff report between SoT and actuals"""
        logger.info("Generating diff report...")
        
        sot = self.load_sot(sot_path)
        actuals = self.load_actuals(actuals_path)
        
        if sot.empty or not actuals:
            logger.error("SoT or actuals data is empty")
            return self.drift_report
        
        # Check for different types of drift
        expired = self.check_expired(sot)
        extra = self.find_extra_access(sot, actuals)
        
        # Update drift report
        self.drift_report['details']['expired'] = expired
        self.drift_report['details']['extra'] = extra
        
        # Summary statistics
        self.drift_report['summary'] = {
            "total_sot_records": len(sot),
            "total_actuals_records": len(actuals),
            "expired_count": len(expired),
            "extra_count": len(extra),
            "drift_found": len(expired) > 0 or len(extra) > 0
        }
        
        self.drift_found = self.drift_report['summary']['drift_found']
        
        if self.drift_found:
            logger.warning(f"Drift detected: {len(expired)} expired, {len(extra)} extra access")
        else:
            logger.info("No drift detected - access is clean!")
        
        return self.drift_report
    
    def save_diff_report(self, report: Dict, filename: str = None):
        """Save diff report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"out/diff_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Diff report saved to {filename}")
        return filename

def main():
    engine = DiffEngine()
    report = engine.generate_diff()
    engine.save_diff_report(report)

if _name_ == "_main_":
    main()