from pydantic import BaseModel

class FinancialAnalysisPrompt(BaseModel):
    ticker: str

class FinancialChatPrompt(BaseModel):
    prompt: str