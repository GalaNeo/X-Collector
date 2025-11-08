import time
import subprocess
import json
from pathlib import Path
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# ---------- CONFIG ----------

"""
SEARCH_URL: Add a custom URL/Query to scrape 
    (Example: https://x.com/search?q=elon%20musk&src=recent_search_click&f=live)
    
OUTPUT_CSV: Path where the collected tweets will be saved in CSV format.
SCROLL_PAUSE: Seconds to pause between scrolls (recommended >2).
TARGET_NEW_TWEETS: Number of new tweets to collect before stopping (if HARD_LIMIT=True). Accounts for dupes.
MAX_SCROLLS_WITHOUT_NEW: Max scrolls allowed without finding new tweets before stopping.
DEBUGGER_ADDRESS: IP:port for attaching to a running browser via remote debugging.
HARD_LIMIT: If True, stop after TARGET_NEW_TWEETS. If False, scrolls until no new tweets.
"""

SEARCH_URL = (
    "https://x.com/search?q=elon%20musk&src=recent_search_click&f=live"
)
OUTPUT_CSV = Path("../data/raw/tweets.csv")
SCROLL_PAUSE = 2.5
TARGET_NEW_TWEETS = 10   # used if HARD_LIMIT=True
MAX_SCROLLS_WITHOUT_NEW = 10
DEBUGGER_ADDRESS = "127.0.0.1:9222"
HARD_LIMIT = True
# ----------------------------

# Make sure you add your own credentials in the settings.json to load
# with open(Path(__file__).parent.parent /"config"/ "settings.json") as f:
#     creds = json.load(f)
#
# EMAIL = creds["TWITTER_EMAIL"]
# PASSWORD = creds["TWITTER_PASSWORD"]

# Path to browser and profile folders
# Manually open session through CMD to avoid detection from X
cmd = f'"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" --remote-debugging-port=9222 --user-data-dir="C:\\SeleniumProfile" --start-maximized https://x.com/login'

subprocess.Popen(cmd, cwd="C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application")


# Initialize browser for automatic login
# options = webdriver.ChromeOptions()
# options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
# options.debugger_address = f"127.0.0.1:9222"
# driver = webdriver.Chrome(options=options)

# try:
#     # Go to X login page
#     driver.get("https://x.com/login")
#     time.sleep(10)
#
#     # Finds the name element and enters your name from settings.json
#     username_field = driver.find_element(By.NAME, "text")
#     username_field.send_keys(EMAIL)
#     username_field.send_keys(Keys.RETURN)
#     time.sleep(10)
#
#     # Finds the password element and enters your password from settings.json
#     password_field = driver.find_element(By.NAME, "password")
#     password_field.send_keys(PASSWORD)
#     password_field.send_keys(Keys.RETURN)
#     time.sleep(10)
#
# except:
#     driver.quit()

# --- X html structure changed making the function useless for now ---
# def parse_count(s: str) -> int:
#     """
#     Convert X short form counts like '1.2K', '3M', or '123' to integers.
#     Args:
#         s (str): The count string to parse, such as '2K', '11M' or '333'.
#
#     Returns:
#         int: The numeric value as an integer. Returns 0 if parsing fails.
#     """
#
#     if not s:
#         return 0
#     s = s.strip()
#     try:
#         return int(s.replace(",", "")) # Attempts direct conversion for plain numbers like '123'
#     except:
#         pass
#
#     # Handles K/M Suffixes
#     s = s.upper().replace(",", "").strip()
#     print("prints s", s)
#     match = re.match(r"([\d,.]+)([KM]?)", s)
#     print("prints the match", match)
#     if not match:
#         return 0
#     num, suffix = match.groups()
#     try:
#         val = float(num)
#     except:
#         return 0
#
#     if suffix == "K":
#         return int(val * 1_000)
#     if suffix == "M":
#         return int(val * 1_000_000)
#     return int(val)

def extract_mentions(text: str) -> list[str]:
    """
    Extract all unique @mentions from a tweet's text.

    Args:
        text (str): The full tweet text.

    Returns:
        list[str]: Unique @usernames found in the text in order of appearance.
    """
    # Find all @handles like @elonmusk
    mentions = re.findall(r"@[\w_]+", text)
    # Preserve order, remove duplicates
    return list(dict.fromkeys(mentions))

