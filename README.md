# PaperAgent

A research paper pipeline API and web interface, deployable on Vercel and Hugging Face Spaces.

## Features
- Upload, list, and delete files via REST API
- Flask backend (Python)
- Static frontend (public/index.html)

## Deployment
- Install Vercel CLI: `npm i -g vercel`
- Run locally: `vercel dev`
- Deploy: `vercel --prod`

## Deployment on Hugging Face Spaces

1. Ensure you have a Hugging Face account.
2. Push this repository to a Hugging Face repository.
3. Spaces will automatically detect the `app.py` file and deploy the application.
4. Visit the Space URL to interact with the application.

## API Endpoints
- `POST /api/upload` - Upload a file
- `GET /api/files` - List files
- `DELETE /api/files/<filename>` - Delete a file

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
.DS_Store

# Vercel
.vercel/

# IDE
.idea/
.vscode/

# PaperAgent
