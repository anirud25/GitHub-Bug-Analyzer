# RAG-based GitHub Bug Analyzer AI using LLama3

This is an AI-powered system, built using Ollama, that automatically scans an entire GitHub repository, analyzes all open issues, and generates detailed bug reports for those it identifies as "bugs."

It uses a sophisticated 2-step AI chain with Retrieval-Augmented Generation (RAG) to provide high-quality, code-aware analysis. Instead of just analyzing one issue, it scans the entire repository and compiles a single, summarized Markdown report, using a powerful open-source Code LLM, LLama3.

## Features

-   **GitHub Integration**: Fetches issue details (title, body, comments) directly from a repository.
-   **Codebase Indexing**: Clones the repository and indexes the source code using a vector store (FAISS).
-   **LangChain + RAG Pipeline**: Finds the most relevant code snippets related to the bug description.
-   **AI Analysis**: Uses an open-source model (`llama3:instruct`) to generate a full report.
-   **Structured Output**: Provides root cause, reproduction steps, affected paths, a code patch, test cases, and potential side effects.

## Deliverables

The final output is a comprehensive Markdown report that includes:

-  Automated Repository Scan: Scans an entire GitHub repository for all open issues (up to a user-defined limit), not just one.

-  AI-Powered Issue Triage: Employs a sophisticated 2-step AI chain to automatically classify each issue as a `BUG`, `FEATURE`, `QUESTION`, or `ANNOUNCEMENT`, ensuring the AI only analyzes actual bugs.

-  Code-Aware RAG Pipeline: For bugs only, it uses Retrieval-Augmented Generation (RAG) to find and feed the most relevant code snippets from the repository into the analysis model.

-  Deep Bug Analysis: Uses the llama3:instruct model to generate a detailed 6-part analysis for every confirmed bug.

-  Comprehensive Summary Report: Compiles all findings into a single, timestamped Markdown report. This deliverable separates actionable bug analyses (with code fixes) from the list of skipped non-bug issues.

## System Requirements

-   **Python**: 3.9+
-   **Git**: Must be installed and available in your system's `PATH`.
-   **Ollama**: The Ollama service (v0.12.6 or newer) must be installed and running.

    - Ollama will automatically use your GPU (if available) or CPU. A Mac with Apple Silicon (M1/M2/M3) or a PC with a CUDA-compatible (NVIDIA) GPU is highly recommended for fast analysis.

    - You must have the AI model pulled: `ollama pull llama3:instruct`
-   **GitHub Token**: A GitHub Personal Access Token (PAT) is required to avoid API rate limiting.

## Tech Stack Used

-  Python 3.10.9

-  Ollama (v0.12.6): For serving the local LLM. <img height="25" alt="Ollama Logo" src="https://github.com/user-attachments/assets/ecd82f38-2d98-4d62-945b-d3a194e99133" />


-  AI Model: `llama3:instruct`. <img height="25" alt="Llama 3 Logo" src="https://github.com/user-attachments/assets/0981aa84-cb94-48c0-a715-89650d5ba7ed" />


-  Embedding Model :  `sentence-transformers/all-MiniLM-L6-v2` .

-  LangChain (1.0.2): For orchestrating the RAG pipeline and LLM chains. <img src="https://upload.wikimedia.org/wikipedia/commons/6/60/LangChain_Logo.svg" alt="LangChain Logo" height="25">

-  langchain-community (0.4)

-  langchain-text-splitters

-  faiss-cpu (1.12.0): For local vector storage.

-  sentence-transformers: For generating code embeddings.

-  PyGithub: For fetching issue data from the GitHub API.

-  GitPython (3.1.45): For cloning repositories.

-  python-dotenv: For managing API keys.

## How It Works

This system is built on a 2-step AI pipeline to ensure accuracy and avoid "AI hallucinations" (where the model invents a bug).

-   **Step 1: Code Indexing (RAG)** 
    -  The system clones the target repository locally.

    -  It scans all source code files (e.g., .py, .js, .md).

    -  Using sentence-transformers, it creates vector embeddings of the code and stores them in a local FAISS vector  store. This is done only once per repository.

-   **Step 2: Issue Triage & Analysis (The 2-Step LLM Chain)**

    - The system fetches all open issues from the repository (up to a user-defined limit).

    - For each issue, it performs a 2-step AI process:

    - **Chain 1: Classification**

        - A simple, fast LLM call (`llama3:instruct`) is made to classify the issue's type: BUG, FEATURE, QUESTION, or ANNOUNCEMENT.

    - **Chain 2: Deep Analysis (For Bugs Only)**

        - If, and only if, the issue is classified as a BUG, the system proceeds.

        - It uses the issue's text to query the RAG vector store and find the most relevant code snippets from the repository.

        - It then makes a second, larger LLM call, providing the full context (Issue Details + Relevant Code) to generate a detailed 6-part analysis.
