# openai-scrapper

---
The OpenAI Scrapper is an advanced web scraping solution designed to automate the extraction, summarization, and storage of web content using state-of-the-art AI and vector database technologies. Leveraging the power of LangChain, this project enables seamless interaction with large language models to process and summarize scraped data efficiently.

## Requirements

- Python 3.12.7
- FastAPI
- Uvicorn

Installation

Clone the repository:

```bash
git clone <your-repo-url>
cd openai-scrapper
```

Running the Application
------------
Start the FastAPI server using Uvicorn:
```bash
uvicorn src.main:app --reload
```

Or Use Launcher:
------------
Uvicorn under hood:
```
python launcher.py
```

## Key Features:
### Automated Web Scraping:
The scrapper navigates and extracts content from specified websites, handling dynamic pages and complex site structures with ease.

### AI-Powered Summarization:
Using LangChain, the extracted content is processed through language models to generate concise, relevant summaries. This ensures that only the most important information is retained, reducing noise and improving data quality.

### Vector Database Storage:
Summarized data is embedded into high-dimensional vectors and stored in a vector database (such as Pinecone, FAISS, or Chroma). This enables efficient similarity search, semantic retrieval, and scalable data management.

### Modular and Extensible Architecture:
The project is built with modularity in mind, allowing easy integration of new scraping targets, summarization models, or vector database backends.

## Use Cases:
- Knowledge base creation from web sources
- Competitive intelligence and market research
- Automated news aggregation and summarization
- Semantic search and content recommendation systems

## Workflow Overview:
### Input: List of target URLs or domains.
- Scraping: The system crawls and extracts raw content from each site.
- Summarization: LangChain processes the content, generating concise summaries.
- Embedding: Summaries are converted into vector representations.
- Storage: Vectors and metadata are saved in the vector database for future retrieval.

### Benefits:
- Saves time by automating data collection and summarization.
- Enhances information retrieval with semantic search capabilities.
- Scalable and adaptable for various domains and data volumes.
- This project is ideal for teams seeking to build intelligent, searchable knowledge repositories from web data using the latest advancements in AI and vector storage.
