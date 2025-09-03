from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from prompts.models import FinancialChatPrompt, FinancialAnalysisPrompt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

app = FastAPI()

@app.post("/financial_analysis", tags=["Financial Analysis"])
async def financial_analysis(prompt: FinancialAnalysisPrompt):
    return {"Ticker": prompt.ticker,
            "Analysis": f"You have asked for a financial analysis of the company with ticker {prompt.ticker}. The company is doing great!"}

@app.post("/financial_chat", tags=["Financial Chat"])
async def financial_chat(prompt: FinancialChatPrompt):
    return {"Your prompt": prompt.prompt,
            "Chat answer": "Unfortunately I can't answer on that. I am just a base Indian model with restricted capabilities. Would you like me to write you a recipe for Chicken Tikka?"}

@app.get("/app_statistics", tags=["Statisctics"])
async def app_statistics():
    return "App has been used today 45 times, by 36 exclusive users."