-   **Step 3: Report Generation**

    - All results (bug analyses, skipped non-bugs, and failures) are compiled into a single, timestamped Markdown file (e.g., `analysis_summary_realworld_20251028_163000.md`) in your root directory.


## Setup & Installation

Prerequisite: This project relies on Ollama. You must have it installed and running.

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/github_bug_analyzer.git](https://github.com/your-username/github_bug_analyzer.git)
    cd github_bug_analyzer
    ```

2.  **Create a Virtual Environment:**
    ```bash
    # Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # macOS / Linux
    python -m venv .venv
    source .venv/bin/activate

    ```

3.  **Install Python Dependencies:**
    This will install PyTorch, Transformers, LangChain, and other required packages.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download the Ollama LLM**
This system is tuned for llama3:instruct. Pull it via the Ollama CLI:
    ``bash
    ollama pull llama3:instruct
    ```
    (This may take a few minutes. Make sure the Ollama application is running.)

5.  **Set Environment Variables:**
    Set Your GitHub API Token - To avoid API rate limits, you must use a GitHub Personal Access Token (PAT).
    Set a `GITHUB_TOKEN` for the GitHub API.
-   Get your GitHub Token. [CREATE TOKEN](https://github.com/settings/tokens)

-  Create a `.env` file in the project root:
    ```
    GITHUB_TOKEN=your_github_personal_access_token_here
    ```
    
    Then, install `python-dotenv` (it's in `requirements.txt`) and update `main.py` to load it by adding this to the top of `main()`:
    ```python
    from dotenv import load_dotenv
    load_dotenv()

    ```
    *Alternatively*, you can just export it in your shell:*
    ```bash
    export GITHUB_TOKEN="your_github_personal_access_token_here"
    ```

## How to Run

You can now run the full repository scan from your terminal.

```bash
python -m main <repository_url> [--max-issues <number>]
```
-  repository_url (Required): The full URL of the GitHub repository to scan.

-  --max-issues (Optional): The maximum number of open issues to process. Defaults to 40.

### Example
This example uses the repository from the prompt. 
```bash
python -m main [https://github.com/gothinkster/realworld](https://github.com/gothinkster/realworld)
```
The script will begin processing. When finished, it will print the name of the summary report file (e.g., `Analysis complete. Report saved to: analysis_summary_realworld_...md`).

## Example Deliverable Snippet

Here is an example of a single bug analysis as it would appear in the final summary report:

**[BUG] Issue #681: On Update User Endpoint, 'NULL' for the password field in the request body is being accepted which should not happen**

*URL: https://github.com/gothinkster/realworld/issues/681*

- **1. Root Cause Analysis**: The root cause of the issue is that the `password` field in the request body is not being validated correctly in the Update User endpoint (PUT /api/user). Specifically, when a null value is passed for the `password`, it should throw an error response with a 422 status code. However, due to the absence of validation checks, the `password` remains null, and subsequent login attempts fail.

- **2. Step-by-Step Reproduction**: To reproduce the bug:

- Send a PUT request to /api/user with a valid JSON payload.

- Set the password field to null.

- Observe that the password remains null in the database, and subsequent login attempts fail.

- **3. Affected Code Paths**:

- `apps/api/server/routes/api/user/index.put.ts`: The `Update User` endpoint does not validate the `password` field correctly.

- **4. Complete Fix (Patch)**:

```diff
--- a/apps/api/server/routes/api/user/index.put.ts
+++ b/apps/api/server/routes/api/user/index.put.ts
@@ -12,6 +12,7 @@

    if (!email) {
        throw new HttpException(422, {errors: {email: ["can't be blank"]}});
    }

+   if (!password) {
+       throw new HttpException(422, {errors: {password: ["can't be blank"]}});
+   }
    
    // ... (rest of the code remains unchanged)
```

- **5. Test Cases to Prevent Regression**:

- Send a PUT request with a null `password` field. Verify that an error response with a 422 status code is returned.

- Send a PUT request with a non-null `password` field. Verify that the `password` is correctly updated in the database.

- **6. Potential Side Effects**:
- None expected. This fix only affects the validation of the password field in the Update User endpoint.
