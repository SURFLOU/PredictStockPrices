from pydantic import BaseModel
from typing import Literal
from pydantic_ai import AIModel, tool


class AswathDamodaranSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float 
    reasoning: str


class DamodaranInput(BaseModel):
    ticker: str
    financial_data: str  # Raw string with financial info


class DamodaranOutput(BaseModel):
    signal: AswathDamodaranSignal


class DamodaranModel(AIModel):
    """
    Analyze financial data in the style of Aswath Damodaran and produce a trading signal.
    """

    @tool
    def analyze(self, input: DamodaranInput) -> DamodaranOutput:
        system_prompt = (
            "You are Aswath Damodaran, Professor of Finance at NYU Stern.\n"
            "Use your valuation framework to issue trading signals on US equities.\n\n"
            "Speak clearly and analytically:\n"
            "- Start with the company's story (qualitatively)\n"
            "- Connect to numbers: growth, margins, reinvestment, risk\n"
            "- Conclude with FCFF DCF estimate, margin of safety, and signal\n"
            "- Respond ONLY with valid JSON in the specified format."
        )

        human_prompt = f"""
            Ticker: {input.ticker}

            Financial Data:
            {input.financial_data}

            Respond in this JSON format:
            {{
            "signal": "bullish" | "bearish" | "neutral",
            "confidence": float (0-100),
            "reasoning": "string"
            }}
        """

        result = self.llm.chat(
            system=system_prompt,
            messages=[("human", human_prompt)],
            output_model=AswathDamodaranSignal,
        )

        return DamodaranOutput(signal=result)
