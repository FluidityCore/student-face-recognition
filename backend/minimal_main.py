#!/usr/bin/env python3
from fastapi import FastAPI
import os
import sys
import time

app = FastAPI(title="Railway Debug Test")

@app.get("/")
async def root():
    print(f"🔍 Root endpoint called - {time.time()}")
    sys.stdout.flush()
    return {"status": "working", "message": "Minimal app funcionando!", "server": "Railway"}

@app.get("/test")
async def test():
    print(f"🧪 Test endpoint called - {time.time()}")
    sys.stdout.flush()
    return {"test": "ok", "python_version": sys.version}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)