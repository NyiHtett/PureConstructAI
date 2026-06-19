const stopWords = new Set([
  "the",
  "and",
  "for",
  "with",
  "this",
  "that",
  "from",
  "into",
  "site",
  "work",
  "need",
  "needs",
  "using",
  "make",
  "modify",
  "modification"
]);

export function matchInventory({ inventory, report, modificationRequest }) {
  const reportText = [
    modificationRequest,
    report.summary,
    ...report.observedConditions,
    ...report.recommendedPlan,
    ...report.risks,
    ...report.nextSteps
  ]
    .join(" ")
    .toLowerCase();

  const tokens = tokenize(reportText);

  return inventory
    .map((item) => scoreItem(item, tokens, reportText))
    .filter((match) => match.score > 0 && match.item.quantity > 0 && match.item.status.toLowerCase() !== "unavailable")
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(({ item, score, reasons }) => ({
      inventoryItemId: item.id,
      name: item.name,
      confidence: Math.min(0.96, 0.54 + score * 0.08),
      reason: reasons.slice(0, 2).join("; ") || "Relevant to the requested field modification."
    }));
}

function scoreItem(item, tokens, reportText) {
  const searchable = [item.name, item.category, item.location, ...(item.tags || []), item.notes || ""]
    .join(" ")
    .toLowerCase();
  let score = 0;
  const reasons = [];

  for (const token of tokens) {
    if (searchable.includes(token)) score += 1;
  }

  for (const tag of item.tags || []) {
    if (reportText.includes(tag.toLowerCase())) {
      score += 2;
      reasons.push(`matched ${tag}`);
    }
  }

  if (item.status.toLowerCase() === "available") {
    score += 1;
    reasons.push(`${item.quantity} ${item.unit} available at ${item.location}`);
  } else if (item.status.toLowerCase() === "low stock") {
    score += 0.5;
    reasons.push(`low stock: ${item.quantity} ${item.unit} at ${item.location}`);
  } else {
    reasons.push(`${item.status.toLowerCase()} item requires supervisor confirmation`);
  }

  return { item, score, reasons };
}

function tokenize(text) {
  return Array.from(
    new Set(
      text
        .replace(/[^a-z0-9\s-]/g, " ")
        .split(/\s+/)
        .map((token) => token.trim())
        .filter((token) => token.length > 2 && !stopWords.has(token))
    )
  );
}
