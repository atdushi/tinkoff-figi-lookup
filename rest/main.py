import os
import uvicorn
from pandas import DataFrame
from fastapi import FastAPI
from tinkoff.invest import Client
from tinkoff.invest.constants import INVEST_GRPC_API_SANDBOX
from tinkoff.invest.services import InstrumentsService

app = FastAPI()
TOKEN = os.getenv('tinkoff_sandbox_token')

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/ticker/{ticker}")
def read_ticker(ticker: str):
    with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
        instruments: InstrumentsService = client.instruments
        list = []
        for method in ['shares', 'bonds', 'etfs']:  # , 'currencies', 'futures']:
            for item in getattr(instruments, method)().instruments:
                list.append({
                    'ticker': item.ticker,
                    'figi': item.figi,
                    'type': method,
                    'name': item.name,
                })

        df = DataFrame(list)

        df = df[df['ticker'] == ticker.upper()]

        print(df.head())

        if df.empty:
            return f"Нет тикера {ticker}"

        return df['figi'].iloc[0]

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)