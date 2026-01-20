from fastapi import FastAPI
import shapi  # Impor file Anda (opsional jika ingin gunakan isinya)

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "message": "API is running!",
        "endpoints": ["/", "/health", "/example"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/example")
def example_endpoint():
    # Contoh penggunaan salah satu fungsi dari shapi.py
    example_result = shapi.Wfti0hdS() if hasattr(shapi, 'Wfti0hdS') else "No function found"
    return {"example": example_result}

# Jika ingin menjalankan langsung dengan uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
