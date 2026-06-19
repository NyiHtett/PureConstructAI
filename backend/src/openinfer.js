const OPENINFER_URL = "https://platform.openinfer.io/v1/responses";
const MODEL = "@oi/beta";

export async function analyzeWithOpenInfer({ projectName, modificationRequest, imageDataUrl, inventory }) {
  const apiKey = process.env.OPENINFER_API_KEY;
  if (!apiKey || apiKey === "replace-with-hackathon-key") {
    throw new Error("OPENINFER_API_KEY is not configured");
  }

  const response = await fetch(OPENINFER_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: MODEL,
      stream: true,
      input: [
        {
          role: "user",
          content: [
            {
              type: "input_text",
              text: buildPrompt({ projectName, modificationRequest, inventory })
            },
            {
              type: "input_image",
              image_url: imageDataUrl
            }
          ]
        }
      ]
    })
  });

  if (!response.ok || !response.body) {
    const body = await response.text();
    throw new Error(`OpenInfer request failed: ${response.status} ${body}`);
  }

  const outputText = await readSseText(response.body);
  return parseReportJson(outputText);
}

function buildPrompt({ projectName, modificationRequest, inventory }) {
  const inventoryPreview = inventory
    .slice(0, 30)
    .map((item) => `${item.name} | ${item.category} | ${item.quantity} ${item.unit} | ${item.status} | tags: ${(item.tags || []).join(", ")}`)
    .join("\n");

  return `You are a senior construction field engineer creating a concise job-site modification report.

Project: ${projectName || "Unnamed project"}
Requested modification: ${modificationRequest}

Available inventory:
${inventoryPreview}

Inspect the image and return only valid JSON with this exact shape:
{
  "summary": "one sentence",
  "observedConditions": ["3-5 concise bullets"],
  "recommendedPlan": ["3-6 sequenced bullets"],
  "risks": ["2-4 safety or constructability risks"],
  "nextSteps": ["2-4 immediate next actions"]
}

Do not wrap the JSON in markdown. Do not include comments.`;
}

async function readSseText(body) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let text = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      for (const line of event.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        try {
          const parsed = JSON.parse(payload);
          if (parsed.type === "response.output_text.delta" && typeof parsed.delta === "string") {
            text += parsed.delta;
          } else if (typeof parsed.delta === "string") {
            text += parsed.delta;
          }
        } catch {
          // Ignore keepalive or non-JSON event fragments.
        }
      }
    }
  }

  return text;
}

function parseReportJson(outputText) {
  const trimmed = outputText.trim();
  const jsonStart = trimmed.indexOf("{");
  const jsonEnd = trimmed.lastIndexOf("}");
  if (jsonStart === -1 || jsonEnd === -1) {
    throw new Error("OpenInfer did not return JSON");
  }

  const parsed = JSON.parse(trimmed.slice(jsonStart, jsonEnd + 1));
  return {
    summary: String(parsed.summary || "Site modification report generated."),
    observedConditions: normalizeLines(parsed.observedConditions),
    recommendedPlan: normalizeLines(parsed.recommendedPlan),
    risks: normalizeLines(parsed.risks),
    nextSteps: normalizeLines(parsed.nextSteps)
  };
}

function normalizeLines(value) {
  if (Array.isArray(value)) {
    return value.map((line) => String(line)).filter(Boolean).slice(0, 8);
  }
  if (typeof value === "string" && value.trim()) {
    return [value.trim()];
  }
  return ["Field review required."];
}
