# openai-scrapper
The OpenAI Scrapper is an advanced web scraping solution designed to automate the extraction, summarization, and storage of web content using state-of-the-art AI and vector database technologies. Leveraging the power of LangChain, this project enables seamless interaction with large language models to process and summarize scraped data efficiently.

## Requirements

- Python 3.12.10
- FastAPI
- Uvicorn
- LangChain
- OpenAI
- Qdrant

## Installation
### Clone the repository:

```bash
git clone <your-repo-url>
cd openai-scrapper
```

### Upload and startup a Database
Go to https://github.com/qdrant/qdrant/releases and get last version of qdrant.exe for windows. Or download tested version [qdrant-x86_64-pc-windows-msvc.zip](https://github.com/qdrant/qdrant/releases/download/v1.16.3/qdrant-x86_64-pc-windows-msvc.zip)

Put qdrant.exe in your cloned project and launch it in project terminal by writing in it (may be different in your environment):
```
./qdrant.exe
```

### Add OPENAI_API_KEY as Environment Variable:
Prerequisites
You must have an OpenAI account. If you don’t have one, sign up at https://platform.openai.com/signup.
After that you will need to the [Billing](https://platform.openai.com/settings/organization/billing/overview) and add some credits to balance.  
5$ is totally enough to test it.

Step 1: Log in to OpenAI Platform
Go to https://platform.openai.com/.
Click Sign In and enter your credentials.

Step 2: Access API Keys Section
Once logged in, click on your profile icon (top right corner).
Select View API Keys from the dropdown menu.

Step 3: Create a New API Key
On the API Keys page, click the + Create new secret key button.
Enter a name for your key (optional, for your reference). Click Create secret key.

Step 4: Copy and Store Your API Key
A new API key will be displayed. Copy it immediately—you won’t be able to see it again!
Store the key securely (e.g., in a password manager or a secure environment variable).

Step 5: Use the API Key
Add it as Environment Variable OPENAI_API_KEY. Set as Environment Variable in PyCharm for launcher.py.
1) Open your project in PyCharm.
2) Go to Run > Edit Configurations...
3) Select your script or create a new configuration.
4) In the configuration window, find the Environment variables field.
5) Click the ... button next to it.
6) In the dialog, click the + button to add a new variable.
7) Enter:
   - Name: OPENAI_API_KEY
   - Value: your-actual-api-key
8) Click OK to save.
9) Run your script from PyCharm. The environment variable will be available to your code.

### Use Launcher:
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
