---
title: Web Knowledge Backend
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# RAG Web Knowledge Bot (Integrated Project)

A Retrieval-Augmented Generation (RAG) system containing a FastAPI backend, a React chat frontend widget, and a command-line interface (CLI) bot runner. The system classifies technical queries, retrieves documentation from trusted websites in real-time, stores them in ChromaDB, and generates grounded answers using Gemini (with automatic Groq fallback).

---

## 📁 Repository Structure

- **`backend/`**: FastAPI backend server implementing the core RAG pipeline (search, parallel crawling, HTML processing, indexing, vector storage, and query generation).
- **`frontend/`**: Vite + React chat widget web application (`frontend/frontend/`).
- **`bot/`**: A standalone Python command-line interface for RAG chat.
- **`main.py`**: Root-level orchestrator script to run services locally.
- **`Dockerfile`**: Root Docker configuration for deploying the backend to Hugging Face Spaces.
- **`.gitignore`**: Global rules to keep local caches, node modules, virtual environments, and `.env` credentials out of version control.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js & npm (for React frontend)

### 2. Environment Configuration
Create a `.env` file at the root of the **`backend/`** directory (and `bot/` directory if running the CLI bot) with the following variables:
```env
GOOGLE_API_KEY=your_gemini_or_groq_api_key_here
EMBEDDING_PROVIDER=huggingface
```
*Note: If `GOOGLE_API_KEY` starts with `gsk_`, the backend will automatically route chat completion requests to the Groq Llama-3 API fallback.*

### 3. Running Services Locally
Use the root `main.py` orchestrator script to run services from the root folder:

- **Start the FastAPI Backend**:
  ```bash
  python main.py backend
  ```
  *(Service runs on `http://127.0.0.1:8000`)*

- **Start the Bot CLI**:
  ```bash
  python main.py bot
  ```

- **Run Backend Unit Tests**:
  ```bash
  python main.py test
  ```

- **Start the React Frontend**:
  Navigate to the frontend project and launch the Vite development server:
  ```bash
  cd frontend/frontend
  npm install
  npm run dev
  ```

---

## 🚀 Cloud Deployment

### 1. Backend (Hugging Face Spaces)
1. Create a new Space on [Hugging Face](https://huggingface.co/).
2. Select **Docker** as the SDK and choose the **Blank** template.
3. In **Settings** under **Variables and secrets**, add a secret named `GOOGLE_API_KEY` with your API key.
4. Add the Space git repository as a remote and push code:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push -f hf main
   ```

### 2. Frontend (Vercel)
1. Create a new project on [Vercel](https://vercel.com/) and import your GitHub repository.
2. Set the **Root Directory** to `frontend/frontend`.
3. Add the following **Environment Variable**:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://YOUR_HF_USERNAME-YOUR_SPACE_NAME.hf.space` *(your Hugging Face direct API endpoint)*
4. Click **Deploy**.
