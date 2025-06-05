import yaml
import logging
from redmine_client import RedmineClient
from github_client import GitHubClient

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    logging.info("Starting migration process...")

    # Load config
    logging.info("Loading configuration...")
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize clients
    logging.info("Initializing Redmine and GitHub clients...")
    redmine = RedmineClient(
        url=config['redmine']['url'],
        api_key=config['redmine']['api_key']
    )
    github = GitHubClient(
        repo=config['github']['repo'],
        token=config['github']['token']
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