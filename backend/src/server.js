import cors from "cors";
import "dotenv/config";
import express from "express";
import { nanoid } from "nanoid";
import { getDb } from "./db.js";
import { matchInventory } from "./matching.js";
import { analyzeWithOpenInfer } from "./openinfer.js";
import { sampleInventory } from "./sampleData.js";

const app = express();
const port = Number(process.env.PORT || 8787);

app.use(cors());
app.use(express.json({ limit: "18mb" }));

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "pureconstruct-ai-backend" });
});

app.get("/api/inventory", async (_req, res) => {
  try {
    const db = await getDb();
    await ensureSeedInventory(db);
    const items = await db.collection("inventory").find({}, { projection: { _id: 0 } }).sort({ category: 1, name: 1 }).toArray();
    res.json(items);
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.post("/api/inventory", async (req, res) => {
  try {
    const db = await getDb();
    const now = new Date();
    const item = {
      id: req.body.id || `inv-${nanoid(10)}`,
      name: String(req.body.name || "").trim(),
      category: String(req.body.category || "Materials").trim(),
      quantity: Number(req.body.quantity || 0),
      unit: String(req.body.unit || "pcs").trim(),
      status: String(req.body.status || "Available").trim(),
      location: String(req.body.location || "Unassigned").trim(),
      tags: Array.isArray(req.body.tags) ? req.body.tags.map(String) : [],
      notes: req.body.notes ? String(req.body.notes) : null,
      imageDataUrl: req.body.imageDataUrl ? String(req.body.imageDataUrl) : null,
      updatedAt: now
    };

    if (!item.name) {
      return res.status(400).json({ error: "name is required" });
    }

    await db.collection("inventory").updateOne({ id: item.id }, { $set: item }, { upsert: true });
    res.status(201).json(item);
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.patch("/api/inventory/:id", async (req, res) => {
  try {
    const db = await getDb();
    const patch = {
      ...req.body,
      updatedAt: new Date()
    };
    delete patch._id;
    delete patch.id;

    const result = await db.collection("inventory").findOneAndUpdate(
      { id: req.params.id },
      { $set: patch },
      { returnDocument: "after", projection: { _id: 0 } }
    );

    if (!result) {
      return res.status(404).json({ error: "inventory item not found" });
    }

    res.json(result);
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.get("/api/reports", async (_req, res) => {
  try {
    const db = await getDb();
    const reports = await db.collection("reports").find({}, { projection: { _id: 0, imageDataUrl: 0 } }).sort({ createdAt: -1 }).limit(30).toArray();
    res.json(reports);
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.get("/api/reports/:id", async (req, res) => {
  try {
    const db = await getDb();
    const report = await db.collection("reports").findOne({ id: req.params.id }, { projection: { _id: 0 } });
    if (!report) {
      return res.status(404).json({ error: "report not found" });
    }
    res.json(report);
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.post("/api/reports/analyze", async (req, res) => {
  try {
    const { projectName = "Field Report", modificationRequest, imageDataUrl } = req.body;
    if (!modificationRequest || !imageDataUrl) {
      return res.status(400).json({ error: "modificationRequest and imageDataUrl are required" });
    }

    const db = await getDb();
    await ensureSeedInventory(db);
    const inventory = await db.collection("inventory").find({}, { projection: { _id: 0 } }).toArray();

    let reportCore;
    let generatedBy = "openinfer";
    try {
      reportCore = await analyzeWithOpenInfer({ projectName, modificationRequest, imageDataUrl, inventory });
    } catch (error) {
      generatedBy = "fallback";
      reportCore = fallbackReport({ modificationRequest });
      console.warn(`[analysis:fallback] ${error.message}`);
    }

    const matchedInventory = matchInventory({ inventory, report: reportCore, modificationRequest });
    const report = {
      id: `rep-${nanoid(12)}`,
      projectName,
      modificationRequest,
      ...reportCore,
      matchedInventory,
      imageDataUrl,
      generatedBy,
      createdAt: new Date()
    };

    await db.collection("reports").insertOne(report);
    const { _id, imageDataUrl: _imageDataUrl, ...clientReport } = report;
    res.status(201).json(clientReport);
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`PureConstruct AI backend listening on http://localhost:${port}`);
});

async function ensureSeedInventory(db) {
  const count = await db.collection("inventory").countDocuments();
  if (count > 0) return;
  const now = new Date();
  await db.collection("inventory").insertMany(sampleInventory.map((item) => ({ ...item, updatedAt: now })));
}

function fallbackReport({ modificationRequest }) {
  return {
    summary: "Field-ready modification report generated from the request while AI vision is unavailable.",
    observedConditions: [
      "Image review should be confirmed by the foreman before work starts.",
      "Adjacent finishes and active work zones should be protected before modification.",
      "Existing utilities, anchors, and penetrations require verification."
    ],
    recommendedPlan: [
      `Clarify the requested scope: ${modificationRequest}`,
      "Mark the work boundary and photograph current conditions.",
      "Stage matched materials and safety equipment before demolition or install.",
      "Perform rough work, inspect alignment, then close finishes."
    ],
    risks: [
      "Hidden utilities or structural conflicts may change the method of work.",
      "Reserved or low-stock inventory may require substitution approval."
    ],
    nextSteps: [
      "Assign a field lead to verify measurements.",
      "Reserve highlighted inventory items.",
      "Capture an after photo for closeout documentation."
    ]
  };
}
