from fastapi import FastAPI, Form, HTTPException
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware

# Instantiate the app
app = FastAPI()

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="root",
    database="usermanagement"
)

# CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Declaring the default method
@app.get("/", description="Welcome API")
def root():
    return {"message": "Welcome to Fast API Dev Tutorial"}

# Define get method
@app.get("/get_users", description="Get user details")
def get_users():
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_table")
    records = cursor.fetchall()
    cursor.close()
    return {
        "message": "Successful",
        "status": True,
        "data": records
    }

# Define add user method
@app.post("/add_users")
def add_users(name: str = Form(...), role: str = Form(...)):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("INSERT INTO users_table (name, role) VALUES (%s, %s)", (name, role))
    conn.commit()
    cursor.close()
    return {
        "message": "New User added successfully",
        "status": True
    }
