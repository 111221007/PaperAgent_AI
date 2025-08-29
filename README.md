# PaperAgent: Free Research Paper Fetcher & Organizer

## Overview
PaperAgent is a **100% free, open-source tool** designed to help researchers, master's students, PhD students, and academics quickly find, deduplicate, and organize research papers from trusted sources. It provides a simple web interface and a powerful backend API to automate literature search, making the research process faster and more efficient.

---

## Features
- **Fetch research papers** from CrossRef and other sources using keywords, date range, and filters
- **Support for primary and two additional keywords** to refine your search
- **Deduplicate** results to remove similar or duplicate papers
- **Automatic abstract extraction** from multiple sources
- **Real-time log streaming** to the UI for transparency
- **Export results** for further analysis
- **Easy to use** web interface
- **Completely free and open-source**

---

## Who is this for?
- **Master's students**: Quickly gather related work for your thesis or coursework
- **PhD students**: Automate literature reviews, stay up-to-date with the latest research, and organize findings
- **Researchers & Academics**: Save time on manual paper search, deduplication, and abstract extraction
- **Anyone** who needs to find, filter, and organize academic papers efficiently

---

## How does it make research easier?
- **Saves hours** of manual searching and filtering
- **Reduces duplicate work** by deduplicating similar papers
- **Finds abstracts** even when not available in the main database
- **Customizable search** with multiple keywords and filters
- **Transparent logs** so you can see exactly what the tool is doing
- **No paywalls, no registration, no limits**

---

## Quick Start (Local)

### 1. Clone the repository
```bash
git clone https://github.com/111221007/PaperAgent_AI.git
cd PaperAgent_AI
```

### 2. Install dependencies
Make sure you have Python 3.8+ and pip installed.
```bash
pip install -r requirements.txt
```

### 3. Run the backend server
```bash
python3 scripts/simple_pipeline_api.py
```

The server will start on `http://localhost:5000` (or the port specified in the `PORT` environment variable).

### 4. Open the UI
Open `scripts/index.html` in your browser, or set up a simple static file server to serve it.

---

## Deployment (Render.com, HuggingFace Spaces, etc.)
- Make sure your `requirements.txt` and `Procfile` are present and correct.
- The backend will automatically bind to the port specified by the `PORT` environment variable (required by most cloud platforms).
- Deploy using your preferred platform's instructions.

---

## How it works
- The backend uses Flask and Flask-SocketIO to provide a REST API and real-time log streaming.
- The `/api/fetch` endpoint queries CrossRef and other sources for papers matching your keywords and filters.
- Deduplication and abstract extraction are performed automatically.
- The UI allows you to enter keywords, date range, and see results and logs in real time.

---

## Example Use Cases
- **Literature review**: Enter your main topic and related keywords, fetch and deduplicate papers, and export the results for your review.
- **Survey paper preparation**: Gather a comprehensive set of papers on a topic, including abstracts, to prepare a survey or meta-analysis.
- **Staying up-to-date**: Regularly search for new papers in your field with just a few clicks.

---

## Contributing
Contributions are welcome! Please open issues or pull requests for bug fixes, new features, or improvements.

---

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact
For questions, suggestions, or support, please open an issue on GitHub.

---

**PaperAgent is 100% free and always will be. Empower your research today!**

