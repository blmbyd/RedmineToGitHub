import requests
import logging

class RedmineClient:
    def __init__(self, url, api_key):
        self.url = url.rstrip('/')
        self.api_key = api_key

    def get_issues(self, limit=None, start_from=0):
        issues = []
        current_offset = 0
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
            
            # Filter issues based on start_from issue number
            filtered_issues = []
            for issue in data['issues']:
                issue_id = issue.get('id', 0)
                if start_from == 0 or issue_id >= start_from:
                    filtered_issues.append(issue)
            
            issues.extend(filtered_issues)
            total_fetched += len(filtered_issues)
            logging.info(f"Received {len(data['issues'])} issues, {len(filtered_issues)} after filtering (total so far: {len(issues)})")
            
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