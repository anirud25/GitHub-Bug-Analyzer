import os
from github import Github, Auth
from git import Repo
from .utils import WORKSPACE_DIR

def get_github_api():
    """
    Initializes the PyGithub client using an environment variable.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN environment variable not set. API rate limits will be very low.")
        return Github()
        
    auth = Auth.Token(token)
    return Github(auth=auth)

def fetch_all_open_issues(owner: str, repo_name: str):
    """
    Fetches all open issues for a repository.
    Returns a PaginatedList of Issue objects.
    """
    print(f"Fetching all open issues for {owner}/{repo_name}...")
    g = get_github_api()
    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
        # Returns a PaginatedList. Iteration in main.py will handle paging.
        return repo.get_issues(state='open')
    except Exception as e:
        print(f"Error fetching issues: {e}")
        raise

def clone_repo(repo_url: str, clone_path: str) -> Repo:
    """
    Clones a public GitHub repository and returns the Repo object.
    """
    if os.path.exists(clone_path):
        print(f"Repository already exists at {clone_path}. Using existing.")
        return Repo(clone_path)
        
    try:
        repo = Repo.clone_from(repo_url, clone_path, progress=None, depth=1)
        print(f"Successfully cloned {repo_url} to {clone_path}")
        return repo
    except Exception as e:
        print(f"Error cloning repository: {e}")
        raise