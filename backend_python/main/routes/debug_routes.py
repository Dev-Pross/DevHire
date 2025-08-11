# backend_python/main/debug_routes.py
import os
import base64
import tempfile
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from playwright.sync_api import sync_playwright

router = APIRouter(prefix="/debug", tags=["debug"])

# Use cross-platform temp directory
TEMP_DIR = tempfile.gettempdir()
PNG_PATH = os.path.join(TEMP_DIR, "snap.png")
HTML_PATH = os.path.join(TEMP_DIR, "snap.html")

@router.get("/capture")
def capture(url: str = Query(...)):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--no-zygote"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            page.goto(url, wait_until="domcontentloaded")
            
            # Ensure temp directory exists
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            # Save HTML
            html = page.content()
            with open(HTML_PATH, "w", encoding="utf-8") as f:
                f.write(html)
                
            # Save screenshot - this will actually work on Windows now
            page.screenshot(path=PNG_PATH, full_page=True)
            
            context.close()
            browser.close()
            
            # Verify files were created
            png_exists = os.path.exists(PNG_PATH)
            html_exists = os.path.exists(HTML_PATH)
            
            return JSONResponse({
                "message": "captured successfully",
                "html_snippet": html[:1000],
                "screenshot_saved": png_exists,
                "html_saved": html_exists,
                "png_path": PNG_PATH,
                "html_path": HTML_PATH
            })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/screenshot")
def get_screenshot():
    if os.path.exists(PNG_PATH):
        return FileResponse(PNG_PATH, media_type="image/png", filename="cloud_page.png")
    raise HTTPException(status_code=404, detail=f"screenshot not found at {PNG_PATH}")

@router.get("/html")
def get_html():
    if os.path.exists(HTML_PATH):
        return FileResponse(HTML_PATH, media_type="text/html", filename="cloud_page.html")
    raise HTTPException(status_code=404, detail=f"html not found at {HTML_PATH}")
