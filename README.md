# SmartSacco AI Agent
<img width="1919" height="1019" alt="image" src="https://github.com/user-attachments/assets/6ab79ba9-7aa4-4840-a7a2-6b152ac82d3b" />

## What
- An AI agent/LLM that predicts whether a member of a given SACCO is likely to default on a loan based on previous loan history, credit score, and investment amounts.

## How to run SmartSacco
#### Prerequisites
- Python 3.10+
- A TiDB Cloud Starter cluster: Create a free cluster here: [tidbcloud.com](https://tidbcloud.com/)
- Ollama, you can install it from [Ollama](https://ollama.com/download)

#### first, start the enbedding service with Ollama
- pull the embedding model
  ```
     ollama pull mistral:7b
  ```
- Test the embedding service to make sure it is running:
 ```
  curl http://localhost:11434/api/embed -d '{
  "model": "mistral:7b",
  "input": "Llamas are members of the camelid family"
}'
```

1. Clone the repository:
   ```bash
   git clone https://github.com/Mikitoxo/Smartsacco1.git
   cd Smartsacco1
   ```
2. Set up a virtual environment and install dependencies
```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Use this on Windows
   pip install -r requirements.txt
```
3. Configure environment variables (create .env from .env.example with your TiDB credentials):
   If you are using TiDB Cloud, you can find the connection parameters in the [TiDB Cloud console](https://tidbcloud.com/).
   ```bash
      cat > .env <<EOF
   TIDB_HOST=gateway01.us-west-2.prod.aws.tidbcloud.com  # Replace with your host
   TIDB_PORT=4000
   TIDB_USERNAME=your_username  # e.g., 4CPrcEoPyoTLuQq.root
   TIDB_PASSWORD=your_password  # e.g., 5b8wsjXDrciBHV4i
   TIDB_PASSWORD=5b8wsjXDrciBHV4i
   TIDB_DATABASE=test
   EOF
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
5. Open [(http://localhost:8501)](http://localhost:8501) in your browser.


## How it works
- Input: User logs in and submits member_id of the Sacco member and amount they want to borrow.
- Search: Queries TiDB Serverless for member data.
- LLM Analysis: Ollama's Mistral 7B evaluates eligibility.
- Output: Based on the member data, the AI agent predicts whether or not the member is eligible for the loan, it also states    why they are/are not eligible.
   

