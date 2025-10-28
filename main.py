import argparse
import os
import sys
import datetime
from dotenv import load_dotenv
from src.utils import parse_github_url, temp_repo_clone, WORKSPACE_DIR, clean_workspace
from src.github_client import fetch_all_open_issues
from src.code_analyzer import create_vector_store, find_relevant_code, get_retriever
from src.llm_handler import check_ollama_model, classify_issue_type, generate_analysis

def write_summary_report(reports: list, repo_name: str, repo_url: str) -> str:
    """
    Writes all analysis results to a single summary Markdown file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_summary_{repo_name}_{timestamp}.md"
    
    print(f"Writing summary report to {filename}...")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 🤖 GitHub Bug Analysis Report\n\n")
        f.write(f"**Repository:** [{repo_name}]({repo_url})\n")
        f.write(f"**Date:** {datetime.datetime.now().isoformat()}\n")
        f.write(f"**Total Issues Processed:** {len(reports)}\n\n")
        
        bugs = [r for r in reports if "Skipped:" not in r['report'] and "Failed:" not in r['report']]
        skipped = [r for r in reports if "Skipped:" in r['report']]
        failed = [r for r in reports if "Failed:" in r['report']]
        
        f.write(f"## 📊 Summary\n")
        f.write(f"- **Bugs Analyzed:** {len(bugs)}\n")
        f.write(f"- **Non-Bugs Skipped:** {len(skipped)}\n")
        f.write(f"- **Failed Analyses:** {len(failed)}\n\n")
        
        f.write("---\n\n")
        
        if bugs:
            f.write("## 🐞 Bug Analyses\n\n")
            for item in bugs:
                issue = item['issue']
                f.write(f"### [BUG] Issue #{issue['number']}: {issue['title']}\n\n")
                f.write(f"**URL:** {issue['url']}\n\n")
                f.write(f"{item['report']}\n\n")
                f.write("---\n\n")
        
        if skipped:
            f.write("## ⏩ Skipped Issues (Non-Bugs)\n\n")
            for item in skipped:
                issue = item['issue']
                f.write(f"* **Issue #{issue['number']}:** {issue['title']} ({item['report']})\n")
                f.write(f"  *URL: {issue['url']}*\n\n")

        if failed:
            f.write("## ❌ Failed Analyses\n\n")
            for item in failed:
                issue = item['issue']
                f.write(f"* **Issue #{issue['number']}:** {issue['title']} ({item['report']})\n")
                f.write(f"  *URL: {issue['url']}*\n\n")
    
    return filename

def run_repo_scan(repo_url: str, max_issues: int):
    """
    Main function to run the end-to-end analysis for an entire repository.
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

    analysis_reports = []

    try:
        print("--- Step 1: Cloning Repo and Building Vector Store ---")
        with temp_repo_clone(repo_url, repo_path):
            create_vector_store(repo_path)
            retriever = get_retriever() # Load retriever ONCE
            print("--- Vector store created successfully. ---")

            print("--- Step 2: Fetching and Processing Issues ---")
            all_issues = fetch_all_open_issues(owner, repo_name)
            
            issue_count = 0
            for issue in all_issues:
                if issue_count >= max_issues:
                    print(f"\nReached max issue limit ({max_issues}). Stopping scan.")
                    break
                
                # Skip pull requests, as they are often listed as issues
                if issue.pull_request:
                    continue

                print("\n" + "="*50)
                print(f"Processing Issue #{issue.number}: {issue.title}")
                print(f"URL: {issue.html_url}")

                # Format comments for the LLM
                comments_list = []
                try:
                    for comment in issue.get_comments():
                        comments_list.append({"user": comment.user.login, "body": comment.body})
                except Exception as e:
                    print(f"Warning: Could not fetch comments for issue #{issue.number}. Error: {e}")

                issue_data = {
                    "title": issue.title,
                    "body": issue.body or "", # Ensure body is not None
                    "comments": comments_list,
                    "url": issue.html_url,
                    "number": issue.number
                }

                try:
                    # Step 2a: Classify
                    issue_type = classify_issue_type(issue_data)
                    
                    if issue_type == "BUG":
                        print("Type: BUG. Proceeding with analysis.")
                        # Step 2b: RAG
                        issue_full_text = f"Title: {issue.title}\n\nBody: {issue.body}"
                        code_context = find_relevant_code(issue_full_text, retriever)
                        
                        # Step 2c: Analyze
                        report = generate_analysis(issue_data, code_context)
                        analysis_reports.append({"issue": issue_data, "report": report})
                    else:
                        print(f"Type: {issue_type}. Skipping analysis.")
                        analysis_reports.append({"issue": issue_data, "report": f"Skipped: Issue classified as {issue_type}."})

                except Exception as e:
                    print(f"Error processing issue #{issue.number}: {e}")
                    analysis_reports.append({"issue": issue_data, "report": f"Failed to analyze: {e}"})
                
                issue_count += 1
        
        print("\n--- Scan complete. ---")

    except Exception as e:
        print(f"\nAn unexpected error occurred during the scan: {e}")
    finally:
        # Generate report even if the scan was interrupted
        if analysis_reports:
            print("--- Step 3: Generating Summary Report ---")
            report_filename = write_summary_report(analysis_reports, repo_name, repo_url)
            print(f"✅ Analysis complete. Report saved to: {report_filename}")
        else:
            print("No issues were processed. No report generated.")

        # Clean up workspace and vector store
        clean_workspace()

def main():
    load_dotenv()  # Load .env file

    parser = argparse.ArgumentParser(description="GitHub Bug Analyzer AI (Repo Scan Edition)")
    parser.add_argument(
        "repo_url",
        type=str,
        help="The full URL of the GitHub repository (e.g., https://github.com/gothinkster/realworld)"
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=40,
        help="The maximum number of open issues to scan."
    )
    
    args = parser.parse_args()
    
    if not os.environ.get("GITHUB_TOKEN"):
        print("Warning: GITHUB_TOKEN environment variable is not set.")
        print("You will face severe API rate limits from GitHub.")
        print("-" * 30)

    run_repo_scan(args.repo_url, args.max_issues)

if __name__ == "__main__":
    main()