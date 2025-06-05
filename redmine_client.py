import requests
import logging

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
            logging.info(f"Requesting Redmine issues: offset={offset}, limit={limit}")
            resp = requests.get(f"{self.url}/issues.json", params=params, verify=False)
            resp.raise_for_status()
            data = resp.json()
            issues.extend(data['issues'])
            logging.info(f"Received {len(data['issues'])} issues (total so far: {len(issues)})")
            if offset + limit >= data['total_count']:
                break
            offset += limit
        return issues