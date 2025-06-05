import yaml
from redmine_client import RedmineClient
from github_client import GitHubClient

def main():
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize clients
    redmine = RedmineClient(
        url=config['redmine']['url'],
        api_key=config['redmine']['api_key']
    )
    github = GitHubClient(
        repo=config['github']['repo'],
        token=config['github']['token']
    )

    # Fetch issues from Redmine
    issues = redmine.get_issues()

    # Migrate to GitHub
    for issue in issues:
        github.create_issue_from_redmine(issue)

if __name__ == '__main__':
    main()