import fitz
import re
import sys
import requests

def extract_pdf_text_from_url(url: str) -> str:
    """Fetches a PDF from a URL and extracts text using PyMuPDF (fitz) with OCR fallback and hyperlink mapping."""
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    pdf_bytes = r.content

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    raw_url_regex = re.compile(r'https?://[^\s]+|www\.[^\s]+')

    for page_num, page in enumerate(doc):
        # 1. Fallback to OCR if page has no standard text layer
        text_blocks = page.get_text("blocks")
        has_text = any(b[4].strip() for b in text_blocks)

        if not has_text:
            try:
                ocr_page = page.get_textpage_ocr(flags=3, language="eng", dpi=300)
                text_blocks = ocr_page.extractBLOCKS()
            except Exception as e:
                print(f"[Warning] OCR failed on page {page_num + 1}: {e}", file=sys.stderr)
                text_blocks = []

        # 2. Map links to their exact text block using spatial coordinates
        page_links = page.get_links()
        page_output = []

        if text_blocks:
            for block in text_blocks:
                bx0, by0, bx1, by1, block_content, _, _ = block
                clean_content = block_content.strip()

                if not clean_content:
                    continue

                # Find links that overlap with this specific block's boundary box
                matched_links = []
                for link in page_links:
                    if "uri" in link:
                        lx0, ly0, lx1, ly1 = link["from"]
                        # Check collision/intersection
                        if (bx0 <= lx1 and bx1 >= lx0 and by0 <= ly1 and by1 >= ly0):
                            url_match = link["uri"].strip()
                            # Grab text strictly inside the link's bounding box
                            anchor_text = page.get_text("text", clip=link["from"]).strip()
                            anchor_clean = anchor_text.strip(" :,.-•[]()")
                            
                            if anchor_clean and not raw_url_regex.search(anchor_clean):
                                matched_links.append((anchor_clean, url_match))

                # 3. Process links locally inside the text block to prevent global overlap errors
                if matched_links:
                    # Sort matched links right-to-left or bottom-to-top to avoid offset shifting issues
                    for anchor, url_match in sorted(matched_links, key=lambda x: len(x[0]), reverse=True):
                        # Construct key-value format
                        replacement = f"{anchor}: {url_match}"
                        
                        # Replace only the FIRST occurrence within this specific paragraph block
                        # This safely splits up duplicate links like "[Link]" across multiple rows
                        if anchor in clean_content and f": {url_match}" not in clean_content:
                            clean_content = clean_content.replace(anchor, replacement, 1)

                page_output.append(clean_content)

        full_text += "\n".join(page_output) + "\n\n"

    doc.close()
    return full_text
