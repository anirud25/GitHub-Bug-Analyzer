import os
import re
import shutil
import stat  
from contextlib import contextmanager

# --- Constants ---
WORKSPACE_DIR = "workspace"
VECTOR_STORE_DIR = "vector_store"
# Using a fast, reliable, and small embedding model
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Ollama model name, This MUST match the model you pulled with 'ollama pull'
OLLAMA_MODEL = "llama3:instruct"


# --- Functions ---

def parse_github_url(repo_url: str) -> tuple[str, str]:
    """
    Parses a GitHub URL to extract the owner and repo name.
    """
    match = re.search(r"github\.com/([\w\.-]+)/([\w\.-]+)", repo_url)
    if match:
        owner, repo_name = match.groups()
        # Remove .git suffix if present
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        return owner, repo_name
    
    raise ValueError(f"Invalid GitHub URL: {repo_url}")


def on_rmtree_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree on Windows.
    This handles read-only files that prevent deletion.
    """
    if not os.access(path, os.W_OK):
        # Make the file writable
        os.chmod(path, stat.S_IWUSR)
        # Retry the function (e.g., os.remove)
        func(path)
    else:
        # Re-raise the error if it's not a permissions issue
        raise


@contextmanager
def temp_repo_clone(repo_url: str, repo_path: str):
    """
    Context manager to clone a repo, close its handle, and clean it up.
    """
    from .github_client import clone_repo  # Local import to avoid circularity
    
    repo = None
    print(f"Cloning repository {repo_url} to {repo_path}...")
    try:
        # 1. Clone the repo and get the Repo object
        repo = clone_repo(repo_url, repo_path)
        yield repo_path
    finally:
        # 2. Explicitly close the Repo object handle
        if repo:
            repo.close()
            print("GitPython repo handle closed.")
            
        print(f"Cleaning up repository at {repo_path}...")
        if os.path.exists(repo_path):
            # 3. Use the robust on_rmtree_error handler
            try:
                shutil.rmtree(repo_path, onerror=on_rmtree_error)
            except Exception as e:
                print(f"Warning: Could not automatically clean up {repo_path}. Error: {e}")
                print("You may need to manually delete this folder.")

            
def clean_workspace():
    """Removes the workspace and vector store directories."""
    print("Cleaning up workspace and vector store...")
    if os.path.exists(WORKSPACE_DIR):
        try:
            shutil.rmtree(WORKSPACE_DIR, onerror=on_rmtree_error)
        except Exception as e:
            print(f"Warning: Could not clean up {WORKSPACE_DIR}. Error: {e}")
    if os.path.exists(VECTOR_STORE_DIR):
        try:
            shutil.rmtree(VECTOR_STORE_DIR, onerror=on_rmtree_error)
        except Exception as e:
            print(f"Warning: Could not clean up {VECTOR_STORE_DIR}. Error: {e}")
    print("Cleanup complete.")