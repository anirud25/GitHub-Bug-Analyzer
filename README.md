# GitHub Bug Analyzer AI

This project is an AI-powered system that analyzes GitHub issues, finds root causes, and generates complete solutions for bugs. It uses a Retrieval-Augmented Generation (RAG) pipeline to provide relevant code context to a powerful open-source Code LLM.

## Features

-   **GitHub Integration**: Fetches issue details (title, body, comments) directly from a repository.
-   **Codebase Indexing**: Clones the repository and indexes the source code using a vector store (FAISS).
-   **RAG Pipeline**: Finds the most relevant code snippets related to the bug description.
-   **AI Analysis**: Uses an open-source model (`codellama/CodeLlama-7b-Instruct-hf`) to generate a full report.
-   **Structured Output**: Provides root cause, reproduction steps, affected paths, a code patch, test cases, and potential side effects.

## System Requirements

-   **Python**: 3.9+
-   **Git**: Must be installed and available in your system's PATH.
-   **GPU**: **Highly Recommended.** A CUDA-compatible (NVIDIA) GPU with at least **8GB of VRAM** is needed to run the 7B parameter model efficiently. It will be *extremely* slow on a CPU.
-   **GitHub Token**: A GitHub Personal Access Token (PAT) is required to avoid API rate limiting.

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/your-username/github_bug_analyzer.git](https://github.com/your-username/github_bug_analyzer.git)
    cd github_bug_analyzer
    ```

2.  **Create a Virtual Environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: venv\Scripts\activate
    OR

    .venc/Scripts/activate

    ```

3.  **Install Dependencies:**
    This will install PyTorch, Transformers, LangChain, and other required packages.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Environment Variables:**
    You must set a `GITHUB_TOKEN` for the GitHub API.

    Create a `.env` file in the project root:
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

Use the `main.py` script from your terminal. Pass the repository URL and the issue number as arguments.

```bash
python -m main <repository_url> <issue_number>
```

### Example
This example uses the repository from the prompt. Note: The issues #1 and #2 mentioned in the prompt are hypothetical and do not exist on the main repository. You must use a real, existing issue number.

Let's find a real, simple, closed issue on that repo. For example, Issue #213 ("Fix typo in agent.js").

```bash
python main.py [https://github.com/gothinkster/realworld](https://github.com/gothinkster/realworld) 1647
```

