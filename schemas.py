"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# AI Platform Schemas

class ModelSpec(BaseModel):
    """Represents a trained or generated model."""
    name: str = Field(..., description="Display name for the model")
    prompt: str = Field(..., description="Prompt or instructions the model was created from")
    version: str = Field("v1", description="Semantic version of the model")
    status: str = Field("ready", description="Status of the model: queued|training|ready|failed")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    artifacts: Optional[List[str]] = Field(default_factory=list, description="List of artifact URIs")

class Deployment(BaseModel):
    """Represents a deployment of a model to a serving endpoint."""
    model_id: str = Field(..., description="ID of the model being deployed")
    name: str = Field(..., description="Deployment name")
    url: Optional[str] = Field(None, description="Public URL for serving")
    status: str = Field("active", description="Deployment status: provisioning|active|error|stopped")

class GenerationJob(BaseModel):
    """Represents a background job to generate a model from a prompt."""
    prompt: str = Field(..., description="Prompt to generate the model")
    status: str = Field("completed", description="Job status: queued|running|completed|failed")
    model_id: Optional[str] = Field(None, description="Resulting model id, if completed")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
