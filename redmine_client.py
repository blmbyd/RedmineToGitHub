import requests

class RedmineClient:
    def __init__(self, url, api_key):
        self.url = url.rstrip('/')
        self.api_key = api_key

    def get_issues(self):
        issues = []
        offset = 0
        limit = 100
        while True:
            params = {
                'key': self.api_key,
                'limit': limit,
                'offset': offset
            }
            resp = requests.get(f"{self.url}/issues.json", params=params)
            resp.raise_for_status()
            data = resp.json()
            issues.extend(data['issues'])
            if offset + limit >= data['total_count']:
                break
            offset += limit
        return issues