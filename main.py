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
async def get_users():
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_table")
    records = cursor.fetchall()
    cursor.close()
    return {
        "message": "Successful",
        "status": True,
        "data": records
    }

# Define get specific users method
@app.get("/get_specific_users", description="Get specific user details")
async def get_specific_users(user_id: int):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users_table where user_id = %s", (user_id,))
    records = cursor.fetchall()
    cursor.close()
    return {
        "message": (
            f"User with user_id {user_id} not found" if not records 
            #else "User Fetch Successful (user_id is 5)" if records[0]["user_id"] == 5 
            else "User Fetch Successful"
        ),
        "status": bool(records),  # False if records is empty, True otherwise
        "data": records if records else None
    }

# Define add user method
@app.post("/add_users")
async def add_users(name: str = Form(...), role: str = Form(...)):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("INSERT INTO users_table (name, role) VALUES (%s, %s)", (name, role))
    cursor.execute("select user_id from users_table where name = (%s) and role = (%s)", (name, role))
    records = cursor.fetchall()
    conn.commit()
    cursor.close()
    return {
        "message": "New User added successfully",
        "status": True,
        "user_id": records
    }

@app.delete("/delete_user", description="Delete a specific user by ID")
async def delete_user(user_id: int):
    cursor = conn.cursor()
    
    # Execute delete SQL command
    cursor.execute("DELETE FROM users_table WHERE user_id = %s", (user_id,))
    conn.commit()  # Commit the transaction to apply changes
    
    cursor.close()
    
    return {
        "message": "User Deleted Successfully",
        "status": True
    }

