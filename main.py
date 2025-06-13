from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import bots, exchange_keys

app = FastAPI()

# 🔐 CORS setup - update with your real frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["https://deally.in"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response

# 📦 Register routers
app.include_router(bots.router, prefix="/bots", tags=["Bots"])
app.include_router(exchange_keys.router, prefix="/exchange-keys", tags=["Exchange Keys"])

@app.get("/")
def read_root():
    return {"message": "DCA Bot Backend running"}

@app.get("/health")
def health_check():
    return {"message": "Backend is healthy"}
