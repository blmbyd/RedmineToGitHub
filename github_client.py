import requests
import logging
import base64
import mimetypes
import re
from typing import List, Dict, Optional

class GitHubClient:
    def __init__(self, repo, token, tracker_mapping=None, user_mapping=None):
        self.repo = repo
        self.token = token
        self.api_url = f"https://api.github.com/repos/{self.repo}"
        self._default_branch: Optional[str] = None
        # Cache of paths confirmed to exist in the repo during this runtime
        self._existing_paths = set()
        # Tracker to label mapping configuration
        self.tracker_mapping = tracker_mapping or {}
        # User mapping configuration
        self.user_mapping = user_mapping or {}

    def _headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github+json'
        }

    def _ensure_default_branch(self):
        if self._default_branch:
            return self._default_branch
        resp = requests.get(self.api_url, headers=self._headers())
        if resp.status_code == 200:
            self._default_branch = resp.json().get('default_branch', 'main')
        else:
            logging.warning(f"Could not determine default branch (status {resp.status_code}); assuming 'main'.")
            self._default_branch = 'main'
        return self._default_branch

    def _sanitize_filename(self, name: str) -> str:
        name = name.split('/')[-1].split('\\')[-1]
        name = re.sub(r'[^A-Za-z0-9._ -]+', '_', name)
        name = name.strip()
        return name or 'attachment'

    def _path_exists(self, path_in_repo: str) -> bool:
        """Return True if a file already exists at the given path in the repository.

        Uses GitHub contents API. Caches positive results for the life of the client
        to avoid duplicate network calls when the same path is checked multiple times.
        On unexpected HTTP status codes (non 200/404) it logs a warning and returns False
        so the caller will proceed to attempt an upload (safer default).
        """
        if path_in_repo in self._existing_paths:
            return True
        url = f"{self.api_url}/contents/{path_in_repo}"
        try:
            resp = requests.get(url, headers=self._headers())
        except Exception as e:
            logging.debug(f"Error checking existence of '{path_in_repo}': {e}; assuming not present")
            return False
        if resp.status_code == 200:
            self._existing_paths.add(path_in_repo)
            return True
        if resp.status_code == 404:
            return False
        logging.warning(f"Unexpected status {resp.status_code} checking existence of '{path_in_repo}'; proceeding to upload")
        return False

    def _upload_file(self, path_in_repo: str, content_bytes: bytes, commit_message: str):
        url = f"{self.api_url}/contents/{path_in_repo}"
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content_bytes).decode('utf-8')
        }
        resp = requests.put(url, headers=self._headers(), json=payload)
        if resp.status_code not in (200, 201):
            logging.error(f"Failed to upload file '{path_in_repo}': {resp.status_code} {resp.text}")
            resp.raise_for_status()
        return resp.json()

    def _build_attachment_markdown(self, uploaded_assets: List[Dict]) -> str:
        if not uploaded_assets:
            return ""
        lines = ["", "### Attachments"]
        for asset in uploaded_assets:
            if asset['is_image']:
                lines.append(f"![{asset['filename']}]({asset['raw_url']})")
            else:
                lines.append(f"[{asset['filename']}]({asset['raw_url']})")
        return "\n".join(lines) + "\n"

    def _get_labels_for_issue(self, issue) -> List[str]:
        """Get GitHub labels for a Redmine issue based on tracker mapping."""
        if not self.tracker_mapping:
            return []
        
        tracker = issue.get('tracker')
        if not tracker:
            return []
        
        # Try to match by tracker name (case-insensitive)
        tracker_name = tracker.get('name', '').strip()
        tracker_id = str(tracker.get('id', ''))
        
        labels = []
        
        # Check for exact name match (case-insensitive)
        for key, value in self.tracker_mapping.items():
            if key.lower() == tracker_name.lower() or key == tracker_id:
                if isinstance(value, str):
                    # Split comma-separated labels and strip whitespace
                    mapped_labels = [label.strip() for label in value.split(',') if label.strip()]
                    labels.extend(mapped_labels)
                break
        
        if labels:
            logging.info(f"Mapped tracker '{tracker_name}' (ID: {tracker_id}) to labels: {labels}")
        else:
            logging.debug(f"No mapping found for tracker '{tracker_name}' (ID: {tracker_id})")
        
        return labels

    def _get_github_username_for_redmine_user(self, redmine_user_name: str) -> str:
        """Map Redmine username to GitHub username with @ mention."""
        if not self.user_mapping or not redmine_user_name:
            return redmine_user_name
        
        # Try exact match first
        mapped_user = self.user_mapping.get(redmine_user_name)
        if mapped_user:
            # Ensure @ prefix for GitHub mentions
            return mapped_user if mapped_user.startswith('@') else f'@{mapped_user}'
        
        # Try case-insensitive match
        for redmine_name, github_user in self.user_mapping.items():
            if redmine_name.lower() == redmine_user_name.lower():
                return github_user if github_user.startswith('@') else f'@{github_user}'
        
        # No mapping found, return original
        return redmine_user_name

    def _map_users_in_text(self, text: str) -> str:
        """Replace Redmine usernames with GitHub mentions in text content."""
        if not self.user_mapping or not text:
            return text
        
        modified_text = text
        for redmine_user, github_user in self.user_mapping.items():
            # Ensure @ prefix
            github_mention = github_user if github_user.startswith('@') else f'@{github_user}'
            # Replace mentions in text (case-insensitive)
            modified_text = re.sub(
                rf'\b{re.escape(redmine_user)}\b', 
                github_mention, 
                modified_text, 
                flags=re.IGNORECASE
            )
        
        return modified_text

    def create_issue_from_redmine(self, issue, mirror_attachments=False, redmine_client=None):
        logging.info(f"Creating GitHub issue for Redmine issue #{issue.get('id', 'unknown')}")
        headers = self._headers()

        issue_id = issue.get('id', 'unknown')
        body = self._map_users_in_text(issue.get('description') or '')

        uploaded_assets = []
        if mirror_attachments and redmine_client:
            attachments = issue.get('attachments', []) or []
            if attachments:
                logging.info(f"Redmine issue #{issue_id}: processing {len(attachments)} attachment(s)")
            seen_filenames = set()
            for att in attachments:
                try:
                    content_bytes, filename, content_type = redmine_client.download_attachment(att)
                except Exception:
                    continue
                filename = self._sanitize_filename(filename)
                base, dot, ext = filename.rpartition('.')
                if not base:
                    base = filename
                    ext = ''
                    dot = ''
                original = filename
                counter = 1
                while filename in seen_filenames:
                    filename = f"{base}-{counter}{dot}{ext}" if ext else f"{base}-{counter}"
                    counter += 1
                seen_filenames.add(filename)

                path_in_repo = f"redmine_attachments/issue-{issue_id}/{filename}"
                commit_message = f"Add attachment {filename} from Redmine issue {issue_id}"
                try:
                    # Determine if this is an image early so we can optionally reuse an existing file
                    is_image = (content_type.startswith('image/')) or bool(mimetypes.guess_type(filename)[0] or '').startswith('image/')

                    # Path-based silent reuse for images: if the exact path already exists, skip upload
                    if is_image and self._path_exists(path_in_repo):
                        self._ensure_default_branch()
                        raw_url = f"https://github.com/{self.repo}/blob/{self._default_branch}/{path_in_repo}?raw=true"
                        uploaded_assets.append({
                            "filename": filename,
                            "raw_url": raw_url,
                            "is_image": True
                        })
                        logging.info(f"Reusing existing image '{filename}' at '{path_in_repo}' (skipping upload)")
                        continue

                    self._ensure_default_branch()  # ensure branch before constructing raw url after upload
                    self._upload_file(path_in_repo, content_bytes, commit_message)
                    raw_url = f"https://github.com/{self.repo}/blob/{self._default_branch}/{path_in_repo}?raw=true"
                    uploaded_assets.append({
                        "filename": filename,
                        "raw_url": raw_url,
                        "is_image": is_image
                    })
                    logging.info(f"Uploaded attachment '{filename}' to '{path_in_repo}'")
                except Exception as e:
                    logging.warning(f"Skipping attachment '{original}' due to upload failure: {e}")

        if uploaded_assets:
            body += self._build_attachment_markdown(uploaded_assets)

        if issue.get('author') and issue['author'].get('name'):
            author_name = issue['author']['name']
            author_info = f"\n\n---\n*Originally created by {author_name} in Redmine issue number {issue_id}*"
            body += author_info

        title = f"{issue['subject']} [Redmine-{issue_id}]"
        
        # Get labels based on tracker mapping
        labels = self._get_labels_for_issue(issue)
        
        # Get assignee from Redmine and map to GitHub username
        assignee = None
        if issue.get('assigned_to') and issue['assigned_to'].get('name'):
            assignee_name = issue['assigned_to']['name']
            mapped_assignee = self._get_github_username_for_redmine_user(assignee_name)
            # Remove @ prefix for GitHub API assignee field
            if mapped_assignee.startswith('@'):
                assignee = mapped_assignee[1:]
            elif mapped_assignee != assignee_name:  # Only if mapping was found
                assignee = mapped_assignee
            
            if assignee:
                logging.info(f"Mapping assignee '{assignee_name}' to GitHub user '{assignee}'")
        
        data = {'title': title, 'body': body}
        if labels:
            data['labels'] = labels
            logging.info(f"Creating GitHub issue with labels: {labels}")
        if assignee:
            data['assignees'] = [assignee]
            logging.info(f"Assigning GitHub issue to: {assignee}")
        
        resp = requests.post(f"{self.api_url}/issues", headers=headers, json=data)
        if resp.status_code == 201:
            issue_number = resp.json().get('number')
            logging.info(f"Successfully created GitHub issue #{issue_number} for Redmine issue #{issue_id}")
            # --- Add Redmine notes as GitHub comments ---
            notes = issue.get('journals', []) or []
            for note in notes:
                note_text = note.get('notes') or ''
                if not note_text.strip():
                    continue
                author = note.get('user', {}).get('name') or note.get('author', {}).get('name') or 'Unknown'
                created_on = note.get('created_on') or note.get('createdAt') or ''
                mapped_author = self._get_github_username_for_redmine_user(author)
                comment_body = self._map_users_in_text(note_text)
                # Optionally add author/timestamp metadata
                meta = []
                if mapped_author:
                    meta.append(f"*By {mapped_author}*")
                if created_on:
                    meta.append(f"*Created on {created_on}*")
                if meta:
                    comment_body += "\n\n---\n" + " ".join(meta)
                comment_data = {'body': comment_body}
                comment_url = f"{self.api_url}/issues/{issue_number}/comments"
                try:
                    comment_resp = requests.post(comment_url, headers=headers, json=comment_data)
                    if comment_resp.status_code == 201:
                        logging.info(f"Added comment for Redmine note to GitHub issue #{issue_number}")
                    else:
                        logging.warning(f"Failed to add comment for Redmine note to GitHub issue #{issue_number}: {comment_resp.status_code} {comment_resp.text}")
                except Exception as e:
                    logging.warning(f"Exception posting comment for Redmine note: {e}")
        else:
            logging.error(f"Failed to create GitHub issue for Redmine issue #{issue_id}: {resp.status_code} {resp.text}")
        resp.raise_for_status()
        return resp.json()
