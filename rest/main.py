import os
import uvicorn
import pandas as pd
from datetime import datetime
from pandas import DataFrame
from fastapi import FastAPI
from starlette.responses import JSONResponse
from tinkoff.invest import Client, OperationsResponse, Operation
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


@app.get("/operations")
def read_operations():
    with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
        account_id = client.users.get_accounts().accounts[0].id
        print(account_id)

        r: OperationsResponse = client.operations.get_operations(
            account_id=account_id,
            from_=datetime(2015, 1, 1),
            to=datetime.now()
        )

        if len(r.operations) < 1: return None
        df = pd.DataFrame([operation_todict(p, account_id) for p in r.operations])
        print(df.tail().to_json())

        return df.to_json(force_ascii=False)


def operation_todict(o: Operation, account_id: str):
    r = {
        'acc': account_id,
        'date': o.date,
        'type': o.type,
        'otype': o.operation_type,
        'currency': o.currency,
        'instrument_type': o.instrument_type,
        'figi': o.figi,
        'quantity': o.quantity,
        'state': o.state,
        'payment': cast_money(o.payment),
        'price': cast_money(o.price),
    }

    return r


def cast_money(v):
    return v.units + v.nano / 1e9  # nano - 9 нулей


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
