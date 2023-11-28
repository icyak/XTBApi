# XTBApi
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

# Simple tutorial
```python
from XTBApi.api import Client
USERID    = 1234567890            # ID from XTB webapp (top right corner, check if you are on real or demo)
PASSWORD  = 'random_pass_here'    # XTB password
TICKER    = 'ETHEREUM'            # ticker for trade
MODE      = 'demo'                # or use 'real' for real

# FIRST INIT THE CLIENT
client = Client()
# THEN LOGIN
client.login(USERID, PASSWORD, mode=MODE)
# CHECK IF MARKET IS OPEN FOR EURUSD
client.check_if_market_open([TICKER])
# BUY ONE VOLUME (FOR EURUSD THAT CORRESPONDS TO 100000 units, for ETHEREUM it is 1)
client.open_trade('buy', TICKER, 1)
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
# Usage of get_expirationtimeStamp
To use get_expirationtimeStamp(minutes to expire)
```python
import datetime
def get_expiration_timeStamp(minutes): #specify timestamp for order
    expitarion_timestamp = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(minutes=minutes)
    expitarion_timestamp = int(datetime.datetime.timestamp(expitarion_timestamp)) * 1000
    return expitarion_timestamp
```

# Examples of opening trades
Some example usage of client.open_trade with/without SL/TP and using volume/dollars
```python
# Open trade with SL/TP with volume 1, TP 5%, SL 5%, expiration in 60 minutes
client.open_trade('buy', 'ETHEREUM', volume=1, custom_message="buy",tp_per = 0.05, sl_per= 0.05,expiration_stamp=get_expiration_timeStamp(60))
# Open trade without SL/TP with volume 10
client.open_trade('buy', 'VWCE.DE', volume=10, custom_message="buy")
# Open trade without SL/TP with volume 1000
client.open_trade('buy', 'CARDANO', volume=1000, custom_message="buy")
# Open trade with 'volume=dollars/price' and you specify dollar size of trade, volume is rounded to accomotade 'lotStep' multiply
client.open_trade('buy', 'CARDANO', dollars=1000, custom_message="buy")
# Open trade without SL/TP, with 'volume=dollars/price' and you specify dollar size of trade, volume is rounded to accomotade 'lotStep' multiply
client.open_trade('buy', 'VWCE.DE', dollars=1000, custom_message="buy")
# Open trade with SL/TP, with volume 10 on instrument O.US CFD - internal XTB ticker is O.US_4
client.open_trade('buy', 'O.US', type_of_instrument='cfd', volume=10, custom_message="buy",tp_per = 0.05, sl_per= 0.05)
# Open trade without SL/TP, with volume 10 on instrument O.US - internal XTB ticker is O.US_9
client.open_trade('buy', 'O.US', type_of_instrument='stc',volume=10, custom_message="buy")
```

# Api Reference
http://developers.xstore.pro/documentation/#introduction
