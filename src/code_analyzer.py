import os
from langchain_community.document_loaders import GitLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from tqdm import tqdm
from .utils import EMBEDDING_MODEL, VECTOR_STORE_DIR

SUPPORTED_EXTENSIONS = [
    ".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".go", ".cs", ".rs", ".rb",
    ".php", ".c", ".cpp", ".h", ".hpp", ".md",
]

def load_and_split_repo(repo_path: str) -> list:
    """
    Loads all supported source files from the cloned repo and splits them.
    """
    print(f"Loading and splitting documents from {repo_path}...")
    all_docs = []
    
    for root, _, files in tqdm(os.walk(repo_path), desc="Scanning repo"):
        if ".git" in root:
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                try:
                    loader = TextLoader(file_path, encoding="utf-8")
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata["source"] = os.path.relpath(file_path, repo_path)
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"Warning: Could not read {file_path}. Error: {e}")

    if not all_docs:
        raise ValueError("No processable source code files found in the repository.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(all_docs)
    print(f"Split {len(all_docs)} documents into {len(splits)} chunks.")
    return splits


def create_vector_store(repo_path: str):
    """
    Creates and saves a FAISS vector store from the repository.
    """
    if os.path.exists(VECTOR_STORE_DIR):
        print(f"Vector store already exists at {VECTOR_STORE_DIR}. Skipping creation.")
        return
        
    documents = load_and_split_repo(repo_path)
    
    print(f"Initializing embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )
    
    print("Creating FAISS vector store... (This may take a while)")
    vector_store = FAISS.from_documents(documents, embeddings)
    
    vector_store.save_local(VECTOR_STORE_DIR)
    print(f"Vector store saved to {VECTOR_STORE_DIR}")

def get_retriever():
    """
    Loads the saved FAISS vector store as a retriever.
    """
    if not os.path.exists(VECTOR_STORE_DIR):
        raise FileNotFoundError("Vector store not found. Please run the analysis first.")
        
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL
    )
    
    print(f"Loading vector store from {VECTOR_STORE_DIR}")
    vector_store = FAISS.load_local(VECTOR_STORE_DIR, embeddings, allow_dangerous_deserialization=True)
    
    return vector_store.as_retriever(search_kwargs={"k": 5})

def find_relevant_code(issue_text: str, retriever) -> dict:
    """
    Searches the vector store for code chunks relevant to the issue.
    Accepts a retriever object to avoid reloading.
    """
    print("Finding relevant code context...")
    
    relevant_docs = retriever.invoke(issue_text)
    
    context_by_file = {}
    for doc in relevant_docs:
        file_path = doc.metadata.get("source", "unknown_file")
        if file_path not in context_by_file:
            context_by_file[file_path] = []
        context_by_file[file_path].append(doc.page_content)
        
    final_context = {
        file: "\n...\n".join(chunks) 
        for file, chunks in context_by_file.items()
    }
    
    print(f"Found {len(relevant_docs)} relevant chunks across {len(final_context)} files.")
    return final_context