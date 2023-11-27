# XTBApi

> Api for XTB trading platform.

A python based API for XTB trading using _websocket_client_.

# Installing / Getting started

To install the API, just clone the repository.

```bash
git clone git@github.com:federico123579/XTBApi.git
cd XTBApi/
python3 -m venv env
. env/bin/activate
pip install .
```

Then you can use XTBApi like this simple tutorial.
```python
from XTBApi.api import Client
# FIRST INIT THE CLIENT
client = Client()
# THEN LOGIN
client.login("{user_id}", "{password}", mode={demo,real})
# CHECK IF MARKET IS OPEN FOR EURUSD
client.check_if_market_open([EURUSD])
# BUY ONE VOLUME (FOR EURUSD THAT CORRESPONDS TO 100000 units)
client.open_trade('buy', EURUSD, 1)
# SEE IF ACTUAL GAIN IS ABOVE 100 THEN CLOSE THE TRADE
trades = client.update_trades() # GET CURRENT TRADES
trade_ids = [trade_id for trade_id in trades.keys()]
for trade in trade_ids:
    actual_profit = client.get_trade_profit(trade) # CHECK PROFIT
    if actual_profit >= 100:
        client.close_trade(trade) # CLOSE TRADE
# CLOSE ALL OPEN TRADES
client.close_all_trades()
# THEN LOGOUT
client.logout()
```

Some example usage of client.open_trade with/without SL/TP and using volume/dollars

```python
# Open trade with SL/TP with volume 1
client.open_trade('buy', 'ETHEREUM', volume=1, custom_Message="buy",tp_per = 0.05, sl_per= 0.05,expiration_stamp=get_expiration_timeStamp(60))
# Open trade without SL/TP with volume 10
client.open_trade('buy', 'VWCE.DE', volume=10, custom_Message="buy")
# Open trade without SL/TP with volume 1000
client.open_trade('buy', 'CARDANO', volume=1000, custom_Message="buy")
# Open trade with volume=dollars/price, if volume need to be multiple of 10, it creates failed order and then tries it again with volume rounded to multiple of 10
client.open_trade('buy', 'CARDANO', dollars=1000, custom_Message="buy")

```





# Api Reference
REQUIRED - **SOON**

_Documentation still in progess_
