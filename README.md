

---
title: Web Knowledge Bot
emoji: 🤖
colorFrom: blue
colorTo: yellow
sdk: docker
pinned: false
---

# 🤖 Web Knowledge Bot

An AI-powered **Technical Documentation Assistant** built using **Retrieval-Augmented Generation (RAG)** to help developers quickly find accurate answers from technical documentation websites and uploaded PDF documents.

Instead of manually searching through lengthy API documentation, SDKs, or developer guides, users can ask questions in natural language and receive context-aware responses generated using **Google Gemini** and **ChromaDB**.

---

# 🚀 Project Overview

The Web Knowledge Bot combines two knowledge sources into a single AI assistant:

* 🌐 Technical Documentation Websites
* 📄 User Uploaded PDF Documents

The system retrieves the most relevant information using semantic search and generates grounded responses with source references.

---

# ✨ Key Features

* AI-powered technical documentation assistant
* Ask questions in natural language
* Upload PDF documents and chat with them
* Crawl and index technical documentation websites
* Retrieval-Augmented Generation (RAG)
* Semantic search using ChromaDB
* Google Gemini integration
* Source attribution for every response
* Modern React-based chat interface
* FastAPI backend with REST APIs
* Automatic fallback support for supported LLM providers

---

# 🏗️ Project Architecture

```
User
   │
   ▼
React Frontend
   │
   ▼
FastAPI Backend
   │
   ├───────────────┐
   │               │
   ▼               ▼
Website RAG     PDF RAG
   │               │
   └───────┬───────┘
           ▼
     ChromaDB Retriever
           ▼
      Google Gemini
           ▼
     AI Generated Response
```

---

# 📂 Repository Structure

```
web_knowledge_bot/

backend/
│
├── api/
├── pdf/
├── embeddings/
├── rag/
├── llm/
├── utils/
├── database/
├── uploads/
└── vector_db/

frontend/
│
├── src/
├── components/
├── pages/
└── assets/

bot/
│
└── CLI Assistant

README.md
Dockerfile
```

---

# 🛠️ Tech Stack

### Frontend

* React
* Vite
* Tailwind CSS

### Backend

* FastAPI
* Python

### AI & RAG

* Google Gemini
* LangChain
* ChromaDB
* PyPDF

### Utilities

* BeautifulSoup
* Requests
* python-dotenv

---

# ⚙️ Environment Variables

Create a `.env` file inside the **backend** directory.

```env
GOOGLE_API_KEY=YOUR_API_KEY
EMBEDDING_PROVIDER=huggingface
```

---

# ▶️ Running the Project

## 1. Clone Repository

```bash
git clone <repository-url>
cd web_knowledge_bot
```

---

## 2. Backend

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn app:app --reload
```

Backend will run at:

```
http://127.0.0.1:8000
```

API Documentation:

```
http://127.0.0.1:8000/docs
```

---

## 3. Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 🌐 Deployment

### Backend

Deploy the FastAPI backend using Docker on Hugging Face Spaces.

### Frontend

Deploy the React application on Vercel.

Set the following environment variable:

```
VITE_API_BASE_URL=https://YOUR_BACKEND_URL
```

---

# 📌 Future Enhancements

* Multi-document conversations
* Support for multiple documentation websites
* Hybrid search (BM25 + Vector Search)
* Authentication & user sessions
* Chat history synchronization
* Voice-based interactions
* Streaming AI responses
* Advanced source citation

---

# 👥 Team

**Team Hufflepuff** -- Pendyala Sindhuja

Developed as part of the **GenAI Internship at Augur CyberX**.

---

# 📄 License

This project is developed for educational and internship purposes.

