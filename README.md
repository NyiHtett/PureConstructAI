# PureConstruct AI

Native SwiftUI construction assistant for hackathon field demos. The app sends a job-site image and requested modification text to a Node API, which calls OpenInfer and stores reports plus inventory in MongoDB.

## Branch

Implementation branch: `codex-nyi`

## Backend setup

```sh
cd backend
npm install
cp .env.example .env
```

Fill in:

- `MONGODB_URI`
- `MONGODB_DB`
- `OPENINFER_API_KEY`

Seed sample inventory:

```sh
npm run seed
```

Run the API:

```sh
npm run dev
```

The iOS app currently calls `http://localhost:8787/api`, which works for the iOS Simulator when the backend runs on the same Mac. For a physical device, change `baseURL` in `ConstructionAPI` to the Mac's LAN address.

## OpenInfer

The backend uses:

- Endpoint: `https://platform.openinfer.io/v1/responses`
- Model: `@oi/beta`
- Streaming: `stream: true`

If `OPENINFER_API_KEY` is missing, the backend returns a fallback structured report so the demo flow remains usable while setup is in progress.
