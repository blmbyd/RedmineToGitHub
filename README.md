# Redmine to GitHub Issues Migrator

A basic Python project to migrate issues from Redmine to GitHub Issues.

## Configuration

This project uses a `.env` file to store sensitive configuration such as API keys and tokens.  
**Do not commit your `.env` file to version control.**

### Steps

1. **Copy the example below and create a `.env` file in the project root:**

    ```
    REDMINE_URL=https://your-redmine-url
    REDMINE_API_KEY=your-redmine-api-key
    GITHUB_REPO=your-github-username/your-repo
    GITHUB_TOKEN=your-github-token
    ```

2. **Install dependencies:**

    ```
    pip install -r requirements.txt
    ```

3. **Run the migration:**

    ```
    python main.py
    ```

    **Optional parameters:**
    
    - `--limit N`: Migrate only the first N issues
    - `--start-from N`: Start migration from issue number N (default: 0 = start from beginning)
    
    **Examples:**
    
    ```bash
    # Migrate all issues (default behavior)
    python main.py
    
    # Migrate only the first 10 issues
    python main.py --limit 10
    
    # Start from issue #50 and migrate the next 20 issues
    python main.py --start-from 50 --limit 20
    
    # Start from issue #100 and migrate all remaining issues
    python main.py --start-from 100
    ```

### Notes

- The `.env` file is loaded automatically by the application using [python-dotenv](https://pypi.org/project/python-dotenv/).
- Make sure `.env` is listed in `.gitignore`.
- Do not store sensitive data in `config.yaml` or any other tracked file.
