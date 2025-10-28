import ollama
import sys
import json

# This MUST match the model you pulled with 'ollama pull'
OLLAMA_MODEL = "llama3:instruct"

# --- Main System Prompt (for Analysis) ---
SYSTEM_PROMPT = """You are an expert software engineer specializing in bug detection and resolution. 
Analyze the provided GitHub issue and relevant code snippets to find the root cause and generate a complete fix. 
Be concise, accurate, and provide code in the requested formats.
Provide your response *only* in the structured format requested."""


# --- STEP 1: NEW CLASSIFICATION FUNCTION ---

CLASSIFICATION_SYSTEM_PROMPT = """You are an issue classifier. Your job is to read a GitHub issue and classify it into one of four categories: 'BUG', 'FEATURE', 'QUESTION', 'ANNOUNCEMENT'.
Respond *only* with the single category name in JSON format.
Example: {"type": "BUG"}"""

def classify_issue_type(issue_data: dict) -> str:
    """
    Step 1: Classifies the issue into a specific type.
    """
    print("Step 1: Classifying issue type...")
    
    issue_text = f"Title: {issue_data['title']}\n\nBody: {issue_data['body']}"
    
    messages = [
        {'role': 'system', 'content': CLASSIFICATION_SYSTEM_PROMPT},
        {'role': 'user', 'content': issue_text}
    ]
    
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            format="json"  # Request JSON output
        )
        
        response_text = response['message']['content']
        classification = json.loads(response_text)
        
        if 'type' in classification:
            issue_type = classification['type'].upper()
            print(f"Issue classified as: {issue_type}")
            return issue_type
        else:
            print("Warning: Classification failed to return 'type' key.")
            return "UNKNOWN"
            
    except Exception as e:
        print(f"Error during issue classification: {e}")
        return "UNKNOWN"


# --- STEP 2: ANALYSIS FUNCTIONS (Modified) ---

def build_analysis_prompt(issue_title: str, issue_body: str, issue_comments: list, relevant_files: dict) -> str:
    """
    Builds the structured user prompt for the analysis task.
    (This is the old 'build_user_prompt' function, renamed)
    """
    
    file_context = "\n\n".join(
        f"--- START FILE: {path} ---\n```\n{content}\n```\n--- END FILE: {path} ---"
        for path, content in relevant_files.items()
    )
    if not file_context:
        file_context = "No relevant code snippets found."

    comment_str = "\n".join(
        [f"- {c['user']}: {c['body']}" for c in issue_comments]
    ) if issue_comments else "No comments."

    # This prompt is now simpler, as it *assumes* it's a bug.
    prompt = f"""
**GitHub Issue Analysis Task**

**1. Issue Details:**
* **Title:** {issue_title}
* **Description:** {issue_body}
* **Comments:** {comment_str}

**2. Relevant Code Context:**
{file_context}

**3. Your Task:**
Provide a comprehensive bug analysis and solution for the issue described above.
Use the provided code context to find the root cause and generate a fix.

<ANALYSIS>
**1. Root Cause Analysis:**
(Explain *why* the bug is happening, based *only* on the issue description and code context.)

**2. Step-by-Step Reproduction:**
(Provide a clear, numbered list of steps to reproduce the *specific bug* described in the issue.)

**3. Affected Code Paths:**
(List the specific files and functions from the context that are *directly related* to the reported bug.)

**4. Complete Fix (Patch):**
(Provide the fix as a git diff in the unified format. Use ```diff ... ```. If this is not possible, provide the complete new function.)

**5. Test Cases to Prevent Regression:**
(Provide test cases that *specifically* validate the fix for the reported bug.)

**6. Potential Side Effects:**
(List any potential risks or areas to double-check after implementing this fix.)
</ANALYSIS>
"""
    return prompt.strip()


def generate_analysis(issue_data: dict, code_context: dict) -> str:
    """
    Step 2: Generates the bug analysis using the Ollama client.
    (This function is now only called if the issue is a bug)
    """
    print("Step 2: Generating full bug analysis...")
    
    user_prompt = build_analysis_prompt(
        issue_title=issue_data['title'],
        issue_body=issue_data['body'],
        issue_comments=issue_data['comments'],
        relevant_files=code_context
    )
    
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': user_prompt}
    ]
    
    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages
        )
        
        response_text = response['message']['content']
        
        # Parse the <ANALYSIS> block
        start_tag = "<ANALYSIS>"
        end_tag = "</ANALYSIS>"
        start_index = response_text.find(start_tag)
        end_index = response_text.rfind(end_tag)
        
        if start_index != -1 and end_index != -1:
            start_index += len(start_tag)
            analysis = response_text[start_index:end_index].strip()
            print("Analysis generation complete.")
            return analysis
        else:
            print("Warning: LLM did not return the expected <ANALYSIS> structure.")
            return response_text.strip()

    except Exception as e:
        print(f"Error during Ollama analysis generation: {e}")
        raise

# --- (check_ollama_model function remains unchanged) ---
def check_ollama_model():
    """
    Checks if the required Ollama model is available locally.
    """
    print(f"Checking for Ollama model: {OLLAMA_MODEL}...")
    try:
        model_data = ollama.list()
        if 'models' not in model_data:
             print("Error: 'models' key not found in ollama.list() response.")
             return False
        models_list = model_data['models']
        print(f"Found {len(models_list)} models. Checking list...")
        for model_object in models_list:
            if hasattr(model_object, 'model'):
                print(f"Checking model: {model_object.model}")
                if model_object.model.startswith(OLLAMA_MODEL):
                    print(f"Success: Found matching model '{model_object.model}'.")
                    return True # Found it
            else:
                print(f"Warning: Found a model entry with no '.model' attribute: {model_object}")
        print(f"Error: Model '{OLLAMA_MODEL}' not found in the list.")
        return False
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return False