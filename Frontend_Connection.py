from fastapi import FastAPI, Form, UploadFile, File, Depends
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_limiter.depends import RateLimiter
from fastapi import Header, HTTPException
from fastapi.staticfiles import StaticFiles
from DATABASE.SQL_Database import connect
from DATABASE.Redis_Connection import redis_cache
from Security.Advance_Logger import logger
from Security.JWT_token import create_token, decode_token
from Security.get_secretes import load_env_from_secret
from RAG.EmbeddingsGenerationnStorage import EmbeddingsALL
from Files_Management.Files_Parser import ParseFile
from RAG.Vector_Store import Vector
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from pathlib import Path
import asyncio
import os
import tempfile
import shutil

REDIS_URL = load_env_from_secret("REDIS_HOST")

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_cache.initialize()
    await FastAPILimiter.init(redis_cache.get_client())
    yield
    if redis_cache.pool:
        await redis_cache.pool.disconnect()

Embedding_Generator = EmbeddingsALL()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static", html=True), name="static")


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
    
@app.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def login( email: str = Form(...), password: str = Form(...) ):
    try:
        user = connect.login_user(email=email, password=password)
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

@app.post("/signin", dependencies=[Depends(RateLimiter(times=3, seconds=60))])
async def signin(name: str = Form(...), email: str = Form(...), password: str = Form(...)) -> bool:
    user_id = connect.get_Id_From_email(email=email)
    token = create_token(user_id=user_id, email=email)
    if connect.create_user(name=name, email=email, password=password):
        return JSONResponse(
            {
                "success": True,
                "message": "sign-in successful",
                "token": token,
                "user": {
                    "id": connect.get_Id_From_email(email=email),
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

@app.post("/addDocument", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def add_document(user_id: int = Depends(get_user_id), files: list[UploadFile] = File(...) ):
    try:
        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                temp_path = None

                suffix = os.path.splitext( file.filename )[1]
                file_name = file.filename
                file_extension = Path(file_name).suffix

                BLACKLISTED_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.z', '.exe'}
                if file_extension in BLACKLISTED_EXTENSIONS:
                    failed_files.append({
                        "filename": file.filename,
                        "reason": "Blocked extension"
                    })
                    continue
                
                MAX_FILE_SIZE = 15 * 1024 * 1024  
                file.file.seek(0, os.SEEK_END)
                actual_size = file.file.tell()
                file.file.seek(0)

                if actual_size > MAX_FILE_SIZE:
                    failed_files.append({
                        "filename": file.filename,
                        "reason": "File too large"
                    })

                    continue

                # Create temp file
                with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as temp_file:
                    shutil.copyfileobj( file.file, temp_file )
                    temp_path = temp_file.name

                extracted_text = await ParseFile.parse_any_file(
                    temp_path
                )

                stored_ = await Embedding_Generator.generate_and_store_embeddings(user_id=user_id, file_name=file_name, extension=file_extension, Text=extracted_text)
                if stored_:
                    uploaded_files.append(
                        file.filename
                    )
                else:
                    logger.error("add_document", "Failed to add document.")
                    failed_files.append({
                            "filename": file.filename,
                            "reason": "Embedding failed"
                        })
                
            except Exception as e:
                logger.error("for_loop.add_document", e)
                failed_files.append({
                "filename": file.filename,
                "reason": str(e)
            })
            
            finally:

                if (temp_path and os.path.exists(temp_path)):
                    os.remove(temp_path)

        await redis_cache.invalidate_user_cache(user_id=user_id)

        return JSONResponse({
            "success": True,
            "uploaded": uploaded_files,
            "failed": failed_files
        })
    
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
        cache_key = f"user_docs_meta:{user_id}"

        cached_metadata = await redis_cache.get_json(cache_key)
        if cached_metadata is not None:
            return JSONResponse({
                "success": True,
                "message": "Here is the list (cached)",
                "Documents_data": cached_metadata
            })
        
        result = connect.get_documents_data_by_userId(user_id=user_id)
        if result:
            json_compatible_data = jsonable_encoder(result)
            await redis_cache.set_json(cache_key, json_compatible_data, ex=600)
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
        result = connect.delete_document(user_id=user_id, document_id=Document_id)
        Vector_ = Vector.delete_vectors_by_document_id(document_id=Document_id, user_id=user_id)
        if result and Vector_:
            await redis_cache.invalidate_user_cache(user_id=user_id)
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

@app.post("/chat", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def chat(user_id: int = Depends(get_user_id), query: str = Form(...)):
    try:
        
        answer = await Embedding_Generator.answer_from_embeddings(user_id=user_id, user_query=query)
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
    
@app.post("/logout")
async def logout(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]  # Extract "Bearer <token>"
        
        # Blacklist the token in Redis to prevent reuse
        await redis_cache.blacklist_token(token=token, expiry_seconds=604800)
        
        return JSONResponse(
            {
                "success": True,
                "message": "Logout successful. Token revoked."
            }
        )
    except Exception as e:
        logger.error("Frontend_Connection.logout", e)
        return JSONResponse(
            {
                "success": False,
                "message": "Logout failed. Invalid authorization format."
            },
            status_code=400
        )
    
@app.get("/dashboard", response_class=HTMLResponse)
async def Dashboard_page():

    with open("templates/dashboard.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    with open("templates/chat.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    with open("templates/settings.html", "r", encoding="utf-8") as file:
        return file.read()
    
@app.middleware("http")
async def add_cache_control_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static"):
        # Cache static CSS/JS files for 1 day to minimize server hits
        response.headers["Cache-Control"] = "public, max-age=86400"
    return response