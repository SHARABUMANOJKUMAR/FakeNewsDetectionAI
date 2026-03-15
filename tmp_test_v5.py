import requests
from bs4 import BeautifulSoup
import feedparser

trusted_rss = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://www.reuters.com/rssFeed/topNews",
    "https://www.ndtv.com/rss",
    "http://rss.cnn.com/rss/edition.rss"
]

def verify_with_google_news(text):
    query = text[:80]
    print(f"\n[?] Testing Google News for: '{query}'")
    try:
        url = f"https://www.google.com/search?q={query}&tbm=nws" # Added &tbm=nws for News tab
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=5)
        print(f"[*] Response Code: {r.status_code}")
        
        soup = BeautifulSoup(r.text, "html.parser")
        # Google News results are often in <div> with specific classes
        articles = soup.find_all("div", attrs={"role": "heading"})
        if not articles:
            # Fallback for standard search results if news tab is different
            articles = soup.find_all("h3")
            
        print(f"[*] Found {len(articles)} potential article links.")
        return len(articles) > 3
    except Exception as e:
        print(f"[!] Google News error: {e}")
    return False

def verify_with_rss(text):
    query = " ".join(text.split()[:4]).lower() # Reduced snippet length for better matching
    print(f"\n[?] Testing RSS search for query snippet: '{query}'")
    for rss_url in trusted_rss:
        try:
            feed = feedparser.parse(rss_url)
            print(f"[*] Checking {rss_url} ({len(feed.entries)} entries)")
            for entry in feed.entries:
                title = entry.title.lower()
                if query in title:
                    print(f"[+] Match found in RSS: {entry.title}")
                    return True
        except Exception as e:
            print(f"[!] RSS error for {rss_url}: {e}")
    return False

# Test cases with currently trending/known news
test_real = "Bitcoin" 
test_fake = "The moon is made of blue cheese and controlled by cats"

print("\n=== STARTING VERIFICATION V2 ===")
print(f"REAL NEWS result: {verify_with_google_news(test_real)}")
print(f"FAKE NEWS result: {verify_with_google_news(test_fake)}")

# RSS requires specific title matches, so we skip general test or use a very common word
print(f"RSS Generic Check (World): {verify_with_rss('World')}")
