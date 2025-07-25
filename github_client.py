import requests
import logging

class GitHubClient:
    def __init__(self, repo, token):
        self.repo = repo
        self.token = token
        self.api_url = f"https://api.github.com/repos/{self.repo}"

    def create_issue_from_redmine(self, issue):
        logging.info(f"Creating GitHub issue for Redmine issue #{issue.get('id', 'unknown')}")
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github+json'
        }
        title = issue['subject']
        body = issue['description'] or ''
        
        # Add author information from Redmine
        if issue.get('author') and issue['author'].get('name'):
            author_name = issue['author']['name']
            issue_id = issue.get('id', '')
            
            # Build the footer with email and issue number
            author_info = f"\n\n---\n*Originally created by {author_name} in Redmine issue number {issue_id}*"
            
            body += author_info
        
        # You may want to enrich the body with Redmine data (e.g., status, custom fields)
        data = {
            'title': title,
            'body': body
        }
        resp = requests.post(f"{self.api_url}/issues", headers=headers, json=data)
        if resp.status_code == 201:
            issue_number = resp.json().get('number')
            logging.info(f"Successfully created GitHub issue #{issue_number} for Redmine issue #{issue.get('id', 'unknown')}")
        else:
            logging.error(f"Failed to create GitHub issue for Redmine issue #{issue.get('id', 'unknown')}: {resp.status_code} {resp.text}")
        resp.raise_for_status()
        return resp.json()
