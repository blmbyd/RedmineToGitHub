# Redmine to GitHub Issues Migrator

A basic Python project to migrate issues from Redmine to GitHub Issues.

## Usage

1. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

2. Edit `config.yaml` with your credentials and repo info.

3. Run:

    ```
    python main.py
    ```

## Notes

- The script currently migrates basic issue fields (title, description).
- Extend `create_issue_from_redmine` to map other fields: assignees, labels, comments, etc.
- Paging is supported for Redmine issues.

**Use at your own risk! Consider running on a test repo first.**