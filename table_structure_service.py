import os
import requests
import shutil
import redis
from fastapi import HTTPException

from models import DatabaseService
from save_kb_files import download_sql

def read_sql_file(file_path):
    """Read the content of the SQL file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"❌ Error reading the SQL file: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error reading the SQL file: {str(e)}")


def update_table_structure(redis_client, xt_id, db):
    # Define a temporary folder where the SQL file will be downloaded
    temp_directory = f"temp_sql_{xt_id}"
    
    def get_files_from_db(xt_id, db):
        try:
            sql_byte = db.query(DatabaseService.file_url).filter(
                DatabaseService.user_id == int(xt_id)).first()
            if not sql_byte:
                raise HTTPException(status_code=404, detail="No sql file found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)
        if not sql_byte:
            raise HTTPException(status_code=500, detail="Tenant Not Found")
        if not sql_byte:
            raise HTTPException(
                status_code=500, detail="Tenant has no Knowledge base files")
        return sql_byte

    sql_byte = get_files_from_db(xt_id, db)

    download_sql(sql_byte, temp_directory)

    # Step 2: Read the content of the downloaded SQL file
    sql_content = read_sql_file(f"{temp_directory}/{temp_directory}.sql")
    if not sql_content:
        raise HTTPException(
            status_code=500, detail="SQL file is empty or failed to read.")
    print(f"Read SQL file with tennentId: {xt_id}")

    try:
        # Set data to Redis
        redis_client.set(f"Db_structure_{xt_id}", sql_content)
        print(f"✅ SQL structure content stored in Redis with xt_vox_id: {xt_id}")
    except redis.exceptions.ConnectionError as e:
        print(f"❌ Redis connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis connection error: {str(e)}")
    except redis.exceptions.ResponseError as e:
        print(f"❌ Redis response error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis response error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected Redis error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected Redis error: {str(e)}")

        # Step 4: Delete the temporary SQL file after reading and storing in Redis
    try:
        shutil.rmtree(temp_directory)
        print(f"✅ The temporary folder and SQL file have been deleted: {temp_directory}")
    except Exception as e:
        print(f"❌ Error deleting the temporary folder: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting the temporary folder: {str(e)}")
    except HTTPException as e:
        print(f"❌ HTTPException: {e}")
        raise e
    except Exception as e:
        print(f"❌ Unexpected error of type: {type(e)}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}")


# def update_table_structure(redis_client, xt_vox_id):
#     Db_structure = "https://www.sample-videos.com/sql/Sample-SQL-File-10rows.sql"

#     redis_client.zadd('Db_structure', {xt_vox_id: Db_structure})
