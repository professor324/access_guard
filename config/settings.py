import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_ORG = os.getenv('GITHUB_ORG', '')  # Leave empty for personal account
    
    # Cloudflare Configuration
    CLOUDFLARE_TOKEN = os.getenv('CLOUDFLARE_TOKEN')
    CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
    
    # MongoDB Configuration
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_DB = os.getenv('MONGO_DB', 'admin')
    
    # Slack Configuration
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    
    # App Configuration
    DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @property
    def has_github_org(self):
        return bool(self.GITHUB_ORG and self.GITHUB_ORG.strip())

settings = Settings()