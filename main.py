import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FlyerInput(BaseModel):
    EVENT_TITLE: str = Field(..., description="Title of the event")
    EVENT_TYPE: str = Field(..., description="Type of the event")
    LOCALITY: str = Field(..., description="City/Locality context")
    MAIN_IMAGE_ID: str = Field(..., description="Asset ID for main image")
    SECONDARY_IMAGES_COUNT: int = Field(..., ge=0, le=12, description="Number of supplemental images")
    CUSTOM_FONT: str = Field(..., description="Font name to align the style")
    CUSTOM_COLOR_SCHEME: str = Field(..., description="Primary palette, e.g., Hex list or brand name")


class FlyerOutput(BaseModel):
    image_generation_prompt: str
    image_editing_tasks: str


def build_generation_prompt(data: FlyerInput) -> str:
    # Keep within ~200 words; one paragraph
    prompt = (
        f"Design a full-page flyer background for '{data.EVENT_TITLE}', a {data.EVENT_TYPE} in {data.LOCALITY}, "
        f"expressed as an academic–minimalist composition aligned to the rule of thirds with an upper-left title zone "
        f"and a lower-right information zone, using generous negative space and clean alignment. Employ soft, diffused "
        f"cinematic lighting with subtle depth and gentle vignetting to guide focus. Style should harmonize with the typography "
        f"character of {data.CUSTOM_FONT} and be driven by {data.CUSTOM_COLOR_SCHEME} as the dominant palette, with refined accent tones "
        f"and print-friendly gradients. Incorporate abstract campus or architectural silhouettes that nod to {data.LOCALITY} as low-contrast, layered shapes "
        f"so the central subject cutout remains clear. Include delicate geometric guide lines that echo the typographic rhythm, keeping textures "
        f"fine-grained and paper-safe. Leave balanced margins for the headline, event details, and footer without clutter. Render at 8K, HDR, ultra-sharp, "
        f"color-accurate, CMYK-aware, print-ready, with crisp edges and minimal banding; ensure the composition can accommodate the primary portrait asset while maintaining visual balance for both digital and physical outputs."
    )
    return prompt[:1800]  # safety margin under 200 words (approx), but ensure not overly truncated


def build_editing_tasks(data: FlyerInput) -> str:
    count = max(0, int(data.SECONDARY_IMAGES_COUNT))
    tasks = [
        "1) Load the main image using [MAIN_IMAGE_ID].".replace('[MAIN_IMAGE_ID]', data.MAIN_IMAGE_ID),
        "2) Apply realistic facial enhancement (clarity, skin accuracy, natural texture).",
        "3) Remove and replace the background with the theme generated in Section 1.",
        f"4) Apply global color harmonization using {data.CUSTOM_COLOR_SCHEME}.",
        "5) Enhance contrast, brightness, and vibrance across all assets.",
        "6) Position the main image as the primary focal point (center-left, rule of thirds).",
        f"7) Insert {count} supplemental images using grid-balanced layout rules.",
        "8) Create a professional flyer layout (title zone, information zone, footer) with clean spacing.",
        f"9) Add {data.EVENT_TITLE} using {data.CUSTOM_FONT}, ensuring high readability.",
        "10) Add placeholder areas for date, venue, and event details (admin fills later).",
        "11) Ensure all text maintains proper contrast against the background.",
        "12) Render the final output as a high-resolution, print-ready file (300 DPI minimum).",
        "13) Optimize final output for both digital display and physical printing.",
    ]
    return "\n".join(tasks)


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.post("/api/generate_flyer_prompt", response_model=FlyerOutput)
async def generate_flyer_prompt(payload: FlyerInput):
    prompt = build_generation_prompt(payload)
    tasks = build_editing_tasks(payload)
    return FlyerOutput(image_generation_prompt=prompt, image_editing_tasks=tasks)


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
