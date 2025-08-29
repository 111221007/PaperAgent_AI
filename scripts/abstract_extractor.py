import os
import sys
import time
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup

def get_input_file():
    input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    if not os.path.exists(input_dir):
        print(f"Input directory not found: {input_dir}")
        sys.exit(1)
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.csv', '.xlsx'))]
    if not files:
        path = input("No input files found in 'input'. Enter the path to the CSV or XLSX file: ").strip()
        if not os.path.exists(path):
            print("File not found.")
            sys.exit(1)
        return path
    if len(files) == 1:
        print(f"Found input file: {files[0]}")
        return os.path.join(input_dir, files[0])
    print("Multiple input files found:")
    for idx, f in enumerate(files):
        print(f"{idx+1}: {f}")
    while True:
        try:
            choice = int(input("Enter the number corresponding to the file you want to process: "))
            if 1 <= choice <= len(files):
                return os.path.join(input_dir, files[choice-1])
        except Exception:
            pass
        print("Invalid selection. Try again.")

def load_file(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.csv':
            try:
                df = pd.read_csv(path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding='ISO-8859-1')
        elif ext == '.xlsx':
            df = pd.read_excel(path, engine='openpyxl')
        else:
            print("Unsupported file type.")
            sys.exit(1)
        return df
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def save_file(df, original_path):
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)
    ext = os.path.splitext(original_path)[1].lower()
    timestamp = int(datetime.now().timestamp())
    base = os.path.splitext(os.path.basename(original_path))[0]
    out_path = os.path.join(output_dir, f"{base}_with_abstracts_{timestamp}{ext}")
    if ext == '.csv':
        df.to_csv(out_path, index=False)
    else:
        df.to_excel(out_path, index=False)
    print(f"File with abstracts saved to: {out_path}")

def fetch_abstract_openalex(title):
    try:
        url = f"https://api.openalex.org/works?filter=title.search:{quote(title)}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('results'):
                return data['results'][0].get('abstract_inverted_index')
    except Exception:
        pass
    return None

def fetch_abstract_crossref(title):
    try:
        url = f"https://api.crossref.org/works?query.title={quote(title)}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            items = data.get('message', {}).get('items', [])
            if items:
                return items[0].get('abstract')
    except Exception:
        pass
    return None

def fetch_abstract_semanticscholar(title):
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={quote(title)}&fields=title,abstract"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                return data['data'][0].get('abstract')
    except Exception:
        pass
    return None

def fetch_abstract_arxiv(title):
    try:
        url = f"http://export.arxiv.org/api/query?search_query=ti:{quote(title)}&max_results=1"
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and '<entry>' in r.text:
            soup = BeautifulSoup(r.text, 'xml')
            entry = soup.find('entry')
            if entry and entry.find('summary'):
                return entry.find('summary').text.strip()
    except Exception:
        pass
    return None

def fetch_abstract_web_scrape(title):
    # Google Scholar scraping is not recommended due to bot detection, but we try a simple search
    try:
        search_url = f"https://scholar.google.com/scholar?q={quote(title)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(search_url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for div in soup.find_all('div', class_='gs_ri'):
                if div.find('h3') and title.lower() in div.find('h3').text.lower():
                    snippet = div.find('div', class_='gs_rs')
                    if snippet:
                        return snippet.text.strip()
    except Exception:
        pass
    return None

def fetch_abstracts_for_titles(df):
    if 'abstract' not in df.columns:
        df['abstract'] = ''
    for idx, row in df.iterrows():
        if pd.notnull(row.get('abstract')) and str(row['abstract']).strip():
            continue  # Skip if already present
        title = str(row['title'])
        abstract = None
        # Try all methods in order
        for fetch_func in [fetch_abstract_openalex, fetch_abstract_crossref, fetch_abstract_semanticscholar, fetch_abstract_arxiv, fetch_abstract_web_scrape]:
            abstract = fetch_func(title)
            if abstract:
                break
            time.sleep(1)  # Be polite to APIs
        if abstract:
            df.at[idx, 'abstract'] = abstract if isinstance(abstract, str) else ' '.join(abstract.keys())
        else:
            df.at[idx, 'abstract'] = ''
        print(f"Processed [{idx+1}/{len(df)}]: {title[:60]}... {'FOUND' if abstract else 'NOT FOUND'}")
    return df

def main():
    path = get_input_file()
    df = load_file(path)
    if 'title' not in df.columns:
        print("No 'title' column found in the file.")
        sys.exit(1)
    df = fetch_abstracts_for_titles(df)
    save_file(df, path)

if __name__ == "__main__":
    main()

