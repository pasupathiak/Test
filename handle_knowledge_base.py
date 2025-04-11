import glob
import shutil
from fastapi import Depends, HTTPException
import os
import pickle
import faiss
import fitz
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import and_
from database_session import get_db
from models import Tenant, UploadedFile
from save_kb_files import download_pdfs


def handle_knowledge_base(embedding_model, xt_id, db):

    pdf_directory = f"temp_kb_{xt_id}"
    print(pdf_directory)
    
    def get_files_from_db(xt_id, db):
        try:
            Urls = db.query(UploadedFile.file_name, UploadedFile.file_url).filter(
                (UploadedFile.tenant_id == int(xt_id)) & (UploadedFile.file_type == "application/pdf")).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=e)
        if not Urls:
            raise HTTPException(status_code=500, detail="Tenant Not Found")
        if not Urls:
            raise HTTPException(
                status_code=500, detail="Tenant has no Knowledge base files")
        return Urls

    url_list = get_files_from_db(xt_id, db)
    # url_list = [url[0] for url in url_list_with_tuples]

    try:
        download_pdfs(url_list, pdf_directory)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error in downloading{e}")

    def load_knowledge_base_from_folder():
        """Load the knowledge base from all PDF files in a folder and split into paragraph-level entries."""
        entries = []
        pdf_paths = glob.glob(os.path.join(pdf_directory, "*.pdf"))

        if not pdf_paths:
            print("⚠️ No PDF files found in the directory.")
            return entries

        for pdf_path in pdf_paths:
            if not os.path.exists(pdf_path):
                print(f"⚠️ PDF file not found: {pdf_path}")
                continue

            try:
                doc = fitz.open(pdf_path)
                text_content = []
                for page in doc:
                    text_content.append(page.get_text("text"))

                knowledge_text = "\n".join(text_content).strip()
                if not knowledge_text:
                    print(
                        f"⚠️ Warning: Extracted knowledge base is empty for {pdf_path}.")
                    continue

                # Split by double newlines to capture paragraphs rather than individual lines
                pdf_entries = [entry.strip() for entry in knowledge_text.split(
                    "\n\n") if entry.strip()]
                entries.extend(pdf_entries)
            except Exception as e:
                print(f"❌ Error loading PDF {pdf_path}: {e}")

        return entries

    # Load the knowledge base from the folder
    knowledge_base = load_knowledge_base_from_folder()

    if not knowledge_base:
        print("🚨 Knowledge base is empty.")
    else:
        print(
            f"✅ Loaded {len(knowledge_base)} entries from PDFs in the directory.")

    # Encode knowledge base using the updated embedding model
    if knowledge_base:
        knowledge_embeddings = np.array(
            [embedding_model.encode(text) for text in knowledge_base])
    else:
        # 768-dimension for all-mpnet-base-v2
        knowledge_embeddings = np.empty((0, 768))

    # Create and build FAISS index only if there are valid embeddings
    if knowledge_embeddings.shape[0] > 0:
        faiss_index = faiss.IndexFlatIP(knowledge_embeddings.shape[1])
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(knowledge_embeddings)
        faiss_index.add(knowledge_embeddings)

        directory = f"user_kb/{xt_id}"
        os.makedirs(directory, exist_ok=True)

        # Save the FAISS index and embeddings with the user_id to a file
        faiss_index_file = f"user_kb/{xt_id}/{xt_id}_faiss_index.index"
        faiss.write_index(faiss_index, faiss_index_file)

        # Optionally, save the knowledge embeddings separately if needed (e.g., for future reference or recovery)
        embeddings_file = f"user_kb/{xt_id}/{xt_id}_embeddings.pkl"
        with open(embeddings_file, 'wb') as f:
            pickle.dump({"embeddings": knowledge_embeddings,
                        "knowledge_base": knowledge_base}, f)
        if os.path.exists(pdf_directory):
            shutil.rmtree(pdf_directory)
            print(f"The folder at {pdf_directory} has been removed.")
        else:
            print(f"The folder at {pdf_directory} does not exist.")
        print(
            f"✅ FAISS index created and saved for user {xt_id} with {knowledge_embeddings.shape[0]} entries.")
    else:
        print("⚠️ FAISS index not created due to empty knowledge base.")
