import requests
import os

BASE_URL = "http://localhost:8000"
API_KEY = "dev-internal-key-change-in-production"
HEADERS = {"X-API-Key": API_KEY}

def test_analyze():
    print("\n--- Testing /analyze ---")
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Sample_Software_Engineer_Resume.pdf"))
    if not os.path.exists(resume_path):
        print(f"Error: {resume_path} not found")
        return
        
    files = {'file': ('resume.pdf', open(resume_path, 'rb'), 'application/pdf')}
    response = requests.post(f"{BASE_URL}/analyze", headers=HEADERS, files=files)
    if response.status_code == 200:
        data = response.json()
        print(f"Role Score: {data['role_score']}")
        print(f"Name: {data['candidate_name']}")
        print(f"Predicted Role: {data['predicted_role']}")
        print(f"Missing Skills: {data['missing_skills']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_match():
    print("\n--- Testing /match ---")
    resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Sample_Software_Engineer_Resume.pdf"))
    files = {'file': ('resume.pdf', open(resume_path, 'rb'), 'application/pdf')}
    data = {"job_description": "We are looking for a Senior Frontend Developer with experience in React, TypeScript, and semantic model architectures."}
    response = requests.post(f"{BASE_URL}/match", headers=HEADERS, files=files, data=data)
    if response.status_code == 200:
        match_data = response.json()
        print(f"Match %: {match_data['match_percentage']}")
        print(f"Semantic Score: {match_data['semantic_score']}%")
        print(f"Matched Keywords: {match_data['matched_keywords']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    try:
        test_analyze()
        test_match()
    except Exception as e:
        print(f"Test failed: {e}")