def extract_tweet_info(article):
    """
    Parse a BeautifulSoup <article> element and extract structured tweet information.

    Args:
        article: The HTML <article> tag representing a single tweet.

    Returns:
        dict | None: A dictionary containing the tweet data:
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

    """
    try:
        # Get all visible text inside the tweet
        full_text = article.get_text(" ", strip=True)

        # Extract @mentions and remove them from the visible text
        reply_mentions = extract_mentions(full_text)
        text_clean = full_text
        for m in reply_mentions:
            text_clean = text_clean.replace(m, "")
        text_clean = text_clean.strip()

        # Find tweet url / id
        tweet_link_tag = article.find("a", href=lambda s: s and "/status/" in s)
        tweet_url = ""
        tweet_id = ""
        if tweet_link_tag and tweet_link_tag.get("href"):
            href = tweet_link_tag["href"]
            tweet_url = href if href.startswith("http") else "https://x.com" + href
            tweet_id = href.rstrip("/").split("/")[-1]

        # Extract timestamp
        ttag = article.find("time")
        timestamp = ttag["datetime"] if ttag and ttag.has_attr("datetime") else ""

        # Identify author @handle
        author = "unknown"
        if tweet_link_tag:
            author_candidate = tweet_link_tag.find_previous("a", href=lambda s: s and s.startswith("/") and "/status/" not in s)
            if author_candidate and author_candidate.get_text():
                auth_text = author_candidate.get_text().strip()
                span_handle = article.find("span", string=lambda s: s and s.startswith("@"))
                author = span_handle.get_text().strip() if span_handle else auth_text

        # Extract engagement metrics (likes/reposts/views), added replies and bookmarks
        replies = reposts = likes = bookmarks = views = 0

        # Find the aria label containing metrics
        metrics_div = article.find(attrs={"aria-label": re.compile(r"replies|reposts|likes|bookmarks|views", re.I)})
        if not metrics_div:
            return replies, reposts, likes, bookmarks, views

        label = metrics_div["aria-label"].lower()

        # Extract numbers in order
        nums = re.findall(r"\d+", label)
        if len(nums) >= 5:
            replies, reposts, likes, bookmarks, views = map(int, nums[:5])

        # for elem in article.find_all(attrs={"aria-label": True}):
        #     label = elem["aria-label"].lower()

            # if "like" in label:
            #     likes = parse_count(re.sub(r"[^\dKMm,.]+", "", label))
            # elif "reposts" in label: # Updated to repost since X changed it and broke the code
            #     reposts = parse_count(re.sub(r"[^\dKMm,.]+", "", label))
            # elif "view" in label:
            #     views = parse_count(re.sub(r"[^\dKMm,.]+", "", label))

        # Return structured tweet data
        return {
            "author": author,
            "text": text_clean,
            "mentions": ",".join(reply_mentions),
            "timestamp": timestamp,
            "tweet_id": tweet_id,
            "tweet_url": tweet_url,
            "replies": replies,
            "reposts": reposts,
            "likes": likes,
            "bookmarks": bookmarks,
            "views": views,
        }
    except Exception as e:
        print("parse error:", e)
        return None

def main():
    """
    Launch a Selenium browser session, scrape tweets from the current page,
    and save them to a CSV file while avoiding duplicates.

    The function connects to an existing browser instance via remote debugging,
    parses all visible tweet <article> elements, extracts tweet metadata, and
    stores the results incrementally in OUTPUT_CSV.

    Behavior is controlled by configuration constants.

    Returns:
        None
    """
    input("Press any Input in the terminal after login in to initiate the program")
    print("Program begins")
    # --- Connect to existing browser session ---
    # Use remote debugging to attach Selenium to your already open Brave/Chrome instance.
    options = Options()
    options.debugger_address = DEBUGGER_ADDRESS
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(SEARCH_URL)
        time.sleep(5)

        # --- Load previously collected tweets ---
        existing_ids = set()
        if OUTPUT_CSV.exists():
            try:
                df_existing = pd.read_csv(OUTPUT_CSV, dtype=str)
                existing_ids = set(df_existing["tweet_id"].dropna().astype(str).tolist())
                print(f"Loaded {len(existing_ids)} existing tweet_ids from {OUTPUT_CSV}")
            except Exception as ex:
                print("Warning: couldn't read existing CSV:", ex)

        # --- Initialize containers and counters ---

        collected_new = []  # Stores new tweet dictionaries
        seen_ids_local = set() # Tracks IDs within this run to prevent duplicates
        scrolls_without_new = 0 # Counts consecutive scrolls with no new tweets

        # --- Main scraping loop ---
        while True:
            # Parse current HTML snapshot with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            articles = soup.find_all("article")

            new_found_this_scroll = 0
            for a in articles:
                info = extract_tweet_info(a)
                if not info:
                    continue
                tid = str(info.get("tweet_id", "")).strip()
                if not tid or tid in existing_ids or tid in seen_ids_local:
                    continue
                collected_new.append(info)
                seen_ids_local.add(tid)
                new_found_this_scroll += 1

                # Stop early if hard limit is reached
                if HARD_LIMIT and len(collected_new) >= TARGET_NEW_TWEETS:
                    break

            if new_found_this_scroll == 0:
                scrolls_without_new += 1
            else:
                scrolls_without_new = 0

            # --- Hard limit Stop conditions ---
            if HARD_LIMIT and len(collected_new) >= TARGET_NEW_TWEETS:
                print(f"Reached target of {TARGET_NEW_TWEETS} new tweets.")
                break
            if scrolls_without_new >= MAX_SCROLLS_WITHOUT_NEW:
                print("No new tweets found in last scrolls. Stopping.")
                break

            # --- Scroll page down to load more tweets ---
            driver.find_element("tag name", "body").send_keys(Keys.END)
            time.sleep(SCROLL_PAUSE)

        # --- Save results to CSV ---
        if collected_new:
            df_new = pd.DataFrame(collected_new)
            expected_cols = ["author","text","mentions","timestamp","tweet_id","tweet_url","replies","reposts","likes","bookmarks","views"]

            # Ensure all expected columns exist
            for c in expected_cols:
                if c not in df_new.columns:
                    df_new[c] = ""

            # Append and deduplicate with previous CSV if it exists
            if OUTPUT_CSV.exists():
                try:
                    df_existing = pd.read_csv(OUTPUT_CSV, dtype=str)
                    combined = pd.concat([df_existing, df_new], ignore_index=True)
                    combined.drop_duplicates(subset=["tweet_id"], inplace=True)
                except Exception as ex:
                    print("Warning combining CSVs:", ex)
                    combined = df_new
            else:
                combined = df_new

            combined.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
            print(f"Appended {len(df_new)} new tweets. CSV now has {len(combined)} rows.")
        else:
            print("No new tweets found this run.")

    except KeyboardInterrupt:
        # Allows you to safely exit with Ctrl+C
        print("\n⏹️  Interrupted by user. Exiting cleanly...")

    finally:
        # Always close the browser even if interrupted or on error
        try:
            driver.quit()
            print("Browser closed successfully.")
        except:
            pass

if __name__ == "__main__":
    main()
