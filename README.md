# Research Paper Pipeline API

This project provides a simple and reliable API for fetching and processing research papers. It includes features such as deduplication, abstract extraction, categorization, and CSV downloading.

## Features
- Fetch research papers from multiple sources.
- Deduplicate papers based on title similarity.
- Extract abstracts from various APIs.
- Categorize papers based on keywords.
- Download results as a CSV file.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/111221007/PaperAgent.git
   cd PaperAgent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application Locally
To run the application locally:
```bash
python3 scripts/simple_pipeline_api.py
```

The application will be available at `http://localhost:8000`.

## Deployment Instructions

### Deploying to Vercel
1. Ensure you have the Vercel CLI installed. If not, install it:
   ```bash
   npm install -g vercel
   ```
2. Deploy the project:
   ```bash
   vercel --prod
   ```
3. The deployed application will be accessible at the URL provided by Vercel.

### Access the Live Application
The application is live at: [https://paper-agent-mu.vercel.app/](https://paper-agent-mu.vercel.app/)

### Backup to GitHub
1. Initialize a Git repository (if not already initialized):
   ```bash
   git init
   ```
2. Add all files to the repository:
   ```bash
   git add .
   ```
3. Commit the changes:
   ```bash
   git commit -m "Add deployment instructions and prepare for backup"
   ```
4. Add the remote repository:
   ```bash
   git remote add origin https://github.com/111221007/PaperAgent.git
   ```
5. Push the changes to GitHub:
   ```bash
   git push -u origin main
   ```

## License
This project is licensed under the MIT License.
