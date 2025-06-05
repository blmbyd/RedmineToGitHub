import requests

class GitHubClient:
    def __init__(self, repo, token):
        self.repo = repo
        self.token = token
        self.api_url = f"https://api.github.com/repos/{self.repo}"

    def create_issue_from_redmine(self, issue):
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github+json'
        }
        title = issue['subject']
        body = issue['description'] or ''
        # You may want to enrich the body with Redmine data (e.g., status, custom fields)
        data = {
            'title': title,
            'body': body
        }
        resp = requests.post(f"{self.api_url}/issues", headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()