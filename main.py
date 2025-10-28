import argparse
import os
import sys
from dotenv import load_dotenv
from src.utils import parse_github_url, temp_repo_clone, WORKSPACE_DIR, clean_workspace
from src.github_client import fetch_issue_details
from src.code_analyzer import create_vector_store, find_relevant_code
# Import all the required functions from our modified handler
from src.llm_handler import check_ollama_model, classify_issue_type, generate_analysis

def run_analysis(repo_url: str, issue_number: int):
    """
    Main function to run the end-to-end analysis using Ollama.
    """
    
    if not check_ollama_model():
        print("Please ensure Ollama is running and the required model is pulled.")
        sys.exit(1)

    try:
        owner, repo_name = parse_github_url(repo_url)
        repo_path = os.path.join(WORKSPACE_DIR, repo_name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        issue_data = fetch_issue_details(owner, repo_name, issue_number)
    except Exception as e:
        print(f"Error fetching issue #{issue_number}: {e}")
        sys.exit(1)

    # --- NEW LOGIC: 2-STEP CHAIN ---
    
    # 1. CLASSIFY THE ISSUE
    try:
        issue_type = classify_issue_type(issue_data)
    except Exception as e:
        print(f"Fatal error during classification: {e}")
        sys.exit(1)
        
    # 2. CHECK CLASSIFICATION AND PROCEED
    if issue_type != "BUG":
        print(f"Analysis complete. Issue is an '{issue_type}', not a bug. No fix required.")
        print("="*80)
        return # Stop execution

    # --- (Original code continues, only if it's a bug) ---
    print("Issue is a BUG. Proceeding with full analysis...")
    
    try:
        with temp_repo_clone(repo_url, repo_path):
            create_vector_store(repo_path)
            issue_full_text = f"Title: {issue_data['title']}\n\nBody: {issue_data['body']}"
            code_context = find_relevant_code(issue_full_text)
            
    except Exception as e:
        print(f"Error during code analysis: {e}")
        sys.exit(1)

    try:
        analysis_report = generate_analysis(issue_data, code_context)
        
        print("\n" + "="*80)
        print(f" BUG ANALYSIS REPORT FOR: {repo_url} - Issue #{issue_number}")
        print("="*80 + "\n")
        print(f"Issue URL: {issue_data['url']}\n")
        print(analysis_report)
        print("\n" + "="*80)

    except Exception as e:
        print(f"Error during LLM analysis generation: {e}")
    finally:
        clean_workspace()


def main():
    load_dotenv()  # Load .env file

    parser = argparse.ArgumentParser(description="GitHub Bug Analyzer AI (Ollama Edition)")
    parser.add_argument(
        "repo_url",
        type=str,
        help="The full URL of the GitHub repository (e.g., https://github.com/gothinkster/realworld)"
    )
    parser.add_argument(
        "issue_number",
        type=int,
        help="The issue number to analyze (e.g., 1647)"
    )
    
    args = parser.parse_args()
    
    if not os.environ.get("GITHUB_TOKEN"):
        print("Warning: GITHUB_TOKEN environment variable is not set.")
        print("-" * 30)

    run_analysis(args.repo_url, args.issue_number)


if __name__ == "__main__":
    main()