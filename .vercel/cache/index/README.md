# PaperAgent

A research paper pipeline API and web interface, deployable on Vercel.

## Features
- Upload, list, and delete files via REST API
- Flask backend (Python)
- Static frontend (public/index.html)

## Deployment
- Install Vercel CLI: `npm i -g vercel`
- Run locally: `vercel dev`
- Deploy: `vercel --prod`

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

