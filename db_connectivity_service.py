
from decimal import Decimal
import json
import sqlite3
from fastapi import HTTPException
import mysql.connector
import psycopg2
import requests
import pyodbc

from models import DatabaseService

def get_db_details(tennent_id, db):
    
    def get_files_from_db(tennent_id, db):
        try:
            database_details = db.query(DatabaseService).filter(
                DatabaseService.user_id == int(tennent_id)).first()
            if not database_details:
                raise HTTPException(status_code=404, detail="No database details configured")
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)
        return database_details

    database_details = get_files_from_db(tennent_id, db)
    
    db_type = database_details.db_type
    host = database_details.db_host
    port = database_details.db_port
    user = database_details.db_username 
    password = database_details.db_password
    db_names = database_details.db_name
    
    # db_type = "postgres" # input("Enter database type (mysql/postgres/sqlserver/oracle/sqlite): ").strip().lower()
    # host = "103.174.10.6" # input("Enter database host (IP or hostname, leave empty for SQLite): ").strip()
    # port = 5432 # input("Enter database port (leave empty for SQLite): ").strip()
    # user = "xtuser" # input("Enter username (leave empty for SQLite): ").strip()
    # password = "xtpass" # input("Enter password (leave empty for SQLite): ").strip()
    # db_names = "test_db"
    return db_type, host, port, user, password, db_names


def giveDataToAi(query):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            # 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
            # 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
            # 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
            # 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
            # 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
            # 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
            "Authorization": "Bearer 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",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
            {
                "role": "user",
                "content": query
            }
            ],
            
        })
    )
    if(str(response) == "<Response [200]>"):
        return response.json()["choices"][0]["message"]["content"]
    elif response.status_code == 400:
        return "Bad Request: Please check your request syntax."
    elif response.status_code == 401:
        return "Unauthorized: You need to provide valid credentials."
    elif response.status_code == 404:
        return "Not Found: The requested resource could not be found."
    elif response.status_code == 500:
        return "Internal Server Error: Something went wrong on the server."
    else:
        return f"Error: Received status code {response.status_code}." + response.json()["choices"][0]["message"]["content"]

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)  # Convert Decimal to float
    raise TypeError(f"Type {type(obj)} not serializable")


def execute_query(db_type, query, db_config):
    try:
        conn = None
        cursor = None

        if db_type == "sqlite":
            conn = sqlite3.connect(db_config["database"])
        elif db_type == "mysql":
            conn = mysql.connector.connect(
                host=db_config["host"],
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"]
            )
        elif db_type == "postgresql":
            conn = psycopg2.connect(
                host=db_config["host"],
                user=db_config["user"],
                password=db_config["password"],
                database=db_config["database"]
            )
        elif db_type == "sqlserver":
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={db_config['server']};DATABASE={db_config['database']};UID={db_config['user']};PWD={db_config['password']}"
            )
        else:
            raise HTTPException(status_code=404, detail=str("No Valid database Found"))
            
        cursor = conn.cursor()
        cursor.execute(query)

        if query.strip().lower().startswith("select"):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            try:
                return json.dumps(result)  # Convert the result to JSON format
            except:
                return json.dumps(result, default=decimal_default)
                

        else:
            conn.commit()
            print("Query executed successfully.")

    except Exception as e:
        print("Error:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def processAnalitics(tennent_id, user_message, Db_structure, db):
    db_type, host, port, user, password, db = get_db_details(tennent_id, db)

    userQuery = "This is my Table structure, " + Db_structure + " I need a SQL query to get the data to this question: " + user_message

    try:
        sql_query = giveDataToAi(userQuery).split('```sql\n')[1].split('```')[0]
    except:
        sql_query = giveDataToAi(userQuery).split('```sql\n')[1].split('```')[0]

    print(sql_query)
    db_config = {
        "host": host,
        "user": user,
        "password": password,
        "database": db,
        "port": port
    }

    query_result = None
    try:
        query_result = execute_query(db_type, sql_query, db_config)
    except Exception as e:
        sql_query = giveDataToAi(userQuery).split('```sql\n')[1].split('```')[0]
        query_result = execute_query(db_type, sql_query, db_config)
        
    if sql_query and query_result is None:
        query_result = execute_query(db_type, sql_query, db_config)
    
    Prompt_for_user_response = f"Please provide a valid, polite, and respectful response without any introductory statements based on the following question and answer: Question: {user_message} Answer: {query_result}"
    try:
        UserResponse = giveDataToAi(Prompt_for_user_response)   
    except:
        print("Retrying")
        UserResponse = giveDataToAi(Prompt_for_user_response)  
    if not UserResponse:
        UserResponse = giveDataToAi(Prompt_for_user_response)
    
    return UserResponse, query_result
