# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Code Review Env Environment.
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

from models import CodeReviewAction, CodeReviewObservation
from server.code_review_env_environment import CodeReviewEnvironment

# Create the app
app = create_app(
    CodeReviewEnvironment,
    CodeReviewAction,
    CodeReviewObservation,
    env_name="code_review_env",
    max_concurrent_envs=1,
)

# === HEALTH CHECK REQUIRED BY HF SPACES ===
# === HF SPACES FIX (VERY IMPORTANT) ===
import time
start_time = time.time()

@app.get("/")
async def root():
    return {
        "status": "running",
        "message": "Code Review Env is live 🚀",
        "uptime": round(time.time() - start_time, 2)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }
# ===========================================

import os

def main():
    import uvicorn

    port = int(os.environ.get("PORT", 8000))  
    print(f"🚀 Starting server on port {port}")

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    print("🚀 Server started successfully")
    main()