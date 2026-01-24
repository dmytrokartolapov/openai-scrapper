# openai-scrapper

**OpenAI Scrapper** is an advanced web scraping solution powered by AI and vector database technologies. It automates extraction, summarization, and storage of web content, using LangChain for LLM-driven summarization and Qdrant for efficient vector search and storage.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment & Install Dependencies](#2-create-a-virtual-environment--install-dependencies)
  - [3. Configure Python Interpreter in PyCharm (with .venv)](#3-configure-python-interpreter-in-pycharm-with-venv)
  - [4. Set Up and Run Qdrant Database](#4-set-up-and-run-qdrant-database)
  - [5. Get an OpenAI API Key & Set as Environment Variable](#5-get-an-openai-api-key--set-as-environment-variable)
- [Running the Scrapper](#running-the-scrapper)
- [Key Features](#key-features)
- [Use Cases](#use-cases)
- [Workflow Overview](#workflow-overview)
- [Benefits](#benefits)

---

## Requirements

- Python 3.12.10
- FastAPI
- Uvicorn
- LangChain
- OpenAI Python SDK
- Qdrant

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd openai-scrapper
```

---

### 2. Create a Virtual Environment & Install Dependencies

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 3. Configure Python Interpreter in PyCharm (with .venv)

1. Open your project in **PyCharm**.
2. Go to **File > Settings > Project: openai-scrapper > Python Interpreter**.
3. Click the gear ⚙️ next to the interpreter dropdown, then select **Add...**.
4. Choose **Existing environment**.
5. Click the `...` button, then browse and select the Python executable from your `.venv` directory:
    - On Windows, this is: `<project_root>\.venv\Scripts\python.exe`
    - On macOS/Linux: `<project_root>/.venv/bin/python`
6. Click **OK** to apply the interpreter.

Now all your project’s dependencies and scripts will run inside your isolated `.venv` environment.

---

### 4. Set Up and Run Qdrant Database

- Download the latest Qdrant for your OS from:  
  [Qdrant Releases](https://github.com/qdrant/qdrant/releases)
- Or grab the Windows version directly:  
  [qdrant-x86_64-pc-windows-msvc.zip](https://github.com/qdrant/qdrant/releases/download/v1.16.3/qdrant-x86_64-pc-windows-msvc.zip)
- Extract and copy `qdrant.exe` into your project folder.
- Launch Qdrant in your project terminal:

```bash
./qdrant.exe
```

> *(Qdrant runs in the background to provide vector storage)*

---

### 5. Get an OpenAI API Key & Set as Environment Variable

#### **A. Create an OpenAI API Key:**

1. Create an account at https://platform.openai.com/signup.
2. Add credits in [Billing](https://platform.openai.com/settings/organization/billing/overview) (minimum $5 recommended).
3. Go to your profile (top right) > **View API keys**.
4. Click **+ Create new secret key**, copy it—save it securely.

#### **B. Set the API Key for Your Project**

**Option 1: Set as Environment Variable in PyCharm (recommended):**

1. Go to **Run > Edit Configurations...**
2. Select your script (e.g., `launcher.py`) or create a new configuration.
3. In the configuration window, find **Environment variables**.
4. Click the `...` button.
5. Click `+`, and add:
    - **Name**: `OPENAI_API_KEY`
    - **Value**: *your-actual-api-key*
6. Click **OK** and save.

**Option 2: Set in Terminal (for manual runs):**

```bash
# Windows (cmd)
set OPENAI_API_KEY=your-actual-api-key

# Linux/macOS
export OPENAI_API_KEY=your-actual-api-key
```

---

## Running the Scrapper

Start the FastAPI app via the launcher script:

```bash
python launcher.py
```

Uvicorn is used under the hood for high-performance async web services.

---

## Key Features

- **Automated Web Scraping:**  
  Handles dynamic web content extraction with ease.

- **AI-Powered Summarization:**  
  LangChain processes raw content into concise summaries using LLMs.

- **Vector Database Storage:**  
  Store and retrieve embeddings for semantic search with Qdrant (or alternatives like FAISS, Chroma, Pinecone).

- **Modular & Extensible:**  
  Easily plug in new scraping targets, AI models, or database backends.

---

## Use Cases

- Automated knowledge base from web
- Competitive/market intelligence
- News aggregation and summarization
- Semantic search & recommendations

---

## Workflow Overview

1. **Input:** List of target URLs/domains.
2. **Scraping:** Extract raw web content.
3. **Summarization:** Turn content into concise summaries with LangChain.
4. **Embedding:** Summaries converted to vectors.
5. **Storage:** Store vectors and metadata in vector database.

---

## Benefits

- Dramatically **reduces manual effort** in data harvesting and summarization.
- Enables **semantic, AI-powered search** in your collected knowledge base.
- **Scalable** to large datasets and domains.
- Perfect for teams or individuals seeking to build **AI-driven searchable knowledge repositories**.

---

