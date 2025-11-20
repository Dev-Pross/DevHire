# backend_python/main/debug_routes.py
import os
import base64
import tempfile
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
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
                
            # Save screenshot
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

# NEW: Get all debug images from scraper runs
@router.get("/all-scraper-images")
def get_all_scraper_debug_images():
    """Return all debug images captured by the scraper as base64"""
    temp_dir = tempfile.gettempdir()
    debug_images = []
    
    try:
        # Look for all debug files created by your scraper
        for filename in os.listdir(temp_dir):
            if filename.startswith("debug_") and filename.endswith(".png"):
                file_path = os.path.join(temp_dir, filename)
                
                # Read image and convert to base64
                with open(file_path, "rb") as f:
                    img_data = f.read()
                    img_b64 = base64.b64encode(img_data).decode("utf-8")
                
                # Parse filename for info
                parts = filename.replace(".png", "").split("_")
                step_name = parts[1] if len(parts) > 1 else "unknown"
                job_title = "_".join(parts[2:-1]) if len(parts) > 3 else ""
                timestamp = parts[-1] if len(parts) > 1 else ""
                
                debug_images.append({
                    "filename": filename,
                    "step": step_name,
                    "job_title": job_title.replace("_", " "),
                    "timestamp": timestamp,
                    "image_b64": f"data:image/png;base64,{img_b64}",
                    "size": len(img_data),
                    "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
        
        # Sort by creation time (newest first)
        debug_images.sort(key=lambda x: x['created'], reverse=True)
        
        return JSONResponse({
            "success": True,
            "total_images": len(debug_images),
            "debug_images": debug_images
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "total_images": 0,
            "debug_images": []
        })

# NEW: Get recent debug images (from last scraper run)
@router.get("/recent-images")
def get_recent_debug_images(minutes: int = Query(5, description="Get images from last N minutes")):
    """Get debug images from recent scraper runs"""
    temp_dir = tempfile.gettempdir()
    debug_images = []
    cutoff_time = datetime.now().timestamp() - (minutes * 60)
    
    try:
        for filename in os.listdir(temp_dir):
            if filename.startswith("debug_") and filename.endswith(".png"):
                file_path = os.path.join(temp_dir, filename)
                
                # Check if file is recent
                if os.path.getctime(file_path) > cutoff_time:
                    with open(file_path, "rb") as f:
                        img_data = f.read()
                        img_b64 = base64.b64encode(img_data).decode("utf-8")
                    
                    parts = filename.replace(".png", "").split("_")
                    step_name = parts[1] if len(parts) > 1 else "unknown"
                    job_title = "_".join(parts[2:-1]) if len(parts) > 3 else ""
                    
                    debug_images.append({
                        "filename": filename,
                        "step": step_name,
                        "job_title": job_title.replace("_", " "),
                        "image_b64": f"data:image/png;base64,{img_b64}",
                        "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                    })
        
        debug_images.sort(key=lambda x: x['created'])
        
        return JSONResponse({
            "success": True,
            "minutes_searched": minutes,
            "total_images": len(debug_images),
            "debug_images": debug_images
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "debug_images": []
        })

# NEW: Simple gallery view
@router.get("/gallery")
def debug_gallery():
    """HTML gallery to view all debug screenshots"""
    temp_dir = tempfile.gettempdir()
    screenshots = []
    
    try:
        for filename in os.listdir(temp_dir):
            if filename.startswith("debug_") and filename.endswith(".png"):
                screenshots.append({
                    "filename": filename,
                    "created": datetime.fromtimestamp(os.path.getctime(os.path.join(temp_dir, filename))).strftime("%H:%M:%S")
                })
        
        screenshots.sort(key=lambda x: x['filename'])
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scraper Debug Screenshots</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 20px; }
                .item { background: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .item img { max-width: 100%; height: auto; border: 1px solid #eee; }
                .filename { font-weight: bold; margin-bottom: 10px; color: #333; }
                .time { font-size: 12px; color: #666; margin-bottom: 10px; }
                h1 { color: #333; }
                .refresh { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .refresh:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <h1>🔍 Scraper Debug Screenshots</h1>
            <button class="refresh" onclick="location.reload()">🔄 Refresh</button>
            <p>Total screenshots: <strong>""" + str(len(screenshots)) + """</strong></p>
            <div class="gallery">
        """
        
        for screenshot in screenshots:
            html_content += f"""
                <div class="item">
                    <div class="filename">{screenshot['filename']}</div>
                    <div class="time">📅 {screenshot['created']}</div>
                    <img src="/debug/capture/{screenshot['filename']}" alt="{screenshot['filename']}" loading="lazy">
                    <br><br>
                    <a href="/debug/capture/{screenshot['filename']}" target="_blank" style="color: #007bff;">🔗 Open Full Size</a>
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")

# NEW: Clear old debug files
@router.delete("/clear-debug")
def clear_debug_files(older_than_hours: int = Query(1, description="Delete files older than N hours")):
    """Clear old debug files"""
    temp_dir = tempfile.gettempdir()
    deleted_files = []
    cutoff_time = datetime.now().timestamp() - (older_than_hours * 604800) #week
    
    try:
        for filename in os.listdir(temp_dir):
            if filename.startswith("debug_") and (filename.endswith(".png") or filename.endswith(".html")):
                file_path = os.path.join(temp_dir, filename)
                
                if os.path.getctime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_files.append(filename)
        
        return JSONResponse({
            "success": True,
            "deleted_files": deleted_files,
            "count": len(deleted_files)
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })
