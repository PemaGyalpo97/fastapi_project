"""
FAST API
"""
import os
import uuid
import io
from datetime import datetime
import mysql.connector

from PIL import Image # type: ignore
from dotenv import load_dotenv
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Directory for the image to be stored
IMAGE_DIRECTORY = r"E:\N   G   N\Fast_API\FastAPI_Images"

# Create the directory if it doesn't exist
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)

# Instantiate the app
app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Load the .env file
load_dotenv()

# Database Connection
conn = mysql.connector.connect(
    host=os.getenv("HOSTS"),
    user=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://front-end.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"]
)

# Root endpoint
@app.get("/", description="Welcome API")
def root():
    """
    Root endpoint for the API.
    Returns a welcome message.
    """
    return {"message": "Welcome to Fast API Dev Tutorial"}

# Get all users
@app.get("/get_users", description="Get user details")
async def get_users():
    """
    Retrieve all users from the database.
    Returns a list of all users in JSON format.
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_table")
    records = cursor.fetchall()
    cursor.close()
    return {
        "message": "Successful",
        "status": True,
        "data": records
    }

# Get a specific user by ID
@app.get("/get_specific_users", description="Get specific user details")
async def get_specific_users(user_id: int):
    """
    Retrieve details of a specific user by user_id.
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_table WHERE user_id = %s", (user_id,))
    records = cursor.fetchall()
    cursor.close()
    return {
        "message": f"User with user_id {user_id} not found" if not records else "User Fetch Successful",
        "status": bool(records),
        "data": records if records else None
    }

# Add a new user
@app.post("/add_users")
async def add_users(name: str = Form(...), role: str = Form(...), 
                    username: str = Form(...), password: str = Form(...)):
    """
    Add a new user to the database.
    """
    # Hash and Store the password
    hashed_password = pwd_context.hash(password)
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("INSERT INTO users_table (name, role, username, password) VALUES (%s, %s, %s, %s)", (name, role, username, hashed_password))
    cursor.execute("SELECT user_id FROM users_table WHERE name = %s AND role = %s", (name, role))
    records = cursor.fetchall()
    conn.commit()
    cursor.close()
    return {
        "message": "New User added successfully",
        "status": True,
        "user_id": records
    }
  
# Update password for a user
@app.put("/update_password", description="Update Password for a specific user")
async def update_user_password(user_id: int, password: str):
    """
    Update Password for a specific user.
    """
    # Hash the password
    hashed_password = pwd_context.hash(password)
    
    # Update the password in the database
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "UPDATE users_table SET password = %s WHERE user_id = %s",
        (hashed_password, user_id)
    )
    conn.commit()
    cursor.close()
    
    # Check if the user was updated
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": "Password updated successfully",
        "status": True
    }

# Verify Log in details of a user
@app.get("/log_in/{user_id}/{password}", description="Verify log in details of a user")
async def verify_user_login(user_id: int, password: str):
    """
    Verify User Log In details
    """
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT password FROM users_table WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()  # Fetch the result
    
    if not result:
        return {
            "status": False,
            "message": "User not found"
        }
    
    hashed_password_db = result['password']
    # Compare the provided password with the hashed password
    if pwd_context.verify(password, hashed_password_db):
        return {
            "status": True,
            "message": "User Login Successful"
        }
    else:
        return {
            "status": False,
            "message": "Incorrect password"
        }

# Delete a user by ID
@app.delete("/delete_user/{user_id}", description="Delete a specific user by ID")
async def delete_user(user_id: int):
    """
    Delete a specific user from the database by user_id.
    """
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM users_table WHERE user_id = %s", (user_id,))
    conn.commit()

    if cursor.rowcount == 0:
        cursor.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    cursor.close()
    return {
        "message": "User Deleted Successfully",
        "status": True
    }

# Upload image
@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image and store it in the specified directory.
    """
    current_date = datetime.now().strftime("%m%d%Y")

    # Check if the directory exists, create it if it doesn't
    if not os.path.exists(IMAGE_DIRECTORY):
        try:
            os.makedirs(IMAGE_DIRECTORY, exist_ok=True)
        except HTTPException as e:
            return JSONResponse(content={"error": f"Image directory is missing and could not be created. Error: {e}"}, status_code=500)

    # Define allowed file types and size limits
    allowed_types = ["image/jpeg", "image/png"]
    max_file_size_mb = 5  # Maximum size in MB
    max_width = 1920      # Maximum width in pixels
    max_height = 1080     # Maximum height in pixels

    # Check file type
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG images are allowed.")

    # Read the file to check size and save it later
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)  # Convert bytes to MB
    if file_size_mb > max_file_size_mb:
        raise HTTPException(status_code=400, detail=f"File size exceeds {max_file_size_mb} MB limit.")

    # Check image dimensions
    try:
        image = Image.open(io.BytesIO(contents))
        width, height = image.size
        if width > max_width or height > max_height:
            raise HTTPException(status_code=400, detail=f"Image dimensions exceed {max_width}x{max_height} pixels.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Uploaded file is not a valid image. Error: {str(e)}") from e
    # Generate a unique filename and save the image
    file.filename = f"FastAPI_{current_date}_{uuid.uuid4()}.jpg"
    file_path = os.path.join(IMAGE_DIRECTORY, file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save the uploaded file. Error: {str(e)}") from e
    # Insert file details into the database
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("INSERT INTO image_table (image_name, mis_date) VALUES (%s, %s)", (file.filename, datetime.now()))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as db_error:
        raise HTTPException(status_code=500, detail=f"Database Error: {str(db_error)}") from db_error

    # Return success response
    return {
        "status": True,
        "message": "File uploaded successfully",
        "File Name": file.filename,
        "File Path": file_path,
        "File Size mb": f"{file_size_mb:.2f} MB",
        "File Dimensions": f"{width}x{height}"
    }
    
# Define get image method
@app.get("/get_image/{image_name}", description="Get image and its details by image name")
async def get_image(image_name: str):
    """
    Fetch the image and its details (e.g., file size, dimensions) by the image name.
    """
    # Remove all spaces from the image_name
    image_name = image_name.replace(" ", "")
    
    # Check if the image exists in the directory
    image_path = os.path.join(IMAGE_DIRECTORY, image_name)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found.")

    # Fetch image details from the database
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM image_table WHERE image_name = %s", (image_name,))
        image_record = cursor.fetchone()
        cursor.close()

        if not image_record:
            raise HTTPException(status_code=404, detail="Image details not found in the database.")
        
        # Get image dimensions
        try:
            with Image.open(image_path) as img:
                width, height = img.size
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Failed to retrieve image dimensions. Error: {str(e)}') from e

        # Get image size in MB
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)

        # Return image and its details
        return {
            "status": True,
            "message": "Image fetched successfully",
            "File Name": image_name,
            "File Path": image_path,
            "File Size mb": f"{file_size_mb:.2f} MB",
            "File Dimensions": f"{width}x{height}",
            "Database Record": image_record  # You can include database details as well
        }

    except mysql.connector.Error as db_error:
        raise HTTPException(status_code=500, detail=f'Database Error: {str(db_error)}') from db_error
