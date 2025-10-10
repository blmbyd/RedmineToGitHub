import os
import json
import logging
import argparse
from dotenv import load_dotenv
from redmine_client import RedmineClient
from github_client import GitHubClient

# Load environment variables from .env file
load_dotenv()

# Read configuration from environment variables
REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Migrate issues from Redmine to GitHub')
    parser.add_argument('--limit', type=int, help='Maximum number of issues to migrate')
    parser.add_argument('--start-from', type=int, default=0, help='Issue number to start migration from (default: 0 = start from beginning)')
    parser.add_argument('--attachments', choices=['mirror','none'], help='Attachment handling mode (default: mirror). "mirror" uploads attachments into the GitHub repo; "none" skips them.')
    parser.add_argument('--tracker-mapping', type=str, help='Path to tracker mapping JSON file (default: tracker_mapping.json)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    
    if args.limit:
        logging.info(f"Starting migration process with limit={args.limit}, start_from={args.start_from}...")
    else:
        logging.info(f"Starting migration process (all issues from #{args.start_from})..." if args.start_from > 0 else "Starting migration process (all issues)...")

    # Determine attachments mode (CLI overrides env)
    attachments_mode = args.attachments or os.getenv('ATTACHMENTS_MODE', 'mirror')
    if attachments_mode not in ('mirror','none'):
        logging.warning(f"Invalid ATTACHMENTS_MODE '{attachments_mode}' specified; falling back to 'mirror'.")
        attachments_mode = 'mirror'
    mirror_attachments = (attachments_mode == 'mirror')
    logging.info(f"Attachments mode: {attachments_mode}")

    # Load tracker mapping configuration
    tracker_mapping_file = args.tracker_mapping or os.getenv('TRACKER_MAPPING_FILE', 'tracker_mapping.json')
    tracker_mapping = {}
    
    if os.path.exists(tracker_mapping_file):
        try:
            with open(tracker_mapping_file, 'r', encoding='utf-8') as f:
                tracker_mapping = json.load(f)
            logging.info(f"Loaded tracker mapping from '{tracker_mapping_file}' with {len(tracker_mapping)} mappings")
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in tracker mapping file '{tracker_mapping_file}': {e}")
            return
        except Exception as e:
            logging.error(f"Failed to load tracker mapping file '{tracker_mapping_file}': {e}")
            return
    else:
        logging.info(f"Tracker mapping file '{tracker_mapping_file}' not found. Issues will be created without tracker-based labels.")

    # Initialize clients
    logging.info("Initializing Redmine and GitHub clients...")
    redmine = RedmineClient(
        url=REDMINE_URL,
        api_key=REDMINE_API_KEY
    )
    github = GitHubClient(
        repo=GITHUB_REPO,
        token=GITHUB_TOKEN,
        tracker_mapping=tracker_mapping
    )

    # Fetch issues from Redmine
    logging.info("Fetching issues from Redmine...")
    issues = redmine.get_issues(limit=args.limit, start_from=args.start_from, include_attachments=mirror_attachments)
    logging.info(f"Fetched {len(issues)} issues from Redmine.")

    # Migrate to GitHub
    if issues:
        logging.info(f"Migration will process issues from ID #{issues[0].get('id', 'unknown')} to #{issues[-1].get('id', 'unknown')}")
    
    for idx, issue in enumerate(issues, 1):
        issue_id = issue.get('id', 'unknown')
        logging.info(f"Migrating issue {idx}/{len(issues)}: Redmine ID #{issue_id}")
    github.create_issue_from_redmine(issue, mirror_attachments=mirror_attachments, redmine_client=redmine)

    logging.info("Migration process completed.")

if __name__ == '__main__':
    main()