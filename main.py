from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routers import bots, exchange_keys, webhook_receiver, webhook  # ✅ include webhook
from app.services.evaluator import evaluate_condition_groups

evaluate_condition_groups()  # optional - runs once at startup for testing

app = FastAPI()

# 🔐 CORS setup - change in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with ["https://deally.in"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔍 Log all incoming requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response

# 📦 Register routers
app.include_router(bots.router, prefix="/bots", tags=["Bots"])
app.include_router(exchange_keys.router, prefix="/exchange-keys", tags=["Exchange Keys"])
app.include_router(webhook_receiver.router, tags=["Webhook Receiver"])
app.include_router(webhook.router, tags=["Webhook"])  # ✅ register webhook routes

# 🏠 Basic routes
@app.get("/")
def read_root():
    return {"message": "DCA Bot Backend running"}

@app.get("/health")
def health_check():
    return {"message": "Backend is healthy"}

@app.get("/test-webhook")
def test_webhook():
    return {"message": "Webhook working!"}
