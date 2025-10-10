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

## Attachments

By default, the migrator mirrors Redmine issue attachments into the target GitHub repository so they remain accessible even if Redmine is retired.

Behavior:

- Files are uploaded under `redmine_attachments/issue-<redmine_issue_id>/` in the repository via the GitHub Contents API.
- Image files (detected via MIME type or extension) are embedded directly in the created GitHub issue with Markdown image syntax.
- Non-image files are added as links.
- If an attachment upload fails, it is skipped and processing continues.

Disable attachment migration:

```powershell
python main.py --attachments none
```

Environment variable alternative (overridden by CLI):

```
ATTACHMENTS_MODE=none
```

Limitations:

- Very large files may exceed GitHub REST API limits and be skipped.
- Filenames that collide within the same issue get a numeric suffix (`-1`, `-2`, ...).

Security note: Attachments are stored in the repository history. Remove sensitive artifacts from Redmine before migration if they should not become part of Git version history.

## Tracker to Label Mapping

The migrator can automatically map Redmine tracker types to GitHub labels during migration.

### Configuration

Create a `tracker_mapping.json` file in the project root with tracker-to-label mappings:

```json
{
  "Bug": "bug",
  "Feature": "enhancement",
  "Task": "task",
  "Support": "question",
  "Improvement": "enhancement",
  "New Feature": "enhancement",
  "Defect": "bug",
  "Story": "feature",
  "Epic": "epic"
}
```

### Usage

The mapping file is loaded automatically from `tracker_mapping.json`. You can override this:

**Command line:**
```powershell
python main.py --tracker-mapping path/to/custom_mapping.json
```

**Environment variable:**
```
TRACKER_MAPPING_FILE=path/to/custom_mapping.json
```

### Mapping Rules

- **By Name**: Match tracker names (case-insensitive): `"Bug": "bug"`
- **By ID**: Match tracker IDs numerically: `"1": "bug"`
- **Multiple Labels**: Use comma-separated values: `"Bug": "bug,critical"`
- **Missing File**: Migration continues without tracker-based labels (warning logged)
- **No Match**: Issues created without tracker labels (no error)

### Examples

```powershell
# Use default tracker_mapping.json
python main.py

# Use custom mapping file
python main.py --tracker-mapping config/my_tracker_mapping.json

# Combine with other options
python main.py --limit 50 --tracker-mapping custom_mapping.json --attachments none
```

## User Mapping

The migrator can automatically map Redmine usernames to GitHub usernames, creating proper @mentions for notifications and attribution.

### Configuration

Create a `user_mapping.json` file in the project root with username mappings:

```json
{
  "john.doe": "@johndoe",
  "jane.smith": "janesmith",
  "admin": "@admin-user",
  "Mike Wilson": "@mikew",
  "test.user": "@testuser",
  "pawel.stuczynski": "@blmbyd"
}
```

### Usage

The mapping file is loaded automatically from `user_mapping.json`. You can override this:

**Command line:**
```powershell
python main.py --user-mapping path/to/custom_user_mapping.json
```

**Environment variable:**
```
USER_MAPPING_FILE=path/to/custom_user_mapping.json
```

### Mapping Rules

- **Exact Match**: Direct username mapping: `"john.doe": "@johndoe"`
- **Case-Insensitive**: Handles username case variations automatically
- **@ Prefix**: Automatically adds @ prefix for GitHub mentions if not present
- **Text Processing**: Maps usernames mentioned in issue descriptions and comments
- **Fallback**: Uses original Redmine usernames if no mapping exists
- **No API Calls**: Simple text replacement - no GitHub API quota consumption

### Behavior

- **Issue Assignment**: Redmine assignees are mapped and assigned to GitHub issues
- **Comment Authors**: Comment metadata shows mapped GitHub username  
- **Content Mapping**: Usernames within issue/comment text become GitHub @mentions
- **Notifications**: Mapped users receive GitHub notifications when mentioned or assigned

### Examples

```powershell
# Use default user_mapping.json
python main.py

# Use custom mapping file
python main.py --user-mapping config/my_user_mapping.json

# Combine with other options
python main.py --limit 50 --user-mapping custom_mapping.json --tracker-mapping tracker_config.json
```
