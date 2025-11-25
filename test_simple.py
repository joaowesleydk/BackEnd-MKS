from fastapi import FastAPI

app = FastAPI(title="MKS Store Test")

@app.get("/")
def test():
    return {"message": "Backend funcionando!", "status": "ok"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)