import requests
import time

BASE_URL = "http://localhost:8000"
REPO_URL = "https://github.com/psf/requests" # Use a popular, stable repo

def test_root():
    print("Testing Root Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("Root Endpoint: OK")
    except Exception as e:
        print(f"Root Endpoint: FAILED ({e})")

def test_generate_adr():
    print("\nTesting ADR Generation...")
    try:
        response = requests.post(f"{BASE_URL}/generate/adr", json={"repo_url": REPO_URL})
        if response.status_code == 200:
            print("ADR Generation: OK")
            print(f"Content Preview: {response.json()['content'][:100]}...")
        else:
            print(f"ADR Generation: FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"ADR Generation: FAILED ({e})")

def test_generate_srs():
    print("\nTesting SRS Generation...")
    try:
        response = requests.post(f"{BASE_URL}/generate/srs", json={"repo_url": REPO_URL})
        if response.status_code == 200:
            print("SRS Generation: OK")
            print(f"Content Preview: {response.json()['content'][:100]}...")
        else:
            print(f"SRS Generation: FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"SRS Generation: FAILED ({e})")

def test_generate_diagram():
    print("\nTesting Diagram Generation...")
    try:
        # Test Class Diagram
        response = requests.post(f"{BASE_URL}/generate/diagram", json={"repo_url": REPO_URL, "diagram_type": "class"})
        if response.status_code == 200:
            print("Class Diagram Generation: OK")
        else:
            print(f"Class Diagram Generation: FAILED (Status {response.status_code})")

        # Test Sequence Diagram
        response = requests.post(f"{BASE_URL}/generate/diagram", json={"repo_url": REPO_URL, "diagram_type": "sequence"})
        if response.status_code == 200:
            print("Sequence Diagram Generation: OK")
        else:
            print(f"Sequence Diagram Generation: FAILED (Status {response.status_code})")

    except Exception as e:
        print(f"Diagram Generation: FAILED ({e})")

def test_download_word():
    print("\nTesting Word Download...")
    try:
        response = requests.post(f"{BASE_URL}/download/word", json={"content": "# Test Title\n\nTest content.", "filename": "test.docx"})
        if response.status_code == 200:
            print("Word Download: OK")
        else:
            print(f"Word Download: FAILED (Status {response.status_code})")
            print(response.text)
    except Exception as e:
        print(f"Word Download: FAILED ({e})")

if __name__ == "__main__":
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5) 
    test_root()
    # Note: Real generation might fail if API keys are not set or valid.
    # We will test connectivity and error handling at least.
    test_generate_adr()
    test_generate_srs()
    test_generate_diagram()
    test_download_word()
