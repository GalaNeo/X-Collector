#   X Collector

A lightweight Selenium-based scraper for collecting tweet information from [X (Twitter)](https://x.com).  
Originally designed for learning and experimentation around **sentiment analysis**.

---

##  Features
- Uses **[Selenium](https://www.selenium.dev/documentation/)** and **[BeautifulSoup4](https://pypi.org/project/beautifulsoup4/)** to collect and parse X posts/replies.  
- Saves results to a clean, deduplicated **CSV** file.  
- Fully **manual login flow** (bypasses automation detection).  
- Includes configurable parameters for scroll depth, tweet count targets, and timing.  
- Simple, readable structure -> easy to modify or extend.

---

##  How It Works
The script launches a Chromium-based browser (e.g., Brave) and opens the X login page.  
You manually log in, then confirm in the terminal to let Selenium attach and begin scraping.

This manual flow avoids detection that occurs when Selenium is attached during login,  
while still allowing automated scrolling and tweet collection afterwards.  

*(An optional automated login block is included in the code for experimentation — use at your own risk, as X.com may detect it.)*

Once scraping begins, tweet information is extracted, cleaned, and saved as a CSV for later analysis.

Collected tweet fields include:
```python
{
    "author": str,
    "text": str,
    "mentions": str,
    "timestamp": str,
    "tweet_id": str,
    "tweet_url": str,
    "replies": int,
    "reposts": int,
    "likes": int,
    "bookmarks": int,
    "views": int,            
}
```
---

##  Setup & Usage

### Prerequisites
You’ll need:
- **Python 3.9+**
- A **Chromium-based browser** (e.g. Brave, Chrome, or Edge)
- A **ChromeDriver** compatible with your browser version
- The necessary adjustments in code for the path of your browser

---

### Install dependencies
Clone this repository and install the required libraries:

```bash
git clone https://github.com/GalaNeo/X-Collector.git
cd X-Collector
pip install -r requirements.txt
```

---

### Launch the browser

- The script automatically opens Brave (or your configured browser) to the X login page using remote debugging mode.
- You can modify the browser path or target search URL in the configuration section near the top of X_Collector.py.

---

### Log in manually

Once the browser window appears:
- Enter your username or email and your password
- After you’ve successfully logged in, return to the terminal and press any input to continue

This step is essential to avoid Selenium being detected during authentication.

---

### Data collection

After you confirm login, the scraper attaches to your active session and begins collecting tweets based on the SEARCH_URL.
Collected tweets are saved to: ```data/raw/mentions.csv```

If this file already exists, new tweets are merged and duplicates removed automatically.

---

### Customizing behavior

At the top of X_Collector.py, you can tune the scraper with these parameters:

```
SEARCH_URL = "https://x.com/search?q=elon%20musk&src=recent_search_click&f=live"
OUTPUT_CSV = Path("data/raw/mentions.csv")
SCROLL_PAUSE = 2.5
TARGET_NEW_TWEETS = 100
MAX_SCROLLS_WITHOUT_NEW = 10
HARD_LIMIT = True
```

- SEARCH_URL — change the X search query or user feed you want to collect
- SCROLL_PAUSE — delay (in seconds) between scrolls
- TARGET_NEW_TWEETS — number of new tweets to collect before stopping
- MAX_SCROLLS_WITHOUT_NEW — how many scrolls to perform before quitting if no new tweets are found
- HARD_LIMIT — if True, stops at TARGET_NEW_TWEETS; if False, continues until no new tweets appear

---

### Output example

The final CSV will look something like this:

| Author          | Text (Truncated)                                                                                                | Mentions        | Timestamp                | Tweet ID            | URL                                                             | Replies | Reposts | Likes | Bookmarks |   Views |
| :-------------- | :-------------------------------------------------------------------------------------------------------------- | :-------------- | :----------------------- | :------------------ | :-------------------------------------------------------------- | ------: | ------: | ----: | --------: | ------: |
| @elonmuskADO    | *Fan Elon Musk · 13h Parody account Eye test I know 99% of you will fail this Question What number do you see?* | @elonmuskADO    | 2025-11-08T06:19:31.000Z | 1987042279471681600 | [Link](https://x.com/elonmuskADO/status/1987042279471681600)    |     553 |      46 |   212 |        12 |   20831 |
| @elonmusknews30 | *Almost half of Americans don’t like Elon Musk — if you like him leave a red heart or thumbs up*                | @elonmusknews30 | 2025-11-07T13:50:33.000Z | 1986793397961506944 | [Link](https://x.com/elonmusknews30/status/1986793397961506944) |    3216 |     808 |  9543 |        50 |  111290 |
| @CrewsMat10     | *Elon Musk has changed the like button to celebrate Halloween #halloween*                                       | @CrewsMat10     | 2025-11-01T15:49:06.000Z | 1984648906056294687 | [Link](https://x.com/CrewsMat10/status/1984648906056294687)     |     258 |     907 | 85828 |       596 | 1665832 |

---

## Future Plans
Originally designed for collecting tweets for **sentiment analysis**.
Next steps include:
- Using **NLTK** to classify sentiment
- Tracking engagement trends over time
- Visualizing tweet activity by keyword

---

### Notes
- The collector depends on X.com’s current HTML structure.  
  If X changes their page layout, certain extraction functions (e.g., metrics or timestamps) may stop working.  
  Check `extract_metrics()` or `extract_tweet_info()` for the relevant parsing logic if you need to update it.
- This project is intended for **educational and research purposes** only.
