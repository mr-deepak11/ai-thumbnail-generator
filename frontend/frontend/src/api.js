const API_BASE = "/api";

async function getErrorMessage(response, fallback) {
  const body = await response.json().catch(() => null);
  const detail = body?.detail;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map(({ loc, msg }) => {
        const field = Array.isArray(loc) ? loc.slice(1).join(".") : "";
        return field ? `${field}: ${msg}` : msg;
      })
      .join("; ");
  }

  return fallback;
}

export async function uploadHeadshot(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/upload-headshot`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    throw new Error(await getErrorMessage(res, "Failed to upload headshot"));
  }

  return res.json();
}

export async function createJob(data) {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(await getErrorMessage(res, "Failed to create job"));
  }

  return res.json();
}

export async function getJob(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);

  if (!res.ok) {
    throw new Error(await getErrorMessage(res, "Failed to fetch job"));
  }

  return res.json();
}

export async function subscribeToJob(
  jobId,
  {
    onThumbnailReady,
    onThumbnailFailed,
    onJobComplete,
    onError,
  }
) {
  const es = new EventSource(`${API_BASE}/jobs/${jobId}/stream`);
  let completed = false;

  es.addEventListener("thumbnail_ready", (event) => {
    onThumbnailReady?.(JSON.parse(event.data));
  });

  es.addEventListener("thumbnail_failed", (event) => {
    onThumbnailFailed?.(JSON.parse(event.data));
  });

  const handleJobComplete = (event) => {
    if (completed) {
      return;
    }
    completed = true;
    onJobComplete?.(JSON.parse(event.data));
    es.close();
  };

  es.addEventListener("job_complete", handleJobComplete);
  es.addEventListener("job_completed", handleJobComplete);

  es.addEventListener("error", (event) => {
    if (onError) {
      onError(event);
    }
    es.close();
  });

  return () => {
    es.close();
  };
}