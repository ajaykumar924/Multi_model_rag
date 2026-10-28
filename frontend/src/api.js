const API_URL = "http://127.0.0.1:8000/api";

export async function sendQuestion(question) {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Failed to get an answer from the assistant."
    );
  }

  return data;
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/upload?overwrite=true`, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to upload file.");
  }

  return data;
}

export async function triggerIngest() {
  const response = await fetch(`${API_URL}/ingest`, {
    method: "POST",
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Ingestion failed.");
  }

  return data;
}

export async function getDocuments() {
  const response = await fetch(`${API_URL}/documents`);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to fetch documents.");
  }

  return data.documents || [];
}

export async function deleteDocument(filename) {
  const response = await fetch(`${API_URL}/documents/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to delete document.");
  }

  return data;
}
