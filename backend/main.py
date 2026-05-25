import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from schema import (
    GenerateTextRequest, GenerateTextResponse,
    GenerateImageRequest, GenerateImageResponse,
    ImproveTextRequest, ImproveTextResponse,
    PostDB, RefinedPostDB, BrandProfileRequest, BrandProfileDB
)
from ai_engine import generate_content, improve_content, generate_matching_image
from supabase import create_client, Client

load_dotenv()

app = FastAPI(
    title="AI Content Marketing Suite API",
    description="REST API for generating and managing AI content and images.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)
)
def execute_supabase(query):
    return query.execute()

@app.post("/api/generate-text", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    try:
        brand_profile_dict = {}
        if supabase:
            profile_res = execute_supabase(supabase.table("brand_profiles").select("*").eq("session_id", request.session_id))
            if profile_res.data:
                brand_profile_dict = profile_res.data[0]

        # Generate the text via LangChain/DeepSeek
        text = generate_content(
            topic=request.topic,
            tone=request.tone,
            audience=request.audience,
            content_type=request.content_type,
            description=request.description or "",
            brand_profile=brand_profile_dict
        )
        
        # Save initial post to Supabase
        post_id = str(uuid.uuid4())
        post_data = {
            "id": post_id,
            "session_id": request.session_id,
            "topic": request.topic,
            "tone": request.tone,
            "audience": request.audience,
            "content_type": request.content_type,
            "generated_text": text,
            "description": request.description or None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if supabase:
            execute_supabase(supabase.table("posts").insert(post_data))
            
        return GenerateTextResponse(id=post_id, text=text, post_id=post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    try:
        # Generate image via OpenRouter Seedream model
        image_url = await generate_matching_image(
            topic=request.topic,
            tone=request.tone,
            generated_text=request.text,
            image_prompt=request.image_prompt or ""
        )
        
        # Update post in Supabase
        if supabase:
            update_data = {"image_url": image_url}
            if request.image_prompt:
                update_data["image_prompt"] = request.image_prompt
            execute_supabase(supabase.table("posts").update(update_data).eq("id", request.post_id))
            
        return GenerateImageResponse(post_id=request.post_id, image_url=image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/improve-text", response_model=ImproveTextResponse)
async def improve_text(request: ImproveTextRequest):
    try:
        # Refine text via LangGraph multi-step workflow
        result = improve_content(text=request.text, goal=request.goal)
        
        post_id = str(uuid.uuid4())
        post_data = {
            "id": post_id,
            "session_id": request.session_id,
            "original_text": request.text,
            "goal": request.goal,
            "refined_text": result["refined_text"],
            "explanation": result["explanation"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if supabase:
            execute_supabase(supabase.table("refined_posts").insert(post_data))
        
        return ImproveTextResponse(
            original_text=request.text,
            refined_text=result["refined_text"],
            explanation=result["explanation"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history", response_model=List[PostDB])
async def get_history(session_id: str = Query(...)):
    if not supabase:
        return []
    try:
        response = execute_supabase(supabase.table("posts").select("*").eq("session_id", session_id).order("created_at", desc=True))
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/{post_id}")
async def delete_history(post_id: str, session_id: str = Query(...)):
    if not supabase:
        return {"status": "success", "message": f"Deleted {post_id} (mock)"}
    try:
        execute_supabase(supabase.table("posts").delete().eq("id", post_id).eq("session_id", session_id))
        return {"status": "success", "message": f"Deleted {post_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/refined", response_model=List[RefinedPostDB])
async def get_refined_history(session_id: str = Query(...)):
    if not supabase:
        return []
    try:
        response = execute_supabase(supabase.table("refined_posts").select("*").eq("session_id", session_id).order("created_at", desc=True))
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/history/refined/{post_id}")
async def delete_refined_history(post_id: str, session_id: str = Query(...)):
    if not supabase:
        return {"status": "success", "message": f"Deleted {post_id} (mock)"}
    try:
        execute_supabase(supabase.table("refined_posts").delete().eq("id", post_id).eq("session_id", session_id))
        return {"status": "success", "message": f"Deleted {post_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/settings")
async def get_settings(session_id: str = Query(...)):
    if not supabase:
        return None
    try:
        response = execute_supabase(supabase.table("brand_profiles").select("*").eq("session_id", session_id))
        return response.data[0] if response.data else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/settings")
async def save_settings(request: BrandProfileRequest):
    if not supabase:
        return {"status": "error", "message": "Supabase not configured"}
    try:
        data = request.model_dump(exclude_unset=True)
        execute_supabase(supabase.table("brand_profiles").upsert(data))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/settings")
async def delete_settings(session_id: str = Query(...)):
    if not supabase:
        return {"status": "error", "message": "Supabase not configured"}
    try:
        execute_supabase(supabase.table("brand_profiles").delete().eq("session_id", session_id))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

