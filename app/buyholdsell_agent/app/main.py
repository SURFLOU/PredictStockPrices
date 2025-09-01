import asyncio
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.azure import AzureProvider
from agents.ben_graham import create_ben_graham_agent
from dotenv import load_dotenv
from settings import AgentSettings

load_dotenv()
cfg = AgentSettings()

async def main():
    model = OpenAIChatModel(
        cfg.llm_model,
        provider=AzureProvider(
            azure_endpoint=cfg.azure_endpoint,
            api_version=cfg.azure_api_version,
            api_key=cfg.azure_api_key,
        ),
    )

    ben_graham_agent = create_ben_graham_agent(model)

    input_text = """
Ticker: AAPL

Analysis:
{
  "score": 11,
  "max_score": 15,
  "earnings_analysis": {
    "score": 3,
    "details": "EPS was positive in all available periods; EPS grew from earliest to latest."
  },
  "strength_analysis": {
    "score": 3,
    "details": "Current ratio = 2.5; Debt ratio = 0.35; Paid dividends in 6/10 years."
  },
  "valuation_analysis": {
    "score": 5,
    "details": "Net-Net margin > 50%; Graham Number = $120; Price per share = $320"
  }
}
"""
    result = await ben_graham_agent.run(input_text)
    print(result.output)

if __name__ == "__main__":
    asyncio.run(main())
