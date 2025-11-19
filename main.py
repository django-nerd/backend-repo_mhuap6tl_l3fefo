import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import ModelSpec, Deployment, GenerationJob, User, Product

app = FastAPI(title="AI Model Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Platform backend is live"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Utilities

def _collection_name(model_cls: Any) -> str:
    return model_cls.__name__.lower()


def _to_public(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

# Schemas endpoint for viewer tooling
@app.get("/schema")
def get_schema_definitions():
    return {
        "models": [
            "user",
            "product",
            "modelspec",
            "deployment",
            "generationjob",
        ]
    }

# AI Platform Endpoints

class PromptRequest(BaseModel):
    prompt: str
    parameters: Optional[Dict[str, Any]] = None

@app.post("/api/generate", status_code=201)
def generate_model(req: PromptRequest):
    # Create a GenerationJob entry as running
    job = GenerationJob(prompt=req.prompt, status="running", model_id=None)
    job_id = create_document(_collection_name(GenerationJob), job)

    # Simulate a quick synchronous generation for demo purposes
    model = ModelSpec(
        name=req.parameters.get("name", "Prompt Model") if req and req.parameters else "Prompt Model",
        prompt=req.prompt,
        version="v1",
        status="ready",
        parameters=req.parameters or {},
        artifacts=["weights://mock/model.bin", "tokenizer://mock/vocab.json"],
    )
    model_id = create_document(_collection_name(ModelSpec), model)

    # Update job to completed
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    db[_collection_name(GenerationJob)].update_one({"_id": ObjectId(job_id)}, {"$set": {"status": "completed", "model_id": model_id}})

    return {"job_id": job_id, "model_id": model_id}

@app.get("/api/models")
def list_models(limit: int = 50):
    docs = get_documents(_collection_name(ModelSpec), limit=limit)
    return [_to_public(d) for d in docs]

class DeployRequest(BaseModel):
    model_id: str
    name: Optional[str] = None

@app.post("/api/deploy", status_code=201)
def deploy_model(req: DeployRequest):
    # Verify model exists
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    model = db[_collection_name(ModelSpec)].find_one({"_id": ObjectId(req.model_id)})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    deployment = Deployment(
        model_id=req.model_id,
        name=req.name or f"deployment-{req.model_id[-6:]}",
        url=f"{os.getenv('PUBLIC_BACKEND_URL', '')}/serve/{req.model_id}",
        status="active",
    )
    dep_id = create_document(_collection_name(Deployment), deployment)
    return {"deployment_id": dep_id}

@app.get("/api/deployments")
def list_deployments(limit: int = 50):
    docs = get_documents(_collection_name(Deployment), limit=limit)
    return [_to_public(d) for d in docs]

@app.get("/serve/{model_id}")
def serve_model(model_id: str, q: Optional[str] = None):
    # Placeholder serving that just echoes a response
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    model = db[_collection_name(ModelSpec)].find_one({"_id": ObjectId(model_id)})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_id": model_id,
        "status": "ok",
        "output": f"Model '{model.get('name', 'Model')}' responded to: {q or 'ping'}"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
