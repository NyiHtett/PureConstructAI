import "dotenv/config";
import { closeDb, getDb } from "./db.js";
import { sampleInventory } from "./sampleData.js";

try {
  const db = await getDb();
  const now = new Date();
  await db.collection("inventory").deleteMany({});
  await db.collection("inventory").insertMany(sampleInventory.map((item) => ({ ...item, updatedAt: now })));
  console.log(`Seeded ${sampleInventory.length} inventory items`);
} finally {
  await closeDb();
}
