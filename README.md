# PureConstruct AI

Native SwiftUI construction assistant for field photo annotation and review.

## Backend setup

The active backend is Python FastAPI. It renders annotations with OpenCV, uses OpenInfer for annotation specs, and persists image assets in MongoDB/GridFS.

```sh
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in:

- `MONGODB_URI`
- `MONGODB_DB`
- `OPENINFER_API_KEY`

Run the API from the repository root:

```sh
PYTHONPATH=backend backend/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a physical iPhone, set the app's Backend URL field to the Mac's LAN address and the selected port, for example `http://192.168.1.176:8000`.

## Runtime storage

Production defaults are:

- `MODEL_PROVIDER=openinfer`
- `PERSISTENCE_BACKEND=mongo`

OpenCV and OpenInfer still require temporary image files while processing a request, but those files are created in the system temp directory and removed after the request. Original and rendered images are stored in MongoDB/GridFS, not under `backend/storage`.
