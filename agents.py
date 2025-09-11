from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_community.utilities import SQLDatabase
from langchain.schema.runnable import RunnablePassthrough
import datetime
import mysql.connector
from mysql.connector.cursor import MySQLCursorDict
from dotenv import load_dotenv
import os
import json
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables from .env
load_dotenv("c:/Users/mikik/OneDrive/Documents/Desktop/Smartsacco1/.env")
print("Environment variables loaded:")
for var in ['TIDB_HOST', 'TIDB_PORT', 'TIDB_USER', 'TIDB_PASSWORD', 'TIDB_DB']:
    value = os.getenv(var)
    print(f"{var}: {value}")
if not all([os.getenv('TIDB_HOST'), os.getenv('TIDB_USER'), os.getenv('TIDB_PASSWORD'), os.getenv('TIDB_DB')]):
    raise ValueError("Missing required environment variables in .env file")

# Database connection using TiDB Cloud details with SSL
db_uri = (
    f"mysql+mysqlconnector://{os.getenv('TIDB_USER')}:{os.getenv('TIDB_PASSWORD')}"
    f"@{os.getenv('TIDB_HOST')}:{os.getenv('TIDB_PORT', 4000)}/{os.getenv('TIDB_DB', 'test')}"
    "?ssl_ca=isrgrootx1 (5).pem"
)
print(f"Connecting to TiDB with URI: {db_uri}")
db = SQLDatabase.from_uri(db_uri)

# Direct MySQL connection for dictionary cursor
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('TIDB_HOST'),
        port=int(os.getenv('TIDB_PORT', 4000)),
        user=os.getenv('TIDB_USER'),
        password=os.getenv('TIDB_PASSWORD'),
        database=os.getenv('TIDB_DB', 'test'),
        ssl_ca="C:/Users/mikik/Downloads/isrgrootx1.pem",
        
        use_pure=True  # Ensure pure Python implementation
    )

# Authentication function for admin_logins
def authenticate_user(email, password):
    query = "SELECT password FROM admin_logins WHERE email = %s"
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_class=MySQLCursorDict)
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        conn.close()
        if result and result['password'] == password:
            return True
        return False
    except Exception as e:
        logging.error(f"Error authenticating user {email}: {e}")
        return False

