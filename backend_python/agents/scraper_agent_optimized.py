import asyncio
import aiohttp
from bs4 import BeautifulSoup # Import Beautiful Soup

async def fetch_and_parse_job_details(session: aiohttp.ClientSession, url: str):
    """
    Fetches the HTML of a URL and then parses it to extract
    the text content of the element with id='job-details'.
    """
    print(f"🚀 Fetching: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                html_content = await response.text()
                print("   ✅ HTML fetched successfully.")

                # --- PARSING STEP ---
                print("   🥣 Parsing HTML with Beautiful Soup...")
                soup = BeautifulSoup(html_content, 'lxml')

                # Find the specific element by its ID
                # On LinkedIn, the job description is in a div with a class, not an ID.
                # Let's use the class from your previous scraper for a real example.
                job_details_div = soup.find('div', class_='show-more-less-html__markup')

                if job_details_div:
                    # Get all the text from the element, stripped of HTML tags
                    job_text = job_details_div.get_text(separator=' ', strip=True)
                    print("   ✅ Extracted content successfully!")
                    return url, job_text
                else:
                    return url, "Failed: Could not find the job description element in the HTML."
            else:
                return url, f"Failed: HTTP status {response.status}"
    except Exception as e:
        return url, f"Failed: An error occurred - {str(e)}"

# --- MAIN ORCHESTRATOR ---
async def main():
    job_urls_to_process = [
        "https://www.linkedin.com/jobs/view/4318073630/",
        'https://www.linkedin.com/jobs/view/4319141548/',
        'https://www.linkedin.com/jobs/view/4319282947/',
    ]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_parse_job_details(session, url) for url in job_urls_to_process]
        results = await asyncio.gather(*tasks)

    print("\n\n--- 📝 FINAL EXTRACTED CONTENT ---")
    for url, content in results:
        print(f"\nURL: {url}")
        if "Failed" in content:
            print(f"Error: {content}")
        else:
            print(f"Extracted Text: {content}") # Print first 300 characters

if __name__ == "__main__":
    asyncio.run(main())