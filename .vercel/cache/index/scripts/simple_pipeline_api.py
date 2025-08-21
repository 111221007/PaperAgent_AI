#!/usr/bin/env python3
"""
Research Paper Pipeline API - Original Working Version
Simple and reliable paper fetching and processing
"""

from flask import Flask, request, jsonify, send_from_directory, send_file, Response, stream_with_context, make_response
from flask_cors import CORS
import os
import re
import urllib.parse
import xml.etree.ElementTree as ET
import json
import requests
import time
import queue

app = Flask(__name__)
CORS(app)

# Global log queue for streaming logs to clients
log_queue = queue.Queue()

# Helper function to log to both terminal and queue
def stream_log(msg):
    print(msg)  # Print to console for debug visibility
    try:
        log_queue.put(msg)
    except Exception:
        pass

@app.route('/api/logs')
def stream_logs():
    def event_stream():
        while True:
            msg = log_queue.get()
            yield f"data: {msg}\n\n"
    return Response(stream_with_context(event_stream()), content_type='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    })

def get_session():
    """Create a session with proper headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    return session

def calculate_similarity(title1, title2):
    """Calculate similarity between titles"""
    if not title1 or not title2:
        return 0.0

    # Simple word-based similarity
    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    return intersection / union if union > 0 else 0.0

def search_semantic_scholar(title):
    """Search Semantic Scholar for abstract"""
    try:
        session = get_session()
        clean_title = re.sub(r'[^\w\s]', ' ', title).strip()

        url = f"https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            'query': clean_title,
            'fields': 'title,abstract',
            'limit': 5
        }

        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            papers = data.get('data', [])

            for paper in papers:
                if paper.get('abstract'):
                    similarity = calculate_similarity(title, paper.get('title', ''))
                    if similarity > 0.6:
                        return {
                            'found': True,
                            'abstract': paper['abstract'],
                            'source': 'Semantic Scholar'
                        }

        time.sleep(1)  # Rate limiting

    except Exception as e:
        print(f"Semantic Scholar error: {e}")

    return {'found': False, 'abstract': '', 'source': 'Semantic Scholar'}

def search_arxiv(title):
    """Search arXiv for abstract"""
    try:
        session = get_session()
        clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
        search_query = urllib.parse.quote(clean_title)

        url = f"http://export.arxiv.org/api/query?search_query=ti:{search_query}&max_results=5"

        response = session.get(url, timeout=30)
        if response.status_code == 200:
            root = ET.fromstring(response.content)

            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                entry_title = entry.find('{http://www.w3.org/2005/Atom}title')
                summary = entry.find('{http://www.w3.org/2005/Atom}summary')

                if entry_title is not None and summary is not None:
                    similarity = calculate_similarity(title, entry_title.text.strip())
                    if similarity > 0.6:
                        return {
                            'found': True,
                            'abstract': summary.text.strip(),
                            'source': 'arXiv'
                        }

        time.sleep(1)  # Rate limiting

    except Exception as e:
        print(f"arXiv error: {e}")

    return {'found': False, 'abstract': '', 'source': 'arXiv'}

def search_ieee_xplore(title):
    """Search IEEE Xplore for abstract"""
    try:
        session = get_session()
        clean_title = re.sub(r'[\^\w\s]', ' ', title).strip()
        search_query = urllib.parse.quote(clean_title)

        url = "https://ieeexploreapi.ieee.org/api/v2/search/articles"
        params = {
            'queryText': search_query,
            'apiKey': 'uzwc9gumppvk6fxf8gu7mrpg',
            'fields': 'title,abstract',
            'maxResults': 5
        }

        for attempt in range(3):  # Retry logic
            response = session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                papers = data.get('articles', [])

                for paper in papers:
                    if paper.get('abstract'):
                        similarity = calculate_similarity(title, paper.get('title', ''))
                        if similarity > 0.6:
                            return {
                                'found': True,
                                'abstract': paper.get('abstract'),
                                'source': 'IEEE Xplore'
                            }
            elif response.status_code == 596:
                print(f"[ERROR] IEEE Xplore API returned 596: {response.text}")
            else:
                print(f"[ERROR] Unexpected status {response.status_code}: {response.text}")

            time.sleep(2 ** attempt)  # Exponential backoff

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error while accessing IEEE Xplore: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in search_ieee_xplore: {e}")

    return {'found': False, 'abstract': '', 'source': 'IEEE Xplore'}

def search_acm_digital_library(title):
    """Search ACM Digital Library for abstract"""
    try:
        session = get_session()
        clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
        search_query = urllib.parse.quote(clean_title)

        url = f"https://dl.acm.org/api/volumes/press/chapters"
        params = {
            'query': search_query,
            'apiKey': 'your_acm_api_key',
            'fields': 'title,abstract',
            'limit': 5
        }

        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            papers = data.get('data', [])

            for paper in papers:
                if paper.get('abstract'):
                    similarity = calculate_similarity(title, paper.get('title', ''))
                    if similarity > 0.6:
                        return {
                            'found': True,
                            'abstract': paper['abstract'],
                            'source': 'ACM Digital Library'
                        }

        time.sleep(1)  # Rate limiting

    except Exception as e:
        print(f"ACM Digital Library error: {e}")

    return {'found': False, 'abstract': '', 'source': 'ACM Digital Library'}

def search_springerlink(title):
    """Search SpringerLink for abstract"""
    try:
        session = get_session()
        clean_title = re.sub(r'[^\w\s]', ' ', title).strip()
        search_query = urllib.parse.quote(clean_title)

        url = f"https://api.springernature.com/metadata/json"
        params = {
            'q': search_query,
            'apiKey': 'your_springer_api_key',
            'fields': 'title,abstract',
            'limit': 5
        }

        response = session.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            papers = data.get('records', [])

            for paper in papers:
                if paper.get('abstract'):
                    similarity = calculate_similarity(title, paper.get('title', ''))
                    if similarity > 0.6:
                        return {
                            'found': True,
                            'abstract': paper['abstract'],
                            'source': 'SpringerLink'
                        }

        time.sleep(1)  # Rate limiting

    except Exception as e:
        print(f"SpringerLink error: {e}")

    return {'found': False, 'abstract': '', 'source': 'SpringerLink'}

def categorize_paper(title, abstract):
    """Simple categorization based on keywords"""
    text = f"{title} {abstract}".lower()

    categories = {
        'survey': ['survey', 'review', 'taxonomy'],
        'latency': ['latency', 'response time', 'cold start'],
        'security': ['security', 'privacy', 'authentication'],
        'cost': ['cost', 'pricing', 'billing'],
        'performance': ['performance', 'optimization', 'efficiency'],
        'serverless': ['serverless', 'lambda', 'function'],
        'others': []
    }

    found_categories = []
    found_keywords = []

    for category, keywords in categories.items():
        if category == 'others':
            continue
        for keyword in keywords:
            if keyword in text:
                if category not in found_categories:
                    found_categories.append(category)
                if keyword not in found_keywords:
                    found_keywords.append(keyword)

    if not found_categories:
        found_categories = ['others']

    return ', '.join(found_categories), ', '.join(found_keywords[:5])

@app.route('/')
def index():
    stream_log("[DEBUG] Root endpoint '/' accessed (frontend loaded)")
    response = make_response(send_from_directory('.', 'index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/fetch', methods=['POST'])
def fetch_papers():
    stream_log("[DEBUG] /api/fetch endpoint called")
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        additional_keyword = data.get('additional_keyword', '').strip()
        from_year = int(data.get('from_year', 2020))
        to_year = int(data.get('to_year', 2025))
        total_results = min(int(data.get('total_results', 20)), 100)
        title_filter = data.get('title_filter', True)
        paper_type_filter = data.get('paper_type_filter', True)

        stream_log(f"[DEBUG] Fetching papers: {keyword} + {additional_keyword}, {from_year}-{to_year}, {total_results} results")

        papers = []
        session = get_session()

        rows_per_request = 20
        offset = 0
        fetched_count = 0
        max_attempts = total_results * 3
        processed_count = 0

        keyword_lower = keyword.lower().strip()
        additional_keyword_lower = additional_keyword.lower().strip()

        while fetched_count < total_results and processed_count < max_attempts:
            try:
                remaining = total_results - fetched_count
                current_rows = min(rows_per_request, remaining * 2)

                if additional_keyword.strip():
                    url = f'https://api.crossref.org/works?query.title={urllib.parse.quote(keyword)}+{urllib.parse.quote(additional_keyword)}'
                else:
                    url = f'https://api.crossref.org/works?query.title={urllib.parse.quote(keyword)}'

                url += f'&filter=from-pub-date:{from_year},until-pub-date:{to_year}'
                if paper_type_filter:
                    url += ',type:journal-article,type:proceedings-article'
                url += f'&rows={current_rows}&offset={offset}&sort=relevance'

                stream_log(f"[DEBUG] Fetching batch: offset={offset}, rows={current_rows}")
                response = session.get(url, timeout=30)
                if not response.ok:
                    stream_log(f"[ERROR] CrossRef API returned status {response.status_code}")
                    break

                data_response = response.json()
                items = data_response.get('message', {}).get('items', [])

                stream_log(f"[DEBUG] Items fetched in this batch: {len(items)}")
                if not items:
                    stream_log("[DEBUG] No more items returned from CrossRef API.")
                    break

                for item in items:
                    processed_count += 1
                    if fetched_count >= total_results:
                        break

                    title = ''
                    if item.get('title') and len(item['title']) > 0:
                        title = item['title'][0] if isinstance(item['title'], list) else item['title']

                    if title_filter and title:
                        title_lower = title.lower()
                        keyword_in_title = keyword_lower in title_lower
                        additional_in_title = not additional_keyword_lower or additional_keyword_lower in title_lower

                        if not (keyword_in_title and additional_in_title):
                            continue

                    paper = extract_paper_info(item, fetched_count + 1)
                    papers.append(paper)
                    fetched_count += 1

                offset += current_rows
                time.sleep(0.2)

            except Exception as e:
                stream_log(f"[ERROR] Error fetching batch: {e}")
                break

        stream_log(f"[DEBUG] Total papers fetched: {len(papers)}")
        return jsonify({
            'success': True,
            'papers': papers,
            'total': len(papers),
            'message': f'Successfully fetched {len(papers)} papers'
        })

    except Exception as e:
        stream_log(f"[ERROR] Error in fetch_papers: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to fetch papers'
        }), 500

def extract_paper_info(item, paper_id):
    """Extract paper information from CrossRef item"""
    authors = []
    if item.get('author'):
        for author in item['author']:
            if author.get('given') and author.get('family'):
                authors.append(f"{author['given']} {author['family']}")
            elif author.get('family'):
                authors.append(author['family'])

    title = ''
    if item.get('title') and len(item['title']) > 0:
        title = item['title'][0] if isinstance(item['title'], list) else item['title']

    abstract = ''
    if item.get('abstract'):
        abstract = re.sub(r'<[^>]+>', '', item['abstract']).replace('\n', ' ').strip()

    journal = ''
    if item.get('container-title') and len(item['container-title']) > 0:
        journal = item['container-title'][0] if isinstance(item['container-title'], list) else item['container-title']

    year = ''
    if item.get('published-print', {}).get('date-parts'):
        year = str(item['published-print']['date-parts'][0][0])
    elif item.get('published-online', {}).get('date-parts'):
        year = str(item['published-online']['date-parts'][0][0])

    return {
        'paper_id': f"paper_{str(paper_id).zfill(3)}",
        'title': title,
        'abstract': abstract,
        'authors': '; '.join(authors) if authors else 'Not Available',
        'journal': journal,
        'year': year,
        'volume': item.get('volume', ''),
        'issue': item.get('issue', ''),
        'pages': item.get('page', ''),
        'publisher': item.get('publisher', ''),
        'doi': item.get('DOI', ''),
        'url': item.get('URL', ''),
        'type': item.get('type', '')
    }

@app.route('/api/deduplicate', methods=['POST'])
def deduplicate_papers():
    try:
        data = request.get_json()
        papers = data.get('papers', [])

        if not papers:
            return jsonify({'error': 'No papers provided'}), 400

        unique_papers = []
        seen_dois = set()
        seen_titles = set()
        removed_count = 0

        for paper in papers:
            is_duplicate = False
            doi = paper.get('doi', '').strip()
            if doi and doi in seen_dois:
                is_duplicate = True
            title = paper.get('title', '').strip().lower()
            if title and title in seen_titles:
                is_duplicate = True
            if not is_duplicate:
                unique_papers.append(paper)
                if doi:
                    seen_dois.add(doi)
                if title:
                    seen_titles.add(title)
            else:
                removed_count += 1

        # Assign unique paper IDs after deduplication
        for idx, paper in enumerate(unique_papers):
            paper['paper_id'] = f"paper{str(idx+1).zfill(3)}"

        stream_log(f"[DEBUG] Deduplication complete: {removed_count} duplicates removed, {len(unique_papers)} unique papers remaining")

        return jsonify({
            'success': True,
            'papers': unique_papers,
            'removed': removed_count,
            'removed_count': removed_count,
            'remaining': len(unique_papers),
            'deduplicated_count': len(unique_papers),
            'original_count': len(papers),
            'message': f'{removed_count} duplicates removed, {len(unique_papers)} unique papers remaining'
        })

    except Exception as e:
        stream_log(f"[ERROR] Deduplication error: {e}")
        return jsonify({'error': str(e)}), 500

def fetch_abstract_multi_source(title):
    """Fetch abstract from multiple sources."""
    sources = [
        search_semantic_scholar,
        search_arxiv,
        search_ieee_xplore,
        search_acm_digital_library,
        search_springerlink
    ]

    for source in sources:
        try:
            result = source(title)
            if result.get('found') and result.get('abstract'):
                return result
        except Exception as e:
            stream_log(f"[ERROR] Error fetching from {source.__name__}: {e}")

    return {'found': False, 'abstract': '', 'source': 'none'}

@app.route('/api/extract-abstracts', methods=['POST'])
def extract_abstracts():
    """Extract abstracts from multiple sources"""
    try:
        data = request.get_json()
        papers = data.get('papers', [])

        if not papers:
            return jsonify({'error': 'No papers provided'}), 400

        found_abstracts = 0

        for i, paper in enumerate(papers):
            stream_log(f"[DEBUG] Processing paper {i+1}/{len(papers)}: {paper.get('title', 'No title')[:50]}...")

            title = paper.get('title', '').strip()
            if title:
                try:
                    result = fetch_abstract_multi_source(title)
                    if result.get('found') and result.get('abstract'):
                        paper['abstract'] = result['abstract']
                        paper['abstract_source'] = result['source']
                        paper['abstract_confidence'] = 'high'
                        found_abstracts += 1
                        stream_log(f"[DEBUG] Found abstract via {result['source']} for paper {i+1}")
                except Exception as e:
                    stream_log(f"[ERROR] Abstract fetch error for paper {i+1}: {e}")

            # Set default values if no abstract found
            if 'abstract' not in paper:
                paper['abstract'] = ''
                paper['abstract_source'] = 'none'
                paper['abstract_confidence'] = 'none'

        stream_log(f"[DEBUG] Abstract extraction complete: {found_abstracts}/{len(papers)} papers now have abstracts")

        return jsonify({
            'papers': papers,
            'found': found_abstracts,
            'total': len(papers)
        })

    except Exception as e:
        stream_log(f"[ERROR] Error in extract_abstracts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-complete', methods=['POST'])
def process_complete():
    """Process papers: deduplicate, extract abstracts, categorize"""
    try:
        data = request.json
        papers = data.get('papers', [])

        if not papers:
            return jsonify({'success': False, 'error': 'No papers provided'}), 400

        print(f"Processing {len(papers)} papers...")

        # Simple deduplication based on title similarity
        unique_papers = []
        seen_titles = []

        for paper in papers:
            title = paper.get('title', '').strip()
            is_duplicate = False

            for seen_title in seen_titles:
                if calculate_similarity(title, seen_title) > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen_titles.append(title)
                unique_papers.append(paper)

        # Process each unique paper
        processed_papers = []

        for i, paper in enumerate(unique_papers):
            print(f"Processing paper {i+1}/{len(unique_papers)}: {paper.get('title', '')[:50]}...")

            # Extract abstract if not available
            if not paper.get('abstract') or len(paper['abstract'].strip()) < 50:
                result = fetch_abstract_multi_source(paper.get('title', ''))
                if result['found']:
                    paper['abstract'] = result['abstract']
                    paper['abstract_source'] = result['source']
                    paper['abstract_confidence'] = 'high'
                else:
                    paper['abstract_source'] = 'Not found'
                    paper['abstract_confidence'] = 'low'
            else:
                paper['abstract_source'] = 'Original'
                paper['abstract_confidence'] = 'high'

            # Categorize paper
            categories, keywords = categorize_paper(paper.get('title', ''), paper.get('abstract', ''))
            paper['original_category'] = categories
            paper['original_keywords'] = keywords

            # Generate contributions and limitations based on abstract
            abstract = paper.get('abstract', '')
            if len(abstract) > 50:
                # Simple keyword-based extraction for contributions
                if any(word in abstract.lower() for word in ['propose', 'present', 'introduce', 'develop', 'design']):
                    paper['contributions'] = "Novel approach and methodology presented"
                else:
                    paper['contributions'] = "Various contributions mentioned in the paper"

                # Simple keyword-based extraction for limitations
                if any(word in abstract.lower() for word in ['limitation', 'challenge', 'future work', 'improve']):
                    paper['limitations'] = "Limitations and future work discussed"
                else:
                    paper['limitations'] = "Not explicitly mentioned"
            else:
                paper['contributions'] = "Not available"
                paper['limitations'] = "Not available"

            processed_papers.append(paper)

        return jsonify({
            'success': True,
            'papers': processed_papers,
            'original_count': len(papers),
            'deduplicated_count': len(unique_papers),
            'processed_count': len(processed_papers),
            'message': f'Successfully processed {len(processed_papers)} papers'
        })

    except Exception as e:
        stream_log(f"Processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process-stream', methods=['POST'])
def process_stream():
    """Stream processing progress in real-time"""
    try:
        data = request.json
        papers = data.get('papers', [])

        if not papers:
            return jsonify({'success': False, 'error': 'No papers provided'}), 400

        def generate():
            yield f"data: {json.dumps({'type': 'start', 'message': f'Processing {len(papers)} papers...'})}\n\n"

            # Simple deduplication based on title similarity
            unique_papers = []
            seen_titles = []

            for paper in papers:
                title = paper.get('title', '').strip()
                is_duplicate = False

                for seen_title in seen_titles:
                    if calculate_similarity(title, seen_title) > 0.8:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    seen_titles.append(title)
                    unique_papers.append(paper)

            yield f"data: {json.dumps({'type': 'dedup', 'message': f'Deduplicated: {len(unique_papers)} unique papers from {len(papers)} total'})}\n\n"

            # Process each unique paper
            processed_papers = []

            for i, paper in enumerate(unique_papers):
                title = paper.get('title', '')
                short_title = title[:70] + '...' if len(title) > 70 else title

                yield f"data: {json.dumps({'type': 'processing', 'message': f'Processing paper {i+1}/{len(unique_papers)}: {short_title}'})}\n\n"

                # Extract abstract if not available
                if not paper.get('abstract') or len(paper['abstract'].strip()) < 50:
                    yield f"data: {json.dumps({'type': 'abstract', 'message': f'Searching for abstract for paper {i+1}...'})}\n\n"

                    result = fetch_abstract_multi_source(paper.get('title', ''))
                    if result['found']:
                        paper['abstract'] = result['abstract']
                        paper['abstract_source'] = result['source']
                        paper['abstract_confidence'] = 'high'
                        message = f'Abstract found via {result["source"]} for paper {i+1}'
                        yield f"data: {json.dumps({'type': 'abstract', 'message': message})}\n\n"
                    else:
                        paper['abstract_source'] = 'Not found'
                        paper['abstract_confidence'] = 'low'
                        yield f"data: {json.dumps({'type': 'abstract', 'message': f'No abstract found for paper {i+1}'})}\n\n"
                else:
                    paper['abstract_source'] = 'Original'
                    paper['abstract_confidence'] = 'high'

                # Categorize paper
                categories, keywords = categorize_paper(paper.get('title', ''), paper.get('abstract', ''))
                paper['original_category'] = categories
                paper['original_keywords'] = keywords

                # Generate contributions and limitations based on abstract
                abstract = paper.get('abstract', '')
                if len(abstract) > 50:
                    if any(word in abstract.lower() for word in ['propose', 'present', 'introduce', 'develop', 'design']):
                        paper['contributions'] = "Novel approach and methodology presented"
                    else:
                        paper['contributions'] = "Various contributions mentioned in the paper"

                    if any(word in abstract.lower() for word in ['limitation', 'challenge', 'future work', 'improve']):
                        paper['limitations'] = "Limitations and future work discussed"
                    else:
                        paper['limitations'] = "Not explicitly mentioned"
                else:
                    paper['contributions'] = "Not available"
                    paper['limitations'] = "Not available"

                processed_papers.append(paper)

                yield f"data: {json.dumps({'type': 'complete', 'message': f'Completed paper {i+1}/{len(unique_papers)}'})}\n\n"

            yield f"data: {json.dumps({'type': 'finished', 'papers': processed_papers, 'total': len(processed_papers)})}\n\n"

        return Response(generate(), content_type='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        })

    except Exception as e:
        stream_log(f"Processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# --- Multi-source abstract fetcher ---
def fetch_abstract_multi_source(title):
    """
    Try to fetch abstract from multiple sources in order of reliability.
    Returns: dict with keys: found (bool), abstract (str), source (str)
    """
    # 1. Semantic Scholar
    result = search_semantic_scholar(title)
    if result.get('found') and result.get('abstract'):
        return result
    # 2. arXiv
    result = search_arxiv(title)
    if result.get('found') and result.get('abstract'):
        return result
    # 3. IEEE Xplore
    result = search_ieee_xplore(title)
    if result.get('found') and result.get('abstract'):
        return result
    # 4. ACM Digital Library
    result = search_acm_digital_library(title)
    if result.get('found') and result.get('abstract'):
        return result
    # 5. SpringerLink
    result = search_springerlink(title)
    if result.get('found') and result.get('abstract'):
        return result
    # 6. DBLP (title search, no abstract, but can try)
    # 7. CORE (API)
    try:
        import requests
        core_url = f'https://core.ac.uk:443/api-v2/search/{urllib.parse.quote(title)}?apiKey=demo'
        r = requests.get(core_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('data'):
                for item in data['data']:
                    if item.get('abstract'):
                        return {'found': True, 'abstract': item['abstract'], 'source': 'CORE'}
    except Exception:
        pass
    # 8. HAL (API)
    try:
        hal_url = f'https://api.archives-ouvertes.fr/search/?q=title_t:({urllib.parse.quote(title)})&wt=json&fl=title_s,abstract_s'
        r = requests.get(hal_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            docs = data.get('response', {}).get('docs', [])
            for doc in docs:
                if doc.get('abstract_s'):
                    return {'found': True, 'abstract': doc['abstract_s'], 'source': 'HAL'}
    except Exception:
        pass
    # 9. OpenAIRE (API)
    try:
        openaire_url = f'https://api.openaire.eu/search/publications?title={urllib.parse.quote(title)}&format=json'
        r = requests.get(openaire_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            hits = data.get('response', {}).get('results', [])
            for hit in hits:
                if hit.get('metadata', {}).get('oaf:result', {}).get('title') and hit.get('metadata', {}).get('oaf:result', {}).get('description'):
                    return {'found': True, 'abstract': hit['metadata']['oaf:result']['description'], 'source': 'OpenAIRE'}
    except Exception:
        pass
    # 10. CiteSeerX (API)
    try:
        csx_url = f'https://citeseerx.ist.psu.edu/search?q={urllib.parse.quote(title)}&submit=Search&sort=rlv&t=doc'
        r = requests.get(csx_url, timeout=10)
        if r.status_code == 200 and 'Abstract' in r.text:
            import re
            m = re.search(r'<div class="abstract">(.*?)</div>', r.text, re.DOTALL)
            if m:
                abs_text = m.group(1).strip()
                return {'found': True, 'abstract': abs_text, 'source': 'CiteSeerX'}
    except Exception:
        pass
    # 11. Google Scholar, IEEE, ACM, Springer, Elsevier, Wiley, ResearchGate, Academia.edu, TechRxiv
    # These require scraping or paid API, not implemented here for legal/ToS reasons.
    return {'found': False, 'abstract': '', 'source': 'none'}

if __name__ == '__main__':
    print("\n==============================")
    print("🚀 Starting Research Paper Pipeline Server on port 8000")
    print("==============================\n")
    app.run(host='0.0.0.0', port=8000, debug=True)

# For Vercel deployment
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
if __name__ == "__main__": print("🚀 Starting Research Paper Pipeline Server on port 8002"); app.run(host="0.0.0.0", port=8002, debug=True)
