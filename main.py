import os
import logging
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Starting migration process...")

    # Initialize clients
    logging.info("Initializing Redmine and GitHub clients...")
    redmine = RedmineClient(
        url=REDMINE_URL,
        api_key=REDMINE_API_KEY
    )
    github = GitHubClient(
        repo=GITHUB_REPO,
        token=GITHUB_TOKEN
    )

    # Fetch issues from Redmine
    logging.info("Fetching issues from Redmine...")
    issues = redmine.get_issues()
    logging.info(f"Fetched {len(issues)} issues from Redmine.")

    # Migrate to GitHub
    for idx, issue in enumerate(issues, 1):
        logging.info(f"Migrating issue {idx}/{len(issues)}: Redmine ID #{issue.get('id', 'unknown')}")
        github.create_issue_from_redmine(issue)

    logging.info("Migration process completed.")

if __name__ == '__main__':
    main()