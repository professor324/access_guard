import requests
import pandas as pd
from datetime import datetime
import json
import logging
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

class GitHubCollector:
    def _init_(self):
        self.headers = {
            'Authorization': f'token {settings.ACCOUNT_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
    
    def get_user_info(self):
        """Get authenticated user information"""
        try:
            response = requests.get(f'{self.base_url}/user', headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def get_user_repos(self, username=None):
        """Get user repositories - for personal account"""
        try:
            if username:
                url = f'{self.base_url}/users/{username}/repos'
            else:
                url = f'{self.base_url}/user/repos'
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            repos = response.json()
            
            logger.info(f"Found {len(repos)} repositories for user")
            return repos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting repos: {e}")
            return []
    
    def get_collaborators(self, owner, repo):
        """Get collaborators for a specific repository"""
        try:
            url = f'{self.base_url}/repos/{owner}/{repo}/collaborators'
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Can't access collaborators for {repo}: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error getting collaborators for {repo}: {e}")
            return []
    
    def collect_actuals(self):
        """Collect actual access data from GitHub"""
        logger.info("Starting GitHub data collection...")
        
        actuals = []
        user_info = self.get_user_info()
        
        if not user_info:
            logger.error("Failed to get user info - check GITHUB_TOKEN")
            return actuals
        
        # Get current user's repositories
        repos = self.get_user_repos()
        
        # Add current user data
        user_data = {
            "system": "github",
            "username": user_info['login'],
            "email": user_info.get('email', ''),
            "role": "owner",
            "scope": [f"repos:{'|'.join([repo['name'] for repo in repos])}"],
            "collected_at": datetime.now().isoformat(),
            "source": {"raw": user_info}
        }
        actuals.append(user_data)
        logger.info(f"Collected data for user: {user_info['login']}")
        
        # Collect collaborators from each repository
        for repo in repos:
            collaborators = self.get_collaborators(user_info['login'], repo['name'])
            
            for collaborator in collaborators:
                # Skip the owner (already added)
                if collaborator['login'] == user_info['login']:
                    continue
                
                collaborator_data = {
                    "system": "github",
                    "username": collaborator['login'],
                    "email": collaborator.get('email', ''),
                    "role": collaborator.get('role', 'collaborator'),
                    "scope": [f"repos:{repo['name']}"],
                    "collected_at": datetime.now().isoformat(),
                    "source": {"raw": collaborator}
                }
                actuals.append(collaborator_data)
                logger.info(f"Found collaborator: {collaborator['login']} on {repo['name']}")
        
        logger.info(f"Collection complete: {len(actuals)} total access records")
        return actuals
    
    def save_actuals(self, actuals, filename=None):
        """Save collected data to JSON file"""
        if not filename:
            filename = "out/github_actuals_latest.json"
        
        with open(filename, 'w') as f:
            json.dump(actuals, f, indent=2)
        
        logger.info(f"GitHub actuals saved to {filename}")
        return filename

def main():
    collector = GitHubCollector()
    actuals = collector.collect_actuals()
    collector.save_actuals(actuals)

if _name_ == "_main_":

    main()
