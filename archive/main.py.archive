import os
import uvicorn

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# Override CESIUM_DIR to point to the Vite build output (dist/) instead of source.
# __file__ = backend/main.py → 1 up = backend/ → frontend/cesium/dist
os.environ.setdefault(
    "CESIUM_DIR",
    os.path.abspath(os.path.join(PROJECT_ROOT, "..", "frontend", "cesium", "dist")),
)

if __name__ == "__main__":
    uvicorn.run("app.api.router:app", host="0.0.0.0", port=8000, reload=True)