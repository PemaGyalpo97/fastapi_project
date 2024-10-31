from fastapi import FastAPI

app = FastAPI()

@app.get("/", description="This is our first route")
async def get():
    return {"message": "hello world"}

@app.put("/")
async def put():
    return {"message": "hello world from put route"}

@app.post("/")
async def post():
    return {"message": "hello world from post route"}