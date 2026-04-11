import os
import time

from fastapi import Request

from openenv.core.env_server.http_server import create_app

from models import CodeReviewAction, CodeReviewObservation
from .code_review_env_environment import CodeReviewEnvironment   # ← Fixed import

start_time = time.time()

# Create the OpenEnv app
app = create_app(
    CodeReviewEnvironment,
    CodeReviewAction,
    CodeReviewObservation,
    env_name="code_review_env",
    max_concurrent_envs=1,
)

# Root endpoint (required for HF)
@app.get("/")
async def root():
    return {
        "status": "running",
        "uptime": round(time.time() - start_time, 2)
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# MAIN FUNCTION
def main():
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
