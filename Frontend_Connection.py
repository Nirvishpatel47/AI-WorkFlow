from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from DATABASE.SQL_Database import UserConnection
from Security.Advance_Logger import AdvancedLogger
from Files_Management.Files_Parser import ParseFile
import os
import tempfile
import shutil

logger = AdvancedLogger()

app = FastAPI()

User_Connection = UserConnection()

app.mount("/static", StaticFiles(directory="static"), name="static")

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
            return JSONResponse(
                        {
                            "success": True,
                            "message": "Login successful",
                            "user": {
                                "id": user.id,
                                "name": user.name,
                                "email": user.email
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
    if User_Connection.create_user(name=name, email=email, password=password):
        return JSONResponse(
            {
                "success": True,
                "message": "sign-in successful",
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
async def add_document( file: UploadFile = File(...) ):
    temp_path = None
    try:
        suffix = os.path.splitext( file.filename )[1]

        # Create temp file
        with tempfile.NamedTemporaryFile( delete=False, suffix=suffix ) as temp_file:
            shutil.copyfileobj( file.file, temp_file )
            temp_path = temp_file.name

        # Parse file
        extracted_text = ParseFile.parse_any_file(
            temp_path
        )
        return JSONResponse(
            {
                "success": True,
                "filename": file.filename,
                "text": extracted_text
            }
        )
    except Exception as e:
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
