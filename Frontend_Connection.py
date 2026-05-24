from fastapi import FastAPI, Form, UploadFile, File, Depends
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Header, HTTPException
from fastapi.staticfiles import StaticFiles
from DATABASE.SQL_Database import UserConnection
from Security.Advance_Logger import AdvancedLogger
from Security.JWT_token import create_token, decode_token
from RAG.EmbeddingsGenerationnStorage import EmbeddingsALL
from Files_Management.Files_Parser import ParseFile
from RAG.Vector_Store import VectorStore
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from pathlib import Path
import os
import tempfile
import shutil

Embedding_Generator = EmbeddingsALL()

logger = AdvancedLogger()

app = FastAPI()

User_Connection = UserConnection()

vector = VectorStore()

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_user_id(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]  # "Bearer <token>"
        return decode_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    

#Login Page
@app.get("/", response_class=HTMLResponse)
async def login_page():

    with open("templates/login.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.post("/login")
async def login( email: str = Form(...), password: str = Form(...) ):
    try:
        user = User_Connection.login_user(email=email, password=password)
        if user:
            logger.info(user)
            token = create_token(user_id=user["id"], email=email)
            return JSONResponse(
                        {
                            "success": True,
                            "message": "Login successful",
                            "token": token,
                            "user": {
                                "id": user["id"],
                                "name": user["name"],
                                "email": user["email"]
                            }
                        }
                    )
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": "User not found"
                }
            )
    except Exception as e:
        logger.error("Frontend_Connection.login", e)

@app.post("/signin")
async def signin(name: str = Form(...), email: str = Form(...), password: str = Form(...)) -> bool:
    user_id = User_Connection.get_Id_From_email(email=email)
    token = create_token(user_id=user_id, email=email)
    if User_Connection.create_user(name=name, email=email, password=password):
        return JSONResponse(
            {
                "success": True,
                "message": "sign-in successful",
                "token": token,
                "user": {
                    "id": User_Connection.get_Id_From_email(email=email),
                    "name": name,
                    "email": email
                }
            }
        )
    return JSONResponse(
        {
            "success": False,
            "message": "Failed to signin"
        }
    )

@app.post("/addDocument")
async def add_document(user_id: int = Depends(get_user_id), file: UploadFile = File(...) ):
    logger.info(user_id)
    temp_path = None
    try:
        suffix = os.path.splitext( file.filename )[1]
        file_name = file.filename
        file_extension = Path(file_name).suffix

        # Create temp file
        with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as temp_file:
            shutil.copyfileobj( file.file, temp_file )
            temp_path = temp_file.name

        extracted_text = ParseFile.parse_any_file(
            temp_path
        )

        if Embedding_Generator.generate_and_store_embeddings(user_id=user_id, file_name=file_name, extension=file_extension, Text=extracted_text):
            return JSONResponse(
                {
                    "success": True,
                    "filename": file.filename,
                    "message": "Document Uploaded Successfully"
                }
            )
        
        logger.error("add_document", "Failed to add document.")
        return JSONResponse(
            {
                "success": False,
                "message": "Failed to add Document!"
            }
        )
    
    except Exception as e:
        logger.error("add_documents", e)
        return JSONResponse(
            {
                "success": False,
                "message": str(e)
            }
        )
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/show_documents")
async def show_documents(user_id: int = Depends(get_user_id)):
    try:
        result = User_Connection.get_documents_data_by_userId(user_id=user_id)
        if result:
            json_compatible_data = jsonable_encoder(result)
            return JSONResponse(
                {
                    "success": True,
                    "message": "Here is the list",
                    "Documents_data": json_compatible_data
                }
            )
        return JSONResponse(
            {
                "success": False,
                "message": "Failed to fetch data",
                "Documents_data": []
            }
        )
    except Exception as e:
        logger.error("show_documents", e)
        return JSONResponse(
            {
                "success": False,
                "message": "Failed to fetch data",
                "Documents_data": []
            }
        )
    
@app.post("/delete_document")
async def delete_document_from_id(Document_id: int, user_id: int = Depends(get_user_id)):
    try:
        result = User_Connection.delete_document(user_id=user_id, document_id=Document_id)
        vector_ = vector.delete_vectors_by_document_id(document_id=Document_id, user_id=user_id)
        if result and vector:
            return JSONResponse(
                {
                    "success": True,
                    "message": "Document Deleted",
                    "Numbers_Of_Document_deleted": result
                }
            )
        return JSONResponse(
                {
                    "success": False,
                    "message": "Failed to fetch data",
                    "Numbers_Of_Document_deleted": 0
                }
            )
    except Exception as e:
        logger.error("delete_document_from_id", e)
        return JSONResponse(
            {
                "success": False,
                "message": "Failed to fetch data",
                "Numbers_Of_Document_deleted": 0
            }
        )

@app.post("/chat")
async def chat(user_id: int = Depends(get_user_id), query: str = Form(...)):
    try:
        
        answer = Embedding_Generator.answer_from_embeddings(user_id=user_id, user_query=query)
        return JSONResponse(
            {
                "success": True,
                "message": str(answer)
            }
        )
    except Exception as e:
        logger.error("Frontend_Connection.chat", e)
        return JSONResponse(
            {
                "success": False,
                "message": "Failed to generate answer. Please try Again later!"
            }
        )

@app.get("/signin", response_class=HTMLResponse)
async def signin_page():

    with open(
        "templates/signin.html",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()
    
@app.get("/dashboard", response_class=HTMLResponse)
async def Dashboard_page():

    with open("templates/dashboard.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    with open("templates/chat.html", "r", encoding="utf-8") as file:
        return file.read()