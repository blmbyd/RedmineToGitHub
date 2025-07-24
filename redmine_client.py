import requests
import logging

class RedmineClient:
    def __init__(self, url, api_key):
        self.url = url.rstrip('/')
        self.api_key = api_key

    def get_issues(self, limit=None, offset=0):
        issues = []
        current_offset = offset
        batch_limit = 100  # Redmine API limit per request
        total_fetched = 0
        
        while True:
            # If we have a limit, adjust the batch size for the last request
            if limit and total_fetched + batch_limit > limit:
                batch_limit = limit - total_fetched
            
            params = {
                'key': self.api_key,
                'limit': batch_limit,
                'offset': current_offset
            }
            logging.info(f"Requesting Redmine issues: offset={current_offset}, limit={batch_limit}")
            resp = requests.get(f"{self.url}/issues.json", params=params, verify=False)
            resp.raise_for_status()
            data = resp.json()
            issues.extend(data['issues'])
            total_fetched += len(data['issues'])
            logging.info(f"Received {len(data['issues'])} issues (total so far: {len(issues)})")
            
            # Stop if we've reached our limit
            if limit and total_fetched >= limit:
                break
                
            # Stop if we've reached the end of available issues
            if current_offset + batch_limit >= data['total_count']:
                break
                
            # Stop if this batch returned fewer issues than expected (end of data)
            if len(data['issues']) < batch_limit:
                break
                
            current_offset += batch_limit
            
        return issues