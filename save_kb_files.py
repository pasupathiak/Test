"""
for pdf
"""

# import os
# import requests


# def download_pdfs(url_list, save_folder):
#     if not os.path.exists(save_folder):
#         os.makedirs(save_folder)

#     # url_list = ["https://www.ijfmr.com/papers/2024/2/14064.pdf",
#     #             "https://www.ijfmr.com/papers/2023/4/5657.pdf"]
#     for url in url_list:
#         print(f"started downloading: {url}")
#         try:
#             # Get the PDF from the URL
#             response = requests.get(url)
#             response.raise_for_status()  # Ensure we got a successful response

#             # Extract the file name from the URL
#             file_name = url.split("/")[-1]
#             if not file_name.endswith(".pdf"):
#                 file_name += ".pdf"  # In case the URL does not include the .pdf extension

#             # Save the PDF to the specified folder
#             with open(f"{save_folder}/{file_name}", "wb") as f:
#                 f.write(response.content)

#             print(f"Downloaded: {file_name}")

#         except requests.exceptions.RequestException as e:
#             print(f"Failed to download {url}: {e}")



import os
import requests
import base64
import json


def download_pdfs(url_list, save_folder):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        
    """
    for Bytes
    """
    for file_name, pdf_bytes in url_list:
        try:
            # Ensure filename ends with .pdf
            if not file_name.endswith(".pdf"):
                file_name += ".pdf"

            # Define full path to save the PDF
            full_path = os.path.join(save_folder, file_name)

            # Write the bytes directly to a PDF file
            with open(full_path, "wb") as f:
                f.write(pdf_bytes)

            print(f"Saved: {file_name}")

        except Exception as e:
            print(f"Failed to save {file_name}: {e}")

    """
    for base64
    """
    # for url in url_list:
    #     print(f"Started downloading: {url}")
    #     try:
    #         # Get the JSON response from the URL
    #         response = requests.get(url)
    #         response.raise_for_status()  # Ensure we got a successful response
            
    #         # Parse the JSON data
    #         data = response.json()  # Assuming the JSON contains the base64 PDF data
            
    #         # Extract the base64 PDF string from the nested JSON structure
    #         base64_pdf = data.get("fields", {}).get("kbFile", {}).get("mapValue", {}).get(
    #             "fields", {}).get("content", {}).get("stringValue", None)
            
    #         if not base64_pdf:
    #             print(f"No base64 PDF found in {url}")
    #             continue
                
    #         # Decode the base64 string
    #         pdf_content = base64.b64decode(base64_pdf)
        
    #         # Extract the file name from the URL or use a default name
    #         # Customize this further if needed
    #         file_name = url.split("/")[-1].replace(".json", ".pdf")
            
    #         if not file_name.endswith(".pdf"):
    #             file_name += ".pdf"
            
    #         # Save the PDF to the specified folder
    #         with open(os.path.join(save_folder, file_name), "wb") as f:
    #             f.write(pdf_content)
            
    #         print(f"Downloaded: {file_name}.pdf")

    #     except requests.exceptions.RequestException as e:
    #         print(f"Failed to download {url}: {e}")
    #     except json.JSONDecodeError:
    #         print(f"Failed to decode JSON response from {url}")
    #     except Exception as e:
    #         print(f"An error occurred while processing {url}: {e}")



def download_sql(url_list, save_folder):

    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    for sql_bytes in url_list:
        file_name = f"{save_folder}.sql"
        try:
            # Ensure filename ends with .sql
            if not file_name.endswith(".sql"):
                file_name += ".sql"

            # Define full path to save the SQL file
            full_path = os.path.join(save_folder, file_name)

            # Write the bytes directly to a SQL file
            with open(full_path, "wb") as f:
                f.write(sql_bytes)

            print(f"Saved: {file_name}")

        except Exception as e:
            print(f"Failed to save {file_name}: {e}")
            
            
# def download_sql_file(url, temp_directory):
#     """Download the SQL file from the provided URL and store it in the temporary directory."""
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for HTTP errors

#         # Create a temp file path
#         temp_file_path = os.path.join(temp_directory, "temp_sql_file.sql")

#         # Write the SQL file content to the temporary file
#         with open(temp_file_path, 'w') as file:
#             file.write(response.text)

#         print(f"✅ SQL file downloaded and saved to {temp_file_path}")
#         return temp_file_path
#     except requests.exceptions.RequestException as e:
#         print(f"❌ Error downloading the SQL file: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Error downloading the SQL file: {str(e)}")