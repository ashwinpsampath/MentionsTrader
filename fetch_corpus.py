"""Smoke test: fetch the entire corpus and report what we got."""
from src.corpus import TRUMP_SPEECHES
from src.fetcher import fetch_html


def main():
    fetched = 0
    failed = []
    
    for url, date, event_type in TRUMP_SPEECHES:
        html = fetch_html(url)
        if html is None:
            failed.append(url)
            continue
        fetched += 1
    
    print()
    print(f"Successfully fetched: {fetched} / {len(TRUMP_SPEECHES)}")
    if failed:
        print(f"Failed URLs:")
        for url in failed:
            print(f"  {url}")


if __name__ == "__main__":
    main()