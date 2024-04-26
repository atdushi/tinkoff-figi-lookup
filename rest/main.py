import os
from datetime import datetime, timedelta

import pandas as pd
import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response
from pandas import DataFrame
from tinkoff.invest import Client, OperationsResponse, Operation, CandleInterval, PortfolioResponse, PortfolioPosition
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

        return Response(content=df.to_json(force_ascii=False), media_type='application/json')


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


@app.get("/candles/{figi}")
def read_candles(figi: str):
    with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
        response = client.market_data.get_candles(
            figi=figi,  # 'USD000UTSTOM'
            from_=datetime.now() - timedelta(days=7),
            to=datetime.now(),
            interval=CandleInterval.CANDLE_INTERVAL_HOUR
        )

        df = DataFrame([{
            'time': c.time,
            'volume': c.volume,
            'open': cast_money(c.open),
            'close': cast_money(c.close),
            'high': cast_money(c.high),
            'low': cast_money(c.low),
        } for c in response.candles])

        print(df.tail())

        return Response(content=df.to_json(), media_type='application/json')


@app.get("/portfolio")
def read_portfolio():
    with Client(TOKEN, target=INVEST_GRPC_API_SANDBOX) as client:
        account_id = client.users.get_accounts().accounts[0].id

        r: PortfolioResponse = client.operations.get_portfolio(account_id=account_id)
        df = pd.DataFrame([portfolio_pose_todict(p) for p in r.positions])

        print(df.tail())

        return Response(content=df.to_json(), media_type='application/json')


def portfolio_pose_todict(p: PortfolioPosition):
    r = {
        'figi': p.figi,
        'quantity': cast_money(p.quantity),
        'expected_yield': cast_money(p.expected_yield),
        'instrument_type': p.instrument_type,
        'average_buy_price': cast_money(p.average_position_price),
        'currency': p.average_position_price.currency,
        'nkd': cast_money(p.current_nkd),
    }

    return r


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
