const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (typeof window !== "undefined") {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://localhost:8000/api";
    }
    return `${window.location.origin}/_/backend/api`;
  }
  return "http://localhost:8000/api";
};

export const API_BASE_URL = getApiBaseUrl();


export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to upload document.");
  }
  return response.json();
}

export async function analyseDocument(documentId: number) {
  const response = await fetch(`${API_BASE_URL}/analyse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_id: documentId }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to start analysis job.");
  }
  return response.json();
}

export async function getAnalysisReport(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/report/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to load completed report.");
  }
  return response.json();
}

export async function getJobClauses(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/clauses/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to load job clauses.");
  }
  return response.json();
}

export async function searchDocument(documentId: number, query: string, k: number = 5) {
  const response = await fetch(`${API_BASE_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ document_id: documentId, query, k }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to search document.");
  }
  return response.json();
}

export async function compareDocuments(jobIds: string[]) {
  const response = await fetch(`${API_BASE_URL}/compare`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_ids: jobIds }),
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Failed to compare documents.");
  }
  return response.json();
}

export async function listJobs() {
  const response = await fetch(`${API_BASE_URL}/jobs`);
  if (!response.ok) {
    throw new Error("Failed to list jobs.");
  }
  return response.json();
}
