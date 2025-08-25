#!/usr/bin/env python3
"""
Research Paper Pipeline API - Original Working Version
Simple and reliable paper fetching and processing
"""

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
import re
import urllib.parse
import json
import requests
import time
import logging
import threading
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging to capture all messages
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Instantiate the advanced extractor

# Add a startup log message so the UI log is never empty
# Remove log_queue usage
logger.info('Research Paper Pipeline API server started.')

def periodic_log():
    import time
    while True:
        # Remove log_queue usage
        logger.debug(f"Periodic log at {time.strftime('%H:%M:%S')}")
        time.sleep(5)

threading.Thread(target=periodic_log, daemon=True).start()

# Helper function to log to both terminal and SocketIO
def stream_log(msg):
    logger.debug(msg)  # Log to console
    try:
        socketio.emit('log', msg)
    except Exception as e:
        logger.error(f"Failed to emit log: {e}")

@app.route('/api/fetch', methods=['POST'])
def fetch_papers():
    stream_log("[DEBUG] /api/fetch endpoint called")
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        additional_keyword = data.get('additional_keyword', '').strip()
        additional_keyword2 = data.get('additional_keyword2', '').strip()  # NEW FIELD
        from_year = int(data.get('from_year', 2020))
        to_year = int(data.get('to_year', 2025))
        total_results = min(int(data.get('total_results', 5)), 100)
        title_filter = data.get('title_filter', True)
        paper_type_filter = data.get('paper_type_filter', True)

        stream_log(f"[DEBUG] Fetching papers: {keyword} + {additional_keyword} + {additional_keyword2}, {from_year}-{to_year}, {total_results} results")

        papers = []
        session = get_session()

        rows_per_request = 20
        offset = 0
        fetched_count = 0
        max_attempts = total_results * 3
        processed_count = 0

        keyword_lower = keyword.lower().strip()
        additional_keyword_lower = additional_keyword.lower().strip()
        additional_keyword2_lower = additional_keyword2.lower().strip()  # NEW FIELD

        while fetched_count < total_results and processed_count < max_attempts:
            try:
                remaining = total_results - fetched_count
                current_rows = min(rows_per_request, remaining * 2)

                # Build Crossref API URL
                url = f'https://api.crossref.org/works?query.title={urllib.parse.quote(keyword)}'
                if additional_keyword:
                    url += f'+{urllib.parse.quote(additional_keyword)}'
                if additional_keyword2:
                    url += f'+{urllib.parse.quote(additional_keyword2)}'

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
                        additional2_in_title = not additional_keyword2_lower or additional_keyword2_lower in title_lower
                        if not (keyword_in_title and additional_in_title and additional2_in_title):
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
            if title:
                title_words = set(title.split())
                for seen_title in seen_titles:
                    seen_words = set(seen_title.split())
                    if len(title_words) > 0 and len(seen_words) > 0:
                        overlap = len(title_words.intersection(seen_words))
                        similarity = overlap / max(len(title_words), len(seen_words))
                        if similarity > 0.8:
                            is_duplicate = True
                            break
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

@app.before_request
def log_request_info():
    stream_log(f"[REQUEST] {request.method} {request.url}")

@app.after_request
def log_response_info(response):
    try:
        stream_log(f"[RESPONSE] {response.status_code} {response.get_data(as_text=True)}")
    except Exception as e:
        stream_log(f"[ERROR] Failed to log response: {e}")
    return response

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

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'index.html')

@app.route('/scripts/<path:filename>')
def serve_scripts(filename):
    return send_from_directory(os.path.abspath(os.path.join(os.getcwd(), 'scripts')), filename)

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

def get_session():
    import requests
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    return session

def search_semantic_scholar(title):
    return {'found': False, 'abstract': '', 'source': 'semantic_scholar'}

def search_arxiv(title):
    return {'found': False, 'abstract': '', 'source': 'arxiv'}

def search_ieee_xplore(title):
    return {'found': False, 'abstract': '', 'source': 'ieee_xplore'}

def search_acm_digital_library(title):
    return {'found': False, 'abstract': '', 'source': 'acm_digital_library'}

def search_springerlink(title):
    return {'found': False, 'abstract': '', 'source': 'springerlink'}

def calculate_similarity(title1, title2):
    # Simple similarity: ratio of common words
    set1 = set(title1.lower().split())
    set2 = set(title2.lower().split())
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / max(len(set1), len(set2))

def categorize_paper(title, abstract):
    # Dummy categorization
    return ['Uncategorized'], ['No keywords']

# Ensure the app runs on Hugging Face Spaces by binding to port 7860
if __name__ == '__main__':
    print('[DEBUG] Starting Flask app on port 7860')
    stream_log('[DEBUG] __main__ block executed, Flask app starting')
    threading.Thread(target=periodic_log, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
