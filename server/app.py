import os
import time

start_time = time.time()

# your existing imports...
from openenv.core.env_server.http_server import create_app
from models import CodeReviewAction, CodeReviewObservation
from server.code_review_env_environment import CodeReviewEnvironment

app = create_app(
    CodeReviewEnvironment,
    CodeReviewAction,
    CodeReviewObservation,
    env_name="code_review_env",
    max_concurrent_envs=1,
)

# ROOT ENDPOINT (CRITICAL)
@app.get("/")
async def root():
    return {
        "status": "running",
        "uptime": round(time.time() - start_time, 2)
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# MAIN FUNCTION (CRITICAL)
def main():
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f" Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
