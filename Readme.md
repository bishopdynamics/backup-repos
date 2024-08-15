# Backup Git Repos

Backup all repos from Github or Gitlab

## Requirements

- python3.7 or newer
- git


## Config

For Github, create `config_github.py` with the following:

```python
# your github username
GITHUB_USERNAME = 'username'
# long lived token with read access to all repos
AUTH_TOKEN = '<PUT TOKEN HERE>'
```

For Gitlab, create `config_gitlab.py` with the following:
```python
# hostname or ip address of your gitlab instance
GIT_HOST = 'git.example.com'
# long lived token
AUTH_TOKEN = '<PUT TOKEN HERE>'
```

## Usage

Run either script like: `python3 backup_github.py`
