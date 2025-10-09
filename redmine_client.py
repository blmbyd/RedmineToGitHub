import requests
import logging
from typing import Optional

class RedmineClient:
    def __init__(self, url, api_key):
        self.url = url.rstrip('/')
        self.api_key = api_key

    def get_issues(self, limit: Optional[int] = None, start_from: int = 0, include_attachments: bool = False):
        issues = []
        current_offset = 0
        batch_limit = 100  # Always fetch 100 items per request

        while True:
            params = {
                'key': self.api_key,
                'limit': batch_limit,
                'offset': current_offset,
                'sort': 'id:asc'
            }
            if include_attachments:
                params['include'] = 'attachments'
            logging.info(f"Requesting Redmine issues: offset={current_offset}, limit={batch_limit}")
            resp = requests.get(f"{self.url}/issues.json", params=params, verify=False)
            resp.raise_for_status()
            data = resp.json()

            # Filter issues based on start_from issue number
            filtered_issues = []
            for issue in data['issues']:
                issue_id = issue.get('id', 0)
                if start_from == 0 or issue_id >= start_from:
                    # Fetch journals for this issue
                    try:
                        detail_url = f"{self.url}/issues/{issue_id}.json"
                        detail_params = {'key': self.api_key, 'include': 'journals'}
                        detail_resp = requests.get(detail_url, params=detail_params, verify=False)
                        detail_resp.raise_for_status()
                        detail_data = detail_resp.json()
                        if 'issue' in detail_data and 'journals' in detail_data['issue']:
                            issue['journals'] = detail_data['issue']['journals']
                        else:
                            issue['journals'] = []
                    except Exception as e:
                        logging.warning(f"Failed to fetch journals for issue {issue_id}: {e}")
                        issue['journals'] = []
                    filtered_issues.append(issue)

            issues.extend(filtered_issues)
            logging.info(f"Received {len(data['issues'])} issues, {len(filtered_issues)} after filtering (total so far: {len(issues)})")

            # Early stop if limit reached
            if limit and len(issues) >= limit:
                logging.info(f"Reached requested issue limit ({limit}); stopping pagination early.")
                break

            # Stop if we've reached the end of available issues
            if current_offset + batch_limit >= data['total_count']:
                break

            # Stop if this batch returned fewer issues than expected (end of data)
            if len(data['issues']) < batch_limit:
                break

            current_offset += batch_limit

        # Ensure correct order and apply limit
        issues.sort(key=lambda x: x.get('id', 0))
        if limit:
            issues = issues[:limit]

        return issues
    
    def download_attachment(self, attachment):
        """Download a single attachment. Returns (bytes, filename, content_type) or raises."""
        attachment_id = attachment.get('id')
        filename = attachment.get('filename') or f"attachment-{attachment_id}"
        content_type = attachment.get('content_type') or 'application/octet-stream'

        content_url = attachment.get('content_url')
        if not content_url:
            content_url = f"{self.url}/attachments/download/{attachment_id}/{filename}"

        if 'key=' not in content_url:
            sep = '&' if '?' in content_url else '?'
            content_url = f"{content_url}{sep}key={self.api_key}"

        try:
            logging.info(f"Downloading attachment {attachment_id} ({filename})")
            resp = requests.get(content_url, verify=False, timeout=60)
            resp.raise_for_status()
            return resp.content, filename, content_type
        except Exception as e:
            logging.warning(f"Failed to download attachment {attachment_id} ({filename}): {e}")
            raise
