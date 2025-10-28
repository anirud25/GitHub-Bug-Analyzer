import os
from github import Github, Auth
from git import Repo  # <-- Make sure Repo is imported
from .utils import WORKSPACE_DIR

def get_github_api():
    """
    Initializes the PyGithub client using an environment variable.
    """
    # Requires a GitHub Personal Access Token (PAT) in GITHUB_TOKEN
    # environment variable.
    # Create one at: https://github.com/settings/tokens
    # Needs "repo" (or "public_repo") scope.
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Warning: GITHUB_TOKEN environment variable not set. API rate limits will be very low.")
        return Github()
        
    auth = Auth.Token(token)
    return Github(auth=auth)

def fetch_issue_details(owner: str, repo_name: str, issue_number: int) -> dict:
    """
    Fetches the title, body, and comments for a specific GitHub issue.
    """
    print(f"Fetching details for issue #{issue_number} from {owner}/{repo_name}...")
    g = get_github_api()
    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
        issue = repo.get_issue(number=issue_number)
        
        comments = []
        for comment in issue.get_comments():
            comments.append({
                "user": comment.user.login,
                "body": comment.body
            })
            
        return {
            "title": issue.title,
            "body": issue.body,
            "comments": comments,
            "url": issue.html_url
        }
    except Exception as e:
        print(f"Error fetching issue: {e}")
        raise

def clone_repo(repo_url: str, clone_path: str) -> Repo:
    """
    Clones a public GitHub repository and returns the Repo object.
    """
    if os.path.exists(clone_path):
        print(f"Repository already exists at {clone_path}. Using existing.")
        # Return a Repo object for the existing path
        return Repo(clone_path)
        
    try:
        # This returns the Repo object after cloning
        repo = Repo.clone_from(repo_url, clone_path, progress=None, depth=1)
        print(f"Successfully cloned {repo_url} to {clone_path}")
        return repo
    except Exception as e:
        print(f"Error cloning repository: {e}")
        raise