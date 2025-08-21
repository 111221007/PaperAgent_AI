# Research Paper Pipeline API

This project provides a simple and reliable API for fetching and processing research papers. It includes features such as deduplication, abstract extraction, categorization, and PDF downloading.

## Features
- Fetch research papers from multiple sources.
- Deduplicate papers based on title similarity.
- Extract abstracts from various APIs.
- Categorize papers based on keywords.
- Download PDFs and generate a ZIP file.

## Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
To run the application locally:
```bash
python3 scripts/simple_pipeline_api.py
```

The application will be available at `http://localhost:7860`.

## Deployment
This project is ready to be deployed on Hugging Face Spaces. Ensure the `requirements.txt` file is included for dependency installation.

## License
This project is licensed under the MIT License.
