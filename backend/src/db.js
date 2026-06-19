import { MongoClient } from "mongodb";

let client;
let database;

export async function getDb() {
  if (database) return database;

  const uri = process.env.MONGODB_URI;
  if (!uri) {
    throw new Error("MONGODB_URI is not configured");
  }

  client = new MongoClient(uri);
  await client.connect();
  database = client.db(process.env.MONGODB_DB || "pureconstruct_ai");

  await database.collection("inventory").createIndex({ name: "text", category: "text", tags: "text" });
  await database.collection("reports").createIndex({ createdAt: -1 });

  return database;
}

export async function closeDb() {
  if (client) {
    await client.close();
    client = undefined;
    database = undefined;
  }
}
