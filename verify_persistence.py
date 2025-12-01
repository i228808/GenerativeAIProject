import requests
import sys

BASE_URL = "http://localhost:8000"

def test_persistence():
    print("Testing Persistence...")
    
    # 1. Generate a document (this should save it to DB)
    repo_url = "https://github.com/fastapi/fastapi" # Example
    print(f"Generating ADR for {repo_url}...")
    try:
        response = requests.post(f"{BASE_URL}/generate/adr", json={"repo_url": repo_url})
        if response.status_code == 200:
            print("ADR Generated successfully.")
        else:
            print(f"Failed to generate ADR: {response.text}")
            return
    except Exception as e:
        print(f"Error calling API: {e}")
        return

    # 2. List documents
    print("Listing documents...")
    try:
        response = requests.get(f"{BASE_URL}/documents")
        if response.status_code == 200:
            docs = response.json()
            print(f"Found {len(docs)} documents.")
            if len(docs) > 0:
                last_doc = docs[0]
                print(f"Latest doc ID: {last_doc['id']}, Type: {last_doc['doc_type']}")
                
                # 3. Retrieve specific document
                print(f"Retrieving document {last_doc['id']}...")
                doc_response = requests.get(f"{BASE_URL}/documents/{last_doc['id']}")
                if doc_response.status_code == 200:
                    print("Document retrieved successfully.")
                else:
                    print(f"Failed to retrieve document: {doc_response.text}")
            else:
                print("No documents found in history.")
        else:
            print(f"Failed to list documents: {response.text}")
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    test_persistence()
