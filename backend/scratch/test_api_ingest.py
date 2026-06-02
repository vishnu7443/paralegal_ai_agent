import requests
import json
import time

def test_pipeline():
    # 1. Upload PDF
    print("=== STEP 1: Uploading PDF via API ===")
    url_upload = "http://127.0.0.1:8000/api/upload"
    files = {"file": ("sample_nda.pdf", open("backend/scratch/sample_nda.pdf", "rb"), "application/pdf")}
    
    response = requests.post(url_upload, files=files)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 201:
        print(f"Upload failed: {response.text}")
        return
        
    upload_data = response.json()
    print(f"Response: {upload_data}")
    doc_id = upload_data["document_id"]
    
    # 2. Dispatch Analysis
    print("\n=== STEP 2: Dispatching Analysis Job ===")
    url_analyse = "http://127.0.0.1:8000/api/analyse"
    payload = {"document_id": doc_id}
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url_analyse, data=json.dumps(payload), headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code != 201:
        print(f"Analysis dispatch failed: {response.text}")
        return
        
    analyse_data = response.json()
    print(f"Response: {analyse_data}")
    job_id = analyse_data["job_id"]
    
    # 3. Stream Events (wait and display results)
    print("\n=== STEP 3: Monitoring Job Progress ===")
    url_report = f"http://127.0.0.1:8000/api/report/{job_id}"
    
    for _ in range(20):
        time.sleep(1.5)
        res = requests.get(url_report)
        job_status = res.json()["status"]
        print(f"Job Status: {job_status}")
        
        if job_status in ["COMPLETED", "FAILED"]:
            break
            
    # Print final result
    res = requests.get(url_report)
    final_data = res.json()
    print("\n=== FINAL ANALYSIS RESULTS ===")
    print(f"Status: {final_data['status']}")
    print(f"Overall Risk Score: {final_data['risk_score']}")
    print(f"Report Length: {len(final_data['report_markdown'] or '')} characters")
    
    # Test clauses endpoint
    url_clauses = f"http://127.0.0.1:8000/api/clauses/{job_id}"
    res_clauses = requests.get(url_clauses)
    clauses = res_clauses.json()
    print(f"Clauses Count: {len(clauses)}")
    if clauses:
        print(f"Top Severe Clause: Page {clauses[0]['page_num']} | {clauses[0]['risk_category']} | Risk: {clauses[0]['risk_level']} (Score: {clauses[0]['risk_score']})")

    # Test ad-hoc semantic search
    print("\n=== STEP 4: Testing Ad-hoc Semantic Search ===")
    url_search = "http://127.0.0.1:8000/api/search"
    search_payload = {"document_id": doc_id, "query": "governing law in Delaware", "k": 1}
    res_search = requests.post(url_search, data=json.dumps(search_payload), headers=headers)
    search_res = res_search.json()
    if search_res:
        print(f"Search match (Score: {search_res[0]['score']:.4f}): {search_res[0]['text']}")

if __name__ == "__main__":
    test_pipeline()
