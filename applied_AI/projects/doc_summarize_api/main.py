from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/summarize")
def summarize():
    return {"status": "ok"}