# Retrieval Tool
def retrieve_member_data(member_id):
    query = """
    SELECT 
        md.member_id, 
        md.member_name, 
        COALESCE(SUM(i.amount_invested), 0) AS total_invested,
        md.credit_score, 
        md.member_phoneno,
        lh.loan_id, 
        lh.amount_borrowed, 
        lh.amount_due, 
        lh.amount_paid, 
        lh.due_date
    FROM 
        member_data md
    LEFT JOIN 
        loan_history2 lh ON md.member_id = lh.member_id
    LEFT JOIN 
        investments i ON md.member_id = i.member_id
    WHERE 
        md.member_id = %s
    GROUP BY 
        md.member_id, md.member_name, md.credit_score, md.member_phoneno, 
        lh.loan_id, lh.amount_borrowed, lh.amount_due, lh.amount_paid, lh.due_date
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_class=MySQLCursorDict)
        cursor.execute(query, (member_id,))
        result = cursor.fetchall()  # Returns list of dictionaries
        conn.close()
        logging.info(f"Retrieved data for member_id {member_id}: {result}")
        return result
    except Exception as e:
        logging.error(f"Error retrieving data for member_id {member_id}: {e}")
        return []

# Analysis Chain
llm = OllamaLLM(model="mistral:7b")
prompt = PromptTemplate(
    input_variables=["data", "amount"],
    template="""
    You are a loan eligibility analyst for SmartSacco. Analyze the following member data: {data} for a loan request of ${amount}. 

    **Data Field Mappings**:
    - `member_id`: Unique identifier for the member.
    - `member_name`: Name of the member.
    - `total_invested`: Sum of all investments from the investments table.
    - `credit_score`: Member's credit score from member_data.
    - `member_phoneno`: Member's phone number.
    - `loan_id`: ID of the loan from loan_history2.
    - `amount_borrowed`: Amount borrowed for the loan.
    - `amount_due`: Outstanding balance for the loan.
    - `amount_paid`: Amount already paid for the loan.
    - `due_date`: Due date for the loan payment or 'none' if null.

    **Rules for Eligibility**:
    - The member is eligible only if their `amount_due` = 0.
    - The loan amount must not exceed 3 times their `total_invested`.
    - The member's `credit_score` must be greater than 200.
    - If the `due_date` is within 7 days from 2025-09-11 (i.e., on or before 2025-09-18), include a reminder to pay in the response.

    **Response Format**:
    Provide a detailed, user-friendly explanation of the member's eligibility, including their credit score, total investments, and current balance (amount_due). Always mention the credit score explicitly. If eligible, confirm the loan amount is within limits. If ineligible, explain why (e.g., outstanding balance, insufficient investments, low credit score). Include any payment reminders if applicable.

    At the end of your response, include a JSON object with the following fields:
    ```json
    {{
        "eligible": "yes" or "no",
        "reasons": "brief explanation",
        "current_balance": amount_due,
        "due_date": "date or 'none'",
        "total_invested": total_invested,
        "credit_score": credit_score
    }}
    ```

    Example Response:
    The member has a credit score of 250, a total investment of $5000, and an outstanding balance of $0. The requested loan amount of $10000 is within 3 times the total investments ($15000). Since the amount due is $0 and the credit score is above 200, the member is eligible for the loan.

    ```json
    {{
        "eligible": "yes",
        "reasons": "No outstanding balance, sufficient investments, and good credit score",
        "current_balance": 0,
        "due_date": "none",
        "total_invested": 5000,
        "credit_score": 250
    }}
    ```
    """
)
analysis_chain = prompt | llm

# Notification Function
def process_notification(member_id, message):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_class=MySQLCursorDict)
        cursor.execute(
            "INSERT INTO notifications (member_id, message, sent_date) VALUES (%s, %s, %s)",
            (member_id, message, datetime.datetime.now())
        )
        conn.commit()
        conn.close()
        return {"notification": message, "member_id": member_id}
    except Exception as e:
        logging.error(f"Error processing notification for member_id {member_id}: {e}")
        return {"error": f"Failed to send notification: {e}"}

# Orchestrate
def process_loan_request(member_id, amount):
    logging.info(f"Processing request for member_id: {member_id}, type: {type(member_id)}, amount: {amount}")
    data = retrieve_member_data(member_id)
    if not data:
        return {"error": "Member not found or no data retrieved"}
    
    analysis = analysis_chain.invoke({"data": data, "amount": amount})
    try:
        # Extract JSON block from response
        json_str = re.search(r'```json\n(\{.*?\})\n```', analysis, re.DOTALL)
        result = json.loads(json_str.group(1)) if json_str else {"error": "No valid JSON found"}
        member_id = data[0].get('member_id') if data else None
        
        if result.get("eligible") == "yes" and "remind" in result.get("reasons", "").lower() and member_id:
            notification = process_notification(member_id, f"Pay reminder: Due by {result.get('due_date', 'soon')}")
            result["notification"] = notification.get("notification", notification.get("error"))
        
        # Include the narrative response
        narrative = analysis.split("```json")[0].strip() if "```json" in analysis else analysis
        result["narrative"] = narrative
        logging.info(f"Processed result for member_id {member_id}: {result}")
        return result
    except (json.JSONDecodeError, AttributeError) as e:
        logging.error(f"Failed to parse LLM output: {e}, raw response: {analysis}")
        return {"error": "Failed to parse LLM output or invalid data"}

# Wrapper function for compatibility with app.py
def get_loan_prediction(member_id, amount):
    return process_loan_request(member_id, amount)