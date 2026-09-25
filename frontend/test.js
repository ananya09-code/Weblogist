const API_URL = "http://127.0.0.1:8000";
const TARGET_URL = process.argv[2] || "https://www.chess.com/";
const POLL_INTERVAL_MS = 2000;
const MAX_POLLS = 60;

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      `${options.method || "GET"} ${path} failed (${response.status}): ${
        body.detail || JSON.stringify(body)
      }`,
    );
  }

  return body;
}

async function main() {
  console.log(`Submitting scan for ${TARGET_URL}...`);

  const created = await request("/api/v1/scans", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: TARGET_URL }),
  });

  console.log("Scan created:", created);

  if (created.status === "done") {
    console.log("Cached result:");
    console.log(JSON.stringify(created, null, 2));
    return;
  }

  for (let attempt = 1; attempt <= MAX_POLLS; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));

    const scan = await request(`/api/v1/scans/${created.scan_id}`);

    console.log(`Poll ${attempt}/${MAX_POLLS}: ${scan.status}`);

    if (scan.status === "done") {
      console.log("\nScan complete:");
      console.log(JSON.stringify(scan, null, 2));
      return;
    }

    if (scan.status === "failed") {
      console.error("\nScan failed:");
      console.error(JSON.stringify(scan, null, 2));
      process.exitCode = 1;
      return;
    }
  }

  throw new Error(
    `Scan did not finish within ${(MAX_POLLS * POLL_INTERVAL_MS) / 1000} seconds`,
  );
}

main().catch((error) => {
  console.error(`\n${error.message}`);
  process.exitCode = 1;
});
