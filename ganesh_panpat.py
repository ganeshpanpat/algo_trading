import streamlit as st
import numpy
import requests
import datetime
from dateutil.tz import gettz
import pandas as pd
from SmartApi.smartConnect import SmartConnect
import pyotp
from logzero import logger
import pandas_ta as pdta
import warnings
import yfinance as yf
import time
import re
warnings.filterwarnings('ignore')
NoneType = type(None)
import math

st.set_page_config(page_title="Algo App",layout="wide",initial_sidebar_state="expanded",)
st.markdown("""
  <style>
    .block-container {padding-top: 0rem;padding-bottom: 0rem;padding-left: 2rem;padding-right: 2rem;}
  </style>
  """, unsafe_allow_html=True)
st.text("Welcome To Algo Trading")

if 'Logged_in' not in st.session_state:st.session_state['Logged_in']="Guest"
if 'login_time' not in st.session_state:st.session_state['login_time']="login_time"
if 'last_check' not in st.session_state:st.session_state['last_check']="last_check"
if 'bnf_expiry_day' not in st.session_state: st.session_state['bnf_expiry_day']=None
if 'nf_expiry_day' not in st.session_state: st.session_state['nf_expiry_day']=None
if 'sensex_expiry_day' not in st.session_state: st.session_state['sensex_expiry_day']=None
if 'monthly_expiry_day' not in st.session_state: st.session_state['monthly_expiry_day']=None
if 'opt_list' not in st.session_state:st.session_state['opt_list']=[]
if 'fut_list' not in st.session_state:st.session_state['fut_list']=['TCS','SBIN','RELIANCE','SAIL','TRENT','HDFCBANK']
if 'options_trade_list' not in st.session_state:st.session_state['options_trade_list']=[]
if 'index_trade_end' not in st.session_state:st.session_state['index_trade_end']={}
if 'todays_trade' not in st.session_state:st.session_state['todays_trade']=[]
if 'orderbook' not in st.session_state:st.session_state['orderbook']=[]
if 'pending_orders' not in st.session_state:st.session_state['pending_orders']=[]
if 'near_opt_df' not in st.session_state:st.session_state['near_opt_df']=[]
fut_list=st.session_state['fut_list']

def get_token_df():
  url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
  d = requests.get(url).json()
  token_df = pd.DataFrame.from_dict(d)
  token_df['expiry'] = pd.to_datetime(token_df['expiry']).apply(lambda x: x.date())
  token_df = token_df.astype({'strike': float})
  now_dt=datetime.datetime.now(tz=gettz('Asia/Kolkata')).date()-datetime.timedelta(days=0)
  token_df=token_df[token_df['expiry']>=now_dt]
  bnf_expiry_day = (token_df[(token_df['name'] == 'BANKNIFTY') & (token_df['instrumenttype'] == 'OPTIDX')])['expiry'].min()
  nf_expiry_day = (token_df[(token_df['name'] == 'NIFTY') & (token_df['instrumenttype'] == 'OPTIDX')])['expiry'].min()
  sensex_expiry_day = (token_df[(token_df['name'] == 'SENSEX') & (token_df['instrumenttype'] == 'OPTIDX')])['expiry'].min()
  monthly_expiry_day = (token_df[(token_df['name'] == 'RELIANCE') & (token_df['instrumenttype'] == 'OPTSTK')])['expiry'].min()
  st.session_state['bnf_expiry_day']=bnf_expiry_day
  st.session_state['nf_expiry_day']=nf_expiry_day
  st.session_state['sensex_expiry_day']=sensex_expiry_day
  st.session_state['monthly_expiry_day']=monthly_expiry_day
  opt_list=token_df[((token_df['name'] == 'BANKNIFTY') & (token_df['expiry'] == bnf_expiry_day) |
                   (token_df['name'] == 'NIFTY') & (token_df['expiry'] == nf_expiry_day) |
                   (token_df['name'] == 'SENSEX') & (token_df['expiry'] == sensex_expiry_day) |
                   (token_df['name'].isin(fut_list) & (token_df['expiry'] == monthly_expiry_day)))]
  st.session_state['opt_list']=opt_list
if st.session_state['nf_expiry_day']==None:get_token_df()

login_details=st.empty()
login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
index_ltp_string=st.empty()
index_ltp_string.text(f"Index Ltp: ")
log_tb, order_tb, position_tb, open_odr_tb, setting_tb, token_tb, gtt_tb, back_test_tb, near_opt_tb= st.tabs(["Log","Order Book", "Position",
                "Open Order", "Settings","Token List","GTT Orders",'Back Test','Near Options'])

with log_tb:
  col1,col2=st.columns([1,9])
  with col1:
    nf_ce=st.button(label="NF CE")
    bnf_ce=st.button(label="BNF CE")
    nf_pe=st.button(label="NF PE")
    bnf_pe=st.button(label="BNF PE")
    close_all=st.button("Close All")
    restart=st.button("Restart")
    algo_state=st.checkbox("Run Algo")
  with col2:
    trade_info=st.empty()
    log_holder=st.empty()
with order_tb:
  order_book_updated=st.empty()
  order_book_updated.text(f"Orderbook : ")
  order_datatable=st.empty()
with position_tb:
  position_updated=st.empty()
  position_updated.text(f"Position : ")
  position_datatable=st.empty()
with open_odr_tb:
  open_order_updated=st.empty()
  open_order_updated.text(f"Open Order : ")
  open_order=st.empty()
with setting_tb:
  ind_col1,ind_col2,ind_col3,ind_col4=st.columns([5,1.5,1.5,1.5])
  indicator_list=['TEMA_EMA_9 Trade','MA_50_ST Trade','ST_7_3 Trade', 'ST_10_2 Trade','ST_10_1 Trade','RSI MA Trade','RSI_60 Trade','MACD Trade','PSAR Trade',
                  'DI Trade','MA Trade','EMA Trade','EMA_5_7 Trade','MA 21 Trade','HMA Trade','RSI_60 Trade','EMA_High_Low Trade',
                  'Two Candle Theory','Multi Time ST Trade','RSI_WMA_9 Trade','High Break Trade','Vwap ST_7_3 Trade']
  with ind_col1:
    index_list=st.multiselect('Select Index',['NIFTY','BANKNIFTY','SENSEX','FINNIFTY'],['BANKNIFTY', 'NIFTY', 'SENSEX','FINNIFTY'])
    time_frame_interval = st.multiselect('Select Time Frame',['IDX:5M','IDX:15M','IDX:1M','OPT:5M','OPT:1M','GTT:5M','STK:5M'],['IDX:5M','OPT:5M','STK:5M'])
    five_buy_indicator = st.multiselect('5M Indicator',indicator_list,['ST_7_3 Trade', 'ST_10_2 Trade','MA_50_ST Trade'])
    five_opt_buy_indicator = st.multiselect('5M OPT Indicator',indicator_list,['ST_7_3 Trade', 'ST_10_2 Trade','MA_50_ST Trade'])
    gtt_indicator=st.multiselect('GTT Indicator',['5M_ST','5M_ST_10_2','1M_10_1','1M_10_2'],['5M_ST','5M_ST_10_2'])
    one_buy_indicator = st.multiselect('1M Indicator',indicator_list,[])
    one_opt_buy_indicator = st.multiselect('1M OPT Indicator',indicator_list,[])
    fifteen_buy_indicator = st.multiselect('15M Indicator',indicator_list,['MA_50_ST Trade'])
    three_buy_indicator = st.multiselect('3M Indicator',indicator_list,[])
    fut_list=st.multiselect('Select Future',fut_list,fut_list)
    with ind_col2:
      target_order_type = st.selectbox('Target Order',('Target', 'Stop_Loss', 'NA'),1)
      target_type = st.selectbox('Target Type',('Points', 'Per Cent','Indicator','ATR'),3)
      if target_type=="ATR":
        sl_point=st.number_input(label="SL",min_value=1, max_value=100, value=3, step=None)
        target_point=st.number_input(label="Target",min_value=1, max_value=100, value=3, step=None)
      elif target_type!="Per Cent":
        sl_point=st.number_input(label="SL",min_value=1, max_value=100, value=30, step=None)
        target_point=st.number_input(label="Target",min_value=1, max_value=100, value=50, step=None)
      elif target_type!="Indicator":
        sl_point=st.number_input(label="SL",min_value=1, max_value=100, value=30, step=None)
        target_point=st.number_input(label="Target",min_value=1, max_value=100, value=50, step=None)
    with ind_col3:
      lots_to_trade=st.number_input(label="Lots To Trade",min_value=1, max_value=10, value=1, step=None)
    with ind_col4:
      st.write('Expiry Dates:')
      st.write(f"Bank Nifty: {st.session_state['bnf_expiry_day']}")
      st.write(f"Nifty: {st.session_state['nf_expiry_day']}")
      st.write(f"SENSEX: {st.session_state['sensex_expiry_day']}")
with token_tb:
    token_df=st.empty()
    token_df=st.dataframe(st.session_state['opt_list'],hide_index=True)
with gtt_tb:
  gtt_order_updated=st.empty()
  gtt_order_updated.text(f"GTT Open Order : ")
  gtt_order_datatable=st.empty()
with back_test_tb:
  backtest=st.button(label="Back Test")
with near_opt_tb:
  near_opt_updated=st.empty()
  near_opt_updated.text(f"Near Option Updated : ")
  near_opt_df=st.empty()
  near_opt_df=st.dataframe(st.session_state['near_opt_df'],hide_index=True)

def telegram_bot_sendtext(bot_message):
  BOT_TOKEN = '5051044776:AAHh6XjxhRT94iXkR4Eofp2PPHY3Omk2KtI'
  BOT_CHAT_ID = '-1001542241163'
  try:
    bot_message=st.session_state['Logged_in']+':\n'+bot_message
    send_text = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + BOT_CHAT_ID + \
                  '&parse_mode=HTML&text=' + bot_message
    response = requests.get(send_text)
  except Exception as e: pass

user='Ganesh'; username = 'G93179'; pwd = '4789'; apikey = 'Rz6IiOsd'; token='U4EAZJ3L44CNJHNUZ56R22TPKI'
obj = SmartConnect(apikey)
totp = pyotp.TOTP(token).now()
correlation_id = "abcde"
data = obj.generateSession(username, pwd, totp)
if data['status'] == False:logger.error(data)
else:
  authToken = data['data']['jwtToken']
  refreshToken = data['data']['refreshToken']
  feedToken = obj.getfeedToken()
  res = obj.getProfile(refreshToken)
  obj.generateToken(refreshToken)
  userProfile= obj.getProfile(refreshToken)
  aa= userProfile.get('data')
  login_name=aa.get('name').title()
  st.session_state['Logged_in']=login_name.split()[0]
  st.session_state['login_time']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0).time()
  st.session_state['last_check']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0).time()

def place_order(token,symbol,qty,buy_sell,ordertype='MARKET',price=0,variety='NORMAL',exch_seg='NFO',producttype='CARRYFORWARD',
                triggerprice=0,squareoff=0,stoploss=0,ordertag='-'):
  try:
    orderparams = {"variety": variety,
                   "tradingsymbol": symbol,
                   "symboltoken": token,
                   "transactiontype": buy_sell,
                   "exchange": exch_seg,
                   "ordertype": ordertype,
                   "producttype": producttype,
                   "duration": "DAY",
                   "price": int(float(price)),
                   "squareoff":int(float(squareoff)),
                   "stoploss": int(float(stoploss)),
                   "quantity": str(qty),
                   "triggerprice":int(float(triggerprice)),
                   "ordertag":ordertag,"trailingStopLoss":5}
    orderId=obj.placeOrder(orderparams)
    return orderId
  except Exception as e:
    logger.info(f"error in place_order Order placement failed: {e}")
    orderId='Order placement failed'
    telegram_bot_sendtext(f'{buy_sell} Order placement failed : {symbol}')
    return orderId

def modify_order(variety,orderid,ordertype,producttype,price,quantity,tradingsymbol,symboltoken,exchange,triggerprice=0,squareoff=0,stoploss=0):
  try:
    modifyparams = {"variety": variety,
                    "orderid": orderid,
                    "ordertype": ordertype,
                    "producttype": producttype,
                    "duration": "DAY",
                    "price": price,
                    "quantity": quantity,
                    "tradingsymbol":tradingsymbol,
                    "symboltoken":symboltoken,
                    "exchange":exchange,
                    "squareoff":squareoff,
                    "stoploss": stoploss,
                    "triggerprice":triggerprice}
    obj.modifyOrder(modifyparams)
  except Exception as e:
    logger.info(f"error in modify_order: {e}")

def cancel_order(orderID,variety):
  try:
    obj.cancelOrder(orderID,variety=variety)
  except Exception as e:
    logger.info(f"Error cancel_order: {e}")

def cancel_all_order(symbol):
  try:
    orderbook,pending_orders=get_order_book()
    if isinstance(orderbook,NoneType)!=True:
      orderlist = orderbook[(orderbook['tradingsymbol'] == symbol) &
                            ((orderbook['orderstatus'] != 'complete') & (orderbook['orderstatus'] != 'cancelled') &
                              (orderbook['orderstatus'] != 'rejected') & (orderbook['orderstatus'] != 'AMO CANCELLED'))]
      orderlist_a = orderbook[(orderbook['tradingsymbol'] == symbol) & (orderbook['variety'] == 'ROBO') &
                              (orderbook['transactiontype'] == 'BUY') & (orderbook['orderstatus'] == 'complete')]
      orderlist=pd.concat([orderlist,orderlist_a])
      for i in range(0,len(orderlist)):
        cancel_order(orderlist.iloc[i]['orderid'],orderlist.iloc[i]['variety'])
  except Exception as e:
    logger.info(f"Error cancel_all_order: {e}")

def get_yf_ltp(symbol="-",token="-",exch_seg='-'):
  try:
    data=yf.Ticker(symbol).history(interval='1m',period='3d')
    return round(float(data['Close'].iloc[-1]),2)
  except Exception as e:
    logger.info(f"error in get_yf_ltp: {e}")
    return "Unable to get LTP"
  
def get_angel_ltp(symbol="-",token="-",exch_seg='-'):
    try:
      market_data = obj.getMarketData("LTP", {"exch_seg": [token]})
      return market_data['data']['fetched'][0]['ltp']
    except Exception as e:
        try:
            ltp_data = obj.ltpData(exch_seg, symbol, token)
            return ltp_data['data']['ltp']
        except Exception as e: return "Unable to get LTP"

def get_ltp_price(symbol="-",token="-",exch_seg='-'):
  try:
    symbol_i="-";ltp="Unable to get LTP"
    if symbol=="BANKNIFTY" or symbol=="^NSEBANK": symbol_i="^NSEBANK";token='99926009';exch_seg='NSE'
    elif symbol=="NIFTY" or symbol=="^NSEI": symbol_i="^NSEI";token='99926000';exch_seg='NSE'
    elif symbol=="SENSEX" or symbol=="^BSESN": symbol_i="^BSESN";token='99919000';exch_seg='BSE'
    if symbol_i!="-":ltp=get_yf_ltp(symbol=symbol_i,token=token,exch_seg=exch_seg)
    if ltp=="Unable to get LTP":ltp=get_angel_ltp(symbol=symbol,token=token,exch_seg=exch_seg)
    return ltp
  except Exception as e:
    logger.info(f"error in get_ltp_price: {e}")
    return "Unable to get LTP"

def print_ltp():
  try:
    data=pd.DataFrame(obj.getMarketData(mode="OHLC",exchangeTokens={"NSE": ["99926000","99926009"],"BSE": ['99919000']})['data']['fetched'])
    data['change']=data['ltp']-data['close']
    data.sort_values(by=['tradingSymbol'], inplace=True)
    print_sting=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()
    for i in range(0,len(data)):
      print_sting=f"{print_sting} {data.iloc[i]['tradingSymbol']} {int(data.iloc[i]['ltp'])}({int(data.iloc[i]['change'])})"
    print_sting=print_sting.replace("Nifty 50","Nifty")
    print_sting=print_sting.replace("Nifty Bank","BankNifty")
    return print_sting
  except Exception as e:
    logger.info(f"error in print_ltp: {e}")
    return None

def get_open_position():
  try:
    position=obj.position()
    if position['status']==True and position['data'] is not None:
      position=position['data']
      position=pd.DataFrame(position)
      position[['realised', 'unrealised']] = position[['realised', 'unrealised']].astype(float)
      pnl=int(position['realised'].sum())+float(position['unrealised'].sum())
      open_position = position[(position['netqty'] > '0') & (position['instrumenttype'] == 'OPTIDX')]
      if len(open_position)==0:open_position=None
      position_datatable.dataframe(position[['tradingsymbol',"totalbuyavgprice","totalsellavgprice","netqty",'realised', 'unrealised','ltp']],hide_index=True)
      position_updated.text(f"PNL : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}: {pnl}")
      return position,open_position
    else:
      position_updated.text(f"No Open Position : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
      return None,None
  except Exception as e:
    position_updated.text(f"error in get_open_position : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
    logger.info(f"error in get_open_position: {e}")
    return None,None

def get_order_book():
  try:
    orderbook=obj.orderBook()
    if orderbook['status']==True and orderbook['data'] is not None:
      orderbook=orderbook['data']
      orderbook=pd.DataFrame(orderbook)
      g_orderbook=orderbook[['updatetime','orderid','transactiontype','status','tradingsymbol','price','averageprice','quantity','ordertag']]
      g_orderbook['updatetime'] = pd.to_datetime(g_orderbook['updatetime']).dt.time
      g_orderbook = g_orderbook.sort_values(by=['updatetime'], ascending=[False])
      order_datatable.dataframe(g_orderbook,hide_index=True)
      order_book_updated.text(f"Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
      pending_orders = orderbook[((orderbook['orderstatus'] != 'complete') & (orderbook['orderstatus'] != 'cancelled') &
                              (orderbook['orderstatus'] != 'rejected') & (orderbook['orderstatus'] != 'AMO CANCELLED'))]
      pending_orders = pending_orders[(pending_orders['instrumenttype'] == 'OPTIDX')]
      n_pending_orders=pending_orders[['updatetime','orderid','transactiontype','status','tradingsymbol','price','averageprice','quantity','ordertag']]
      n_pending_orders = n_pending_orders.sort_values(by=['updatetime'], ascending=[False])
      open_order.dataframe(n_pending_orders,hide_index=True)
      open_order_updated.text(f"Pending Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
      return orderbook,pending_orders
    else:
      order_book_updated.text(f"No Order : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
      return None,None
  except Exception as e:
    print(f'Error in getting order book {e}')
    order_book_updated.text(f"Error in getting Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
    return None,None
  
def yfna_data(symbol,interval,period):
  try:
    df=yf.Ticker(symbol).history(interval=interval,period=str(period)+"d")
    df['Datetime'] = df.index
    df['Datetime']=df['Datetime'].dt.tz_localize(None)
    df.index=df['Datetime']
    df=df[['Datetime','Open','High','Low','Close','Volume']]
    df['Date']=df['Datetime'].dt.strftime('%m/%d/%y')
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.time
    df=df[['Date','Datetime','Open','High','Low','Close','Volume']]
    df=df.round(2)
    if isinstance(df, str) or (isinstance(df, pd.DataFrame)==True and len(df)==0):
      logger.info(f"Yahoo Data Not Found {symbol}: {e}")
      return "No data found, symbol may be delisted"
    return df
  except Exception as e:
    logger.info(f"error in yfna_data {symbol}: {e}")
    return None

def angel_data(token,interval,exch_seg,period=5):
  try:
    to_date= datetime.datetime.now(tz=gettz('Asia/Kolkata'))
    from_date = to_date - datetime.timedelta(days=period)
    fromdate = from_date.strftime("%Y-%m-%d %H:%M")
    todate = to_date.strftime("%Y-%m-%d %H:%M")
    historicParam={"exchange": exch_seg,"symboltoken": token,"interval": interval,"fromdate": fromdate, "todate": todate}
    res_json=obj.getCandleData(historicParam)
    df = pd.DataFrame(res_json['data'], columns=['timestamp','O','H','L','C','V'])
    df = df.rename(columns={'timestamp':'Datetime','O':'Open','H':'High','L':'Low','C':'Close','V':'Volume'})
    df['Datetime'] = df['Datetime'].apply(lambda x: datetime.datetime.fromisoformat(x))
    df['Datetime'] = pd.to_datetime(df['Datetime'],format = '%Y-%m-%d %H:%M:%S')
    df['Datetime']=df['Datetime'].dt.tz_localize(None)
    df = df.set_index('Datetime')
    df['Datetime']=pd.to_datetime(df.index,format = '%Y-%m-%d %H:%M:%S')
    df['Date']=df['Datetime'].dt.strftime('%m/%d/%y')
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.time
    df=df[['Date','Datetime','Open','High','Low','Close','Volume']]
    return df
  except Exception as e:
    logger.info(f"error in angel_data : {e}")
    return None

def get_historical_data(symbol="-",interval='5m',token="-",exch_seg="-",candle_type="NORMAL"):
  try:
    symbol_i="-";df=None
    if (symbol=="^NSEI" or symbol=="NIFTY") : symbol_i,token,exch_seg="^NSEI",99926000,"NSE"
    elif (symbol=="^NSEBANK" or symbol=="BANKNIFTY") : symbol_i,token,exch_seg="^NSEBANK",99926009,"NSE"
    elif (symbol=="^BSESN" or symbol=="SENSEX") : symbol_i,token,exch_seg="^BSESN",99919000,"BSE"
    if symbol[3:]=='-EQ': symbol_i=symbol[:-3]+".NS"
    if (interval=="5m" or interval=='FIVE_MINUTE'): period,delta_time,agl_interval,yf_interval=5,5,"FIVE_MINUTE","5m"
    elif (interval=="1m" or interval=='ONE_MINUTE') : period,delta_time,agl_interval,yf_interval=1,1,"ONE_MINUTE","1m"
    elif (interval=="15m" or interval=='FIFTEEN_MINUTE'): period,delta_time,agl_interval,yf_interval=5,15,"FIFTEEN_MINUTE","15m"
    elif (interval=="60m" or interval=='ONE_HOUR'): period,delta_time,agl_interval,yf_interval=30,60,"ONE_HOUR","60m"
    elif (interval=="1d" or interval=='ONE_DAY') : period,delta_time,agl_interval,yf_interval=100,5,"ONE_DAY","1d"
    else:period,delta_time,agl_interval,yf_interval=5,1,"ONE_MINUTE","1m"
    if (symbol_i[0]=="^") or symbol_i[3:]=='.NS':df=yfna_data(symbol_i,yf_interval,period)
    else:df=angel_data(token,agl_interval,exch_seg,period)
    now=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None)
    if now - df.index[-1] > datetime.timedelta(minutes=5):df=angel_data(token,agl_interval,exch_seg,period)
    now=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None)
    last_candle=now.replace(second=0, microsecond=0)- datetime.timedelta(minutes=delta_time)
    df = df[(df.index <= last_candle)]
    df['Time Frame']=yf_interval
    df['Time']=now.time()
    df.index.names = ['']
    df['VWAP']=pdta.vwap(high=df['High'],low=df['Low'],close=df['Close'],volume=df['Volume'])
    df = df.reset_index(drop=True)
    df=df[['Time','Date','Datetime','Open','High','Low','Close','Volume','VWAP','Time Frame']]
    df['Symbol']=symbol
    df=calculate_indicator(df)
    df=df.round(2)
    return df
  except Exception as e:
    logger.info(f"error in get_historical_data: {e}")
    return None

def get_trade_info(df):
    trade_columns = ['ST_7_3 Trade','MACD Trade','PSAR Trade','DI Trade','MA Trade','EMA Trade','BB Trade','Trade','Trade End',
                     'Rainbow MA','Rainbow Trade','MA 21 Trade','ST_10_2 Trade','Two Candle Theory','HMA Trade','VWAP Trade',
                     'EMA_5_7 Trade','ST_10_4_8 Trade','EMA_High_Low Trade','RSI MA Trade','RSI_60 Trade','ST_10_1 Trade',
                     'TEMA_EMA_9 Trade','RSI_WMA_9 Trade','High Break Trade','Vwap ST_7_3 Trade','MA_50_ST Trade','MA_50 Trade']
    
    for col in trade_columns:df[col] = '-'
    time_frame = df['Time Frame'][0]
    Symbol = df['Symbol'][0]
    symbol_type = "IDX" if Symbol in ["^NSEBANK", "BANKNIFTY", "^NSEI", "NIFTY", "SENSEX", "^BSESN"] else "OPT"
    indicator_list = []
    if symbol_type == "IDX":
        if time_frame == "5m":indicator_list = five_buy_indicator
        elif time_frame == "15m":indicator_list = fifteen_buy_indicator
        else:indicator_list = ['ST_7_3 Trade', 'ST_10_2 Trade', 'TEMA_EMA_9 Trade', 'RSI_60 Trade']
    elif symbol_type == "OPT":
        if time_frame == "5m":indicator_list = five_opt_buy_indicator
        elif time_frame == "15m":indicator_list = []
        elif time_frame == "1m":indicator_list = one_opt_buy_indicator
        else:indicator_list = ['ST_7_3 Trade', 'ST_10_2 Trade', 'TEMA_EMA_9 Trade', 'RSI_60 Trade']
    
    df['Indicator'] = symbol_type + " " + df['Time Frame']
    df['Trade'] = "-"
    df['Trade End'] = "-"
    sl="-"
    # Ensure that the DataFrame has at least two rows to perform the check
    if len(df) >= 2:
      i = len(df) - 1  # Get the index of the last row
      try:           
        if df.iloc[i-1]['Close'] <= df.iloc[i-1]['Supertrend'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend']:
          df.loc[i, 'ST_7_3 Trade'] = "Buy"
          if symbol_type == "OPT":sl=df.iloc[i]['Supertrend']
        elif df.iloc[i-1]['Close'] >= df.iloc[i-1]['Supertrend'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend']:
          df.loc[i, 'ST_7_3 Trade'] = "Sell"

        if df.iloc[i]['MACD'] > df.iloc[i]['MACD signal'] and df.iloc[i-1]['MACD'] < df.iloc[i-1]['MACD signal']:
          df.loc[i, 'MACD Trade'] = "Buy"
        elif df.iloc[i]['MACD'] < df.iloc[i]['MACD signal'] and df.iloc[i-1]['MACD'] > df.iloc[i-1]['MACD signal']:
          df.loc[i, 'MACD Trade'] = "Sell"

        if df.iloc[i-1]['Close'] < df.iloc[i-1]['Supertrend_10_2'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend_10_2']:
          df.loc[i, 'ST_10_2 Trade'] = "Buy"
          if symbol_type == "OPT":sl=df.iloc[i]['Supertrend_10_2']
        elif df.iloc[i-1]['Close'] > df.iloc[i-1]['Supertrend_10_2'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend_10_2']:
          df.loc[i, 'ST_10_2 Trade'] = "Sell"

        if df.iloc[i-1]['Close'] < df.iloc[i-1]['Supertrend_10_1'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend_10_1']:
          df.loc[i, 'ST_10_1 Trade'] = "Buy"
          if symbol_type == "OPT":sl=df.iloc[i]['Supertrend_10_1']
        elif df.iloc[i-1]['Close'] > df.iloc[i-1]['Supertrend_10_1'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend_10_1']:
          df.loc[i, 'ST_10_1 Trade'] = "Sell"

        if df.iloc[i-1]['Tema_9'] < df.iloc[i-1]['EMA_9'] and df.iloc[i]['Tema_9'] > df.iloc[i]['EMA_9'] and float(df.iloc[i]['RSI']) >= 55:
          df.loc[i, 'TEMA_EMA_9 Trade'] = "Buy"
        elif df.iloc[i-1]['Tema_9'] > df.iloc[i-1]['EMA_9'] and df.iloc[i]['Tema_9'] < df.iloc[i]['EMA_9']:
          df.loc[i, 'TEMA_EMA_9 Trade'] = "Sell"

        if int(df.iloc[i]['RSI']) >= 60 and int(df.iloc[i-1]['RSI']) < 60:df.loc[i, 'RSI_60 Trade'] = "Buy"
        if int(df.iloc[i]['RSI_9']) >=  int(df.iloc[i]['WMA_RSI_9']) and int(df.iloc[i-1]['RSI_9']) <=  int(df.iloc[i-1]['WMA_RSI_9']) :df.loc[i, 'RSI_WMA_9 Trade'] = "Buy"

        if df['Close'][i] > df['Close'][i-1] and df['Close'][i] > df['Close'][i-2] and df['Close'][i] > df['Close'][i-3] and df['Close'][i] > df['Close'][i-4] and df['Close'][i] > df['Close'][i-5]:
          df['High Break Trade'][i] = "Buy"
          if symbol_type == "OPT":sl=min(df['Close'][i],df['Close'][i-1])

        if df.iloc[i-1]['Close'] <= df.iloc[i-1]['MA_50'] and df.iloc[i]['Close'] > df.iloc[i]['MA_50']:df.loc[i, 'MA_50 Trade'] = "Buy"
        elif df.iloc[i-1]['Close'] >= df.iloc[i-1]['MA_50'] and df.iloc[i]['Close'] < df.iloc[i]['MA_50']:df.loc[i, 'MA_50 Trade'] = "Sell"

        if df.loc[i, 'MA_50 Trade'] == "Buy" and df.loc[i, 'ST_7_3 Trade'] == "Buy":
          df.loc[i, 'MA_50_ST Trade'] = "Buy"
          if symbol_type == "OPT":sl=df.iloc[i]['Supertrend']
        elif df.loc[i, 'MA_50 Trade'] == "Sell" and df.loc[i, 'ST_7_3 Trade'] == "Sell":df.loc[i, 'MA_50_ST Trade'] = "Sell"
    
        for indicator_trade in indicator_list:
            if df[indicator_trade][i] == "Buy":
                df.loc[i, 'Trade'] = "Buy"
                df.loc[i, 'Trade End'] = "Buy"
                df.loc[i, 'Indicator'] = df['Indicator'][i] + ":" + indicator_trade + ' RSI:' + str(int(df['RSI'][i]))  + ' ATR:' + str(int(df['Atr'][i]))
                break
            elif df[indicator_trade][i] == "Sell":
                df.loc[i, 'Trade'] = "Sell"
                df.loc[i, 'Trade End'] = "Sell"
                df.loc[i, 'Indicator'] = df['Indicator'][i] + ":" + indicator_trade + ' RSI:' + str(int(df['RSI'][i])) + ' ATR:' + str(int(df['Atr'][i]))
                break
      except Exception as e: pass
    return df

def calculate_indicator(df):
  try:
    df['RSI']=pdta.rsi(df['Close'],timeperiod=9)
    df['RSI_14']=pdta.rsi(df['Close'],timeperiod=14)
    df['MACD']=pdta.macd(close=df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)['MACD_12_26_9']
    df['MACD signal']=pdta.macd(close=df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)['MACDs_12_26_9']
    df['Macdhist']=pdta.macd(close=df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)['MACDh_12_26_9']
    df['Supertrend']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=7,multiplier=3)['SUPERT_7_3.0']
    df['Supertrend_10_2']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=2)['SUPERT_10_2.0']
    df['Supertrend_10_1']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=1)['SUPERT_10_1.0']
    df['Atr']=pdta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)
    df['Tema_9']=pdta.tema(df['Close'],9)
    df['EMA_9']=pdta.ema(df['Close'],length=6)
    df['RSI_9']=pdta.rsi(df['Close'],timeperiod=9)
    df['WMA_RSI_9']=pdta.wma(df['RSI_9'],length=9)
    df['MA_50']=df['Close'].rolling(50).mean()
    #df['UBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBU_20_2.0']
    #df['MBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBM_20_2.0']
    #df['LBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBL_20_2.0']
    #df['Supertrend_10_4']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=4)['SUPERT_10_4.0']
    #df['Supertrend_10_8']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=8)['SUPERT_10_8.0']
    #df['PSAR']=pdta.psar(high=df['High'],low=df['Low'],acceleration=0.02, maximum=0.2)['PSARl_0.02_0.2']
    #df['ADX']=pdta.adx(df['High'],df['Low'],df['Close'],14)['ADX_14']
    #df['MINUS_DI']=pdta.adx(df['High'],df['Low'],df['Close'],14)['DMN_14']
    #df['PLUS_DI']=pdta.adx(df['High'],df['Low'],df['Close'],14)['DMP_14']
    #df['MA_200']=df['Close'].rolling(200).mean()
    #df['MA_50']=df['Close'].rolling(50).mean()
    #df['EMA_12']=pdta.ema(df['Close'],length=12)
    #df['EMA_26']=pdta.ema(df['Close'],length=26)
    #df['EMA_13']=pdta.ema(df['Close'],length=13)
    #df['EMA_5']=pdta.ema(df['Close'],length=5)
    #df['EMA_7']=pdta.ema(df['Close'],length=7)
    #df['MA_1']=df['Close'].rolling(1).mean()
    #df['MA_2']=df['Close'].rolling(2).mean()
    #df['MA_3']=df['Close'].rolling(3).mean()
    #df['MA_4']=df['Close'].rolling(4).mean()
    #df['MA_5']=df['Close'].rolling(5).mean()
    #df['MA_6']=df['Close'].rolling(6).mean()
    #df['MA_7']=df['Close'].rolling(7).mean()
    #df['MA_8']=df['Close'].rolling(8).mean()
    #df['MA_9']=df['Close'].rolling(9).mean()
    #df['MA_10']=df['Close'].rolling(10).mean()
    #df['MA_21']=pdta.ema(df['Close'],length=21)
    #df['WMA_20']=pdta.wma(df['Close'],length=20)
    #df['HMA_21']=pdta.hma(df['Close'],length=21)
    #df['HMA_55']=pdta.hma(df['Close'],length=55)
    #df['RSI_MA']=df['RSI'].rolling(14).mean()
    #df['EMA_High']=pdta.ema(df['High'],length=21)
    #df['EMA_Low']=pdta.ema(df['Low'],length=21)
    #df = df.round(decimals=2)
    df=get_trade_info(df)
    return df
  except Exception as e:
    logger.info(f"Error in calculate Indicator: {e}")
    return df

def getTokenInfo(symbol, exch_seg ='NFO',instrumenttype='OPTIDX',strike_price = 0,pe_ce = 'CE',expiry_day = None):
  try:
    token_df=st.session_state['opt_list']
    if exch_seg == 'NSE' or exch_seg == 'BSE': return token_df[(token_df['exch_seg'] == exch_seg) & (token_df['name'] == symbol)]
    elif (instrumenttype == 'FUTSTK') or (instrumenttype == 'FUTIDX'):
        return token_df[(token_df['instrumenttype'] == instrumenttype) & (token_df['name'] == symbol)].sort_values(by=['expiry'], ascending=True)
    elif (instrumenttype == 'OPTSTK' or instrumenttype == 'OPTIDX'):
        if pe_ce=="CE":
            return (token_df[(token_df['name'] == symbol) & (token_df['expiry']==expiry_day) &
                    (token_df['instrumenttype'] == instrumenttype) & (token_df['strike'] >= strike_price*100) &
                    (token_df['symbol'].str.endswith(pe_ce))].sort_values(by=['expiry']))
        else:
          return (token_df[(token_df['name'] == symbol) & (token_df['expiry']==expiry_day) &
                    (token_df['instrumenttype'] == instrumenttype) & (token_df['strike'] <= strike_price*100) &
                    (token_df['symbol'].str.endswith(pe_ce))].sort_values(by=['expiry']))
  except Exception as e:return None

def get_ce_pe_data(symbol,indexLtp="-"):
  indexLtp=float(indexLtp) if indexLtp!="-" else get_ltp_price(symbol)
  # ATM
  if symbol=='BANKNIFTY' or symbol=='^NSEBANK':
    symbol='BANKNIFTY'
    expiry_day=st.session_state['bnf_expiry_day']
    exch_seg="NFO"
    instrumenttype='OPTIDX'
  elif symbol=='NIFTY' or symbol=='^NSEI':
    symbol='NIFTY'
    expiry_day=st.session_state['nf_expiry_day']
    exch_seg="NFO"
    instrumenttype='OPTIDX'
  elif symbol=="SENSEX" or symbol=="^BSESN":
    symbol='SENSEX'
    expiry_day=st.session_state['sensex_expiry_day']
    exch_seg="BFO"
    instrumenttype='OPTIDX'
  else:
    expiry_day=st.session_state['monthly_expiry_day']
    exch_seg="NFO"
    instrumenttype='OPTSTK'
  #CE,#PE
  ce_strike_symbol = getTokenInfo(symbol,exch_seg,instrumenttype,indexLtp,'CE',expiry_day).iloc[0]
  pe_strike_symbol = getTokenInfo(symbol,exch_seg,instrumenttype,indexLtp,'PE',expiry_day).iloc[0]
  return indexLtp, ce_strike_symbol,pe_strike_symbol

def get_sl_tgt(ltp_price,indicator_strategy):
  try:
    sl_match=re.search(r'SL:(\d+)',indicator_strategy)
    #tgt_match=re.search(r'TGT:(\d+)',indicator_strategy)
    atr_match=re.search(r'ATR:(\d+)',indicator_strategy)

    sl_value=sl_match.group(1) if sl_match else None
    #tgt_value=tgt_match.group(1) if tgt_match else None
    atr_value=atr_match.group(1) if atr_match else None

    if sl_value!="-" and sl_value: stop_loss=int(sl_value)
    elif sl_value=="-" and atr_match==True and "IDX" in indicator_strategy:stop_loss=int(float(ltp_price)-(0.5*float(atr_value)))
    elif sl_match:stop_loss=int(sl_value)
    elif atr_match:stop_loss=int(float(ltp_price)-(1*float(atr_value)))
    else:stop_loss=int(float(ltp_price*0.7))
    target_price=int(ltp_price+ltp_price-stop_loss)
    return target_price,stop_loss
  except:
    target_price=int(float(ltp_price*1.5))
    stop_loss=int(float(ltp_price*0.7))
    return target_price,stop_loss

def buy_option(symbol,indicator_strategy="Manual Buy",interval="5m",index_sl="-"):
  try:
    option_token=symbol['token']; option_symbol=symbol['symbol']; exch_seg=symbol['exch_seg']; lotsize=int(symbol['lotsize'])
    ltp_price=round(float(get_ltp_price(symbol=option_symbol,token=option_token,exch_seg=exch_seg)),2)
    orderId=place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='BUY',ordertype='LIMIT',price=ltp_price,
                          variety='NORMAL',exch_seg=exch_seg,producttype='CARRYFORWARD',ordertag=indicator_strategy)
    if str(orderId)=='Order placement failed':
      telegram_bot_sendtext(f'Order Failed Buy: {option_symbol} Indicator {indicator_strategy}')
      return
    try:
      ltp_price=round(float(get_ltp_price(symbol=option_symbol,token=option_token,exch_seg=exch_seg)),2)
      target_price,stop_loss=get_sl_tgt(ltp_price,indicator_strategy)
      indicator_strategy=indicator_strategy+ " LTP:"+str(int(ltp_price))+"("+str(int(stop_loss))+":"+str(int(target_price))+")"
      buy_msg=(f'Buy: {option_symbol}\nLTP: {ltp_price}\n{indicator_strategy}\nTarget: {target_price} Stop Loss: {stop_loss}')
      telegram_bot_sendtext(buy_msg)
    except:
      ltp_price=0
    orderbook=obj.orderBook()['data']
    orderbook=pd.DataFrame(orderbook)
    orders= orderbook[(orderbook['orderid'] == orderId)]
    orders_status=orders.iloc[0]['orderstatus']
    if orders_status== 'complete':
      if st.session_state['target_order_type']=="Target":
        place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='SELL',ordertype='LIMIT',price=target_price,
                    variety='NORMAL',exch_seg=exch_seg,producttype='CARRYFORWARD',ordertag=str(orderId)+" Target order Placed")
      elif st.session_state['target_order_type']=='Stop_Loss':
        place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='SELL',ordertype='STOPLOSS_LIMIT',price=stop_loss,
                    variety='STOPLOSS',exch_seg=exch_seg,producttype='CARRYFORWARD',triggerprice=stop_loss,squareoff=stop_loss,
                    stoploss=stop_loss, ordertag=str(orderId)+" Stop Loss order Placed")
  except Exception as e:
    logger.info(f"Error in buy_option: {e}")

def exit_position(symboltoken,tradingsymbol,exch_seg,qty,ltp_price,sl,ordertag='',producttype='CARRYFORWARD'):
  try:
    cancel_all_order(tradingsymbol)
    place_order(token=symboltoken,symbol=tradingsymbol,qty=qty,buy_sell='SELL',ordertype='STOPLOSS_LIMIT',price=sl,
                variety='STOPLOSS',exch_seg=exch_seg,producttype=producttype,triggerprice=sl,squareoff=sl, stoploss=sl,ordertag=ordertag)
    logger.info(f"Exit Alert In Option: {tradingsymbol} LTP:{ltp_price} SL:{sl} Ordertag {ordertag}")
    #telegram_bot_sendtext(sell_msg)
  except Exception as e:
    logger.info(f"Error in exit_position: {e}")

def cancel_index_order(nf_5m_trade_end="-",bnf_5m_trade_end="-",sensex_5m_trade_end="-"):
  if nf_5m_trade_end!="-" or bnf_5m_trade_end!="-" or sensex_5m_trade_end!="-":
    orderbook,pending_orders=get_order_book()
    for i in range(0,len(pending_orders)):
      try:
        tradingsymbol=pending_orders.loc[i]['tradingsymbol']
        if ((tradingsymbol[-2:]=='CE' and tradingsymbol.startswith("NIFTY") and nf_5m_trade_end=="Sell") or
            (tradingsymbol[-2:]=='CE' and tradingsymbol.startswith("BANKNIFTY") and bnf_5m_trade_end=="Sell") or
            (tradingsymbol[-2:]=='CE' and tradingsymbol.startswith("SENSEX") and sensex_5m_trade_end=="Sell") or
            (tradingsymbol[-2:]=='PE' and tradingsymbol.startswith("NIFTY") and nf_5m_trade_end=="Buy") or
            (tradingsymbol[-2:]=='PE' and tradingsymbol.startswith("BANKNIFTY") and bnf_5m_trade_end=="Buy") or
            (tradingsymbol[-2:]=='PE' and tradingsymbol.startswith("SENSEX") and sensex_5m_trade_end=="Buy")):
            orderID=pending_orders.loc[i]['orderid']
            variety=pending_orders.loc[i]['variety']
            cancel_order(orderID,variety)
      except Exception as e:
        logger.info(f"error in cancel_index_order: {e}")
        pass

def close_options_position(position,nf_5m_trade_end="-",bnf_5m_trade_end="-",sensex_5m_trade_end="-"):
  cancel_index_order(nf_5m_trade_end,bnf_5m_trade_end,sensex_5m_trade_end)
  position,open_position=get_open_position()
  for i in range(0,len(position)):
    try:
      tradingsymbol=position.loc[i]['tradingsymbol']
      if ((tradingsymbol[-2:]=='CE' and tradingsymbol.startswith("NIFTY") and nf_5m_trade_end=="Sell") or
          (tradingsymbol[-2:]=='CE' and tradingsymbol.startswith("BANKNIFTY") and bnf_5m_trade_end=="Sell") or
          (tradingsymbol[-2:]=='CE' and tradingsymbol.startswith("SENSEX") and sensex_5m_trade_end=="Sell") or
          (tradingsymbol[-2:]=='PE' and tradingsymbol.startswith("NIFTY") and nf_5m_trade_end=="Buy") or
          (tradingsymbol[-2:]=='PE' and tradingsymbol.startswith("BANKNIFTY") and bnf_5m_trade_end=="Buy") or
          (tradingsymbol[-2:]=='PE' and tradingsymbol.startswith("SENSEX") and sensex_5m_trade_end=="Buy")):
          qty=position['netqty'][i]
          if int(qty)!=0:
            symboltoken=position.loc[i]['symboltoken']
            producttype=position['producttype'][i]
            exch_seg=position['exchange'][i]
            ltp_price=position['ltp'][i]
            exit_position(symboltoken,tradingsymbol,exch_seg,qty,ltp_price,ltp_price,ordertag='Indicator Exit LTP: '+str(ltp_price),producttype='CARRYFORWARD')
            time.sleep(1)
    except Exception as e:
      logger.info(f"Error in Close index trade: {e}")

def index_trade(symbol,interval):
  try:
    fut_data=get_historical_data(symbol=symbol,interval=interval,token="-",exch_seg="-",candle_type="NORMAL")
    if fut_data is None: return None
    trade=str(fut_data['Trade'].values[-1])
    if trade!="-":
      indicator_strategy=f"{fut_data['Indicator'].values[-1]} [{fut_data['Datetime'].values[-1]}]"
      indexLtp=fut_data['Close'].values[-1]
      indexLtp, ce_strike_symbol,pe_strike_symbol=get_ce_pe_data(symbol,indexLtp=indexLtp)
      if trade=="Buy" : buy_option(ce_strike_symbol,indicator_strategy,interval)
      elif trade=="Sell" : buy_option(pe_strike_symbol,indicator_strategy,interval)
    information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),
                'Symbol':symbol,
                'Datetime':str(fut_data['Datetime'].values[-1]),'Close':fut_data['Close'].values[-1],
                'Indicator':fut_data['Indicator'].values[-1],
                'Trade':fut_data['Trade'].values[-1],
                'Trade End':fut_data['Trade End'].values[-1],
                'Supertrend':fut_data['Supertrend'].values[-1],
                'Supertrend_10_2':fut_data['Supertrend_10_2'].values[-1],
                'RSI':fut_data['RSI'].values[-1],
                'VWAP':fut_data['VWAP'].values[-1]}
    st.session_state['options_trade_list'].append(information)
    st.session_state['index_trade_end'][symbol+"_"+interval] = trade
  except Exception as e:
    logger.info(f"error in index_trade: {e}")

def get_near_options(symbol,index_ltp,symbol_expiry):
  token_df=st.session_state['opt_list']
  ltp=index_ltp*100
  a=token_df[(token_df['name'] == symbol) & (token_df['expiry']==symbol_expiry) & (token_df['strike']<=ltp) &
            (token_df['symbol'].str.endswith('PE'))].sort_values(by=['strike'], ascending=False).head(2)
  a.reset_index(inplace=True)
  b=token_df[(token_df['name'] == symbol) & (token_df['expiry']==symbol_expiry) & (token_df['strike']>=ltp) &
            (token_df['symbol'].str.endswith('CE'))].sort_values(by=['strike'], ascending=True).head(2)
  b.reset_index(inplace=True)
  df=pd.concat([a,b])
  df.sort_index(inplace=True)
  return df

def all_near_options():
  df=pd.DataFrame()
  for symbol in index_list:
    try:
      index_ltp=get_ltp_price(symbol)
      if symbol=="NIFTY":symbol_expiry=st.session_state['nf_expiry_day']
      elif symbol=="BANKNIFTY":symbol_expiry=st.session_state['bnf_expiry_day']
      elif symbol=="SENSEX":symbol_expiry=st.session_state['sensex_expiry_day']
      else:symbol_expiry="-"
      option_list=get_near_options(symbol,index_ltp,symbol_expiry)
      df=pd.concat([df,option_list])
    except Exception as e:print(e)
  st.session_state['near_opt_df']=df
  near_opt_df.dataframe(df,hide_index=True)
  near_opt_updated.text(f"Near Option Updated : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")

def trade_near_options(time_frame):
  try:
    option_list=st.session_state['near_opt_df']
    for symbol in index_list:
      index_exit_trade=st.session_state['index_trade_end'].get(symbol+"_"+time_frame)
      if index_exit_trade is None or index_exit_trade=="-":
        for i in range(0,len(option_list)):
          try:
            symbol_name=option_list['symbol'].iloc[i]
            if symbol_name.startswith(symbol):
              token_symbol=option_list['token'].iloc[i]
              exch_seg=option_list['exch_seg'].iloc[i]
              opt_data=get_historical_data(symbol=symbol_name,interval=time_frame,token=token_symbol,exch_seg=exch_seg)
              information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),
                           'Symbol':symbol_name,
                           'Datetime':str(opt_data['Datetime'].values[-1]),'Close':opt_data['Close'].values[-1],
                           'Indicator':opt_data['Indicator'].values[-1],
                           'Trade':opt_data['Trade'].values[-1],
                           'Trade End':opt_data['Trade End'].values[-1],
                           'Supertrend':opt_data['Supertrend'].values[-1],
                           'Supertrend_10_2':opt_data['Supertrend_10_2'].values[-1],
                           'RSI':opt_data['RSI'].values[-1],
                           'VWAP':opt_data['VWAP'].values[-1]}
              st.session_state['options_trade_list'].append(information)
              st.session_state['index_trade_end'][symbol_name+"_"+time_frame] = opt_data['Trade'].values[-1]
              if opt_data['Trade'].values[-1]=="Buy":
                indicator=f"{opt_data['Indicator'].values[-1]} [{opt_data['Datetime'].values[-1]}]"
                strike_symbol=option_list.iloc[i]
                buy_option(symbol=strike_symbol,indicator_strategy=indicator,interval=time_frame,index_sl="-")
                break
          except:pass
  except Exception as e:logger.info(f"Trade Near Option Error {e}")

def closing_trade():
  try:
    pass
    #orderbook,pending_orders=get_order_book()
    #st.session_state['NIFTY_5m_Trade']="Buy"
    #st.session_state['BANKNIFTY_5m_Trade']="Buy"
    #st.session_state['SENSEX_5m_Trade']="Buy"
    #todays_trade=get_todays_trade(orderbook)
    #st.session_state['NIFTY_5m_Trade']="Sell"
    #st.session_state['BANKNIFTY_5m_Trade']="Sell"
    #st.session_state['SENSEX_5m_Trade']="Sell"
    #todays_trade=get_todays_trade(orderbook)
  except:pass

def trail_sl():
  orderbook,pending_orders=get_order_book()
  if pending_orders is not None:
    for i in range(0,len(pending_orders)):
      try:
        if pending_orders['status'].iloc[i] not in ['rejected','complete','cancelled']:
          if pending_orders['transactiontype'].iloc[i]=="SELL":
            order_price=pending_orders['price'].iloc[i]
            new_sl=order_price
            symbol=pending_orders['tradingsymbol'].iloc[i]
            token=pending_orders['symboltoken'].iloc[i]
            exch_seg=pending_orders['exchange'].iloc[i]
            ltp_price=get_ltp_price(symbol=symbol,token=token,exch_seg=exch_seg)
            if ltp_price>order_price:
              old_data=get_historical_data(symbol=symbol,interval="5m",token=token,exch_seg=exch_seg,candle_type="NORMAL")
              atr=ltp_price-(float(old_data['Atr'].iloc[-1])*2)
              st_10_2=float(old_data['Supertrend_10_2'].iloc[-1])
              st_7_3=float(old_data['Supertrend'].iloc[-1])
              st_10_1=float(old_data['Supertrend_10_1'].iloc[-1])
              if st_7_3 > new_sl and st_7_3 < ltp_price: new_sl=int(st_7_3)
              if st_10_2 > new_sl and st_10_2 < ltp_price: new_sl=int(st_10_2)
              if atr > new_sl and atr < ltp_price : new_sl=int(atr)
              transactiontype=pending_orders['transactiontype'].iloc[i]
              variety=pending_orders['variety'].iloc[i]
              orderid=pending_orders['orderid'].iloc[i]
              ordertype=pending_orders['ordertype'].iloc[i]
              producttype=pending_orders['producttype'].iloc[i]
              quantity=pending_orders['quantity'].iloc[i]
              modify_order(variety,orderid,ordertype,producttype,new_sl,quantity,symbol,token,exch_seg,new_sl,new_sl,new_sl)
      except Exception as e:
        logger.info(f"error in trail_sl: {e}")
        pass

def check_indicator_exit(buy_df,minute):
  for i in range(0,len(buy_df)):
      try:
        if buy_df['Status'].iloc[i]=="Pending" and buy_df['price'].iloc[i]!="-":
          symboltoken=buy_df['symboltoken'].iloc[i]
          tradingsymbol=buy_df['tradingsymbol'].iloc[i]
          exch_seg=buy_df['exchange'].iloc[i]
          indicator=buy_df['ordertag'].iloc[i]
          if minute%15==0 and "15m" in indicator: time_frame="15m"
          elif (minute%5==0 and "5m" in indicator) or "GTT" in indicator:time_frame="5m"
          elif "1m" in indicator or indicator=="Buy:Multi Time Frame ST":time_frame="1m"
          else:time_frame="5m"
          opt_data=get_historical_data(symbol=tradingsymbol,interval=time_frame,token=symboltoken,exch_seg=exch_seg,candle_type="NORMAL")
          st.session_state['index_trade_end'][tradingsymbol+"_"+time_frame] = opt_data['Trade'].values[-1]
      except Exception as e:
        print(e)

def check_login():
  pass

def sub_loop_code(now_minute):
  try:
    st.session_state['options_trade_list']=[]
    if (now_minute%5==0 and 'IDX:5M' in time_frame_interval):
      st.session_state['index_trade_end']={}
      for symbol in index_list:
        index_trade(symbol,"5m")
        log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
      if 'OPT:5M' in time_frame_interval:
        trade_near_options('5m')
        log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
      if 'STK:5M' in time_frame_interval:
        for symbol in st.session_state['fut_list']:
          index_trade(symbol+".NS","5m")
        log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
    if (now_minute%15==0 and 'IDX:15M' in time_frame_interval):
      for symbol in index_list:index_trade(symbol,"15m")
    if 'IDX:1M' in time_frame_interval:
      for symbol in index_list: index_trade(symbol,"1m")
    if 'OPT:1M' in time_frame_interval:
      trade_near_options('1m')
      log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
    #if (now_minute%5==0 and 'GTT:5M' in time_frame_interval):gtt_sub_loop()
  except Exception as e:
    logger.info(f"error in sub_loop_code: {e}")

def loop_code():
  now = datetime.datetime.now(tz=gettz('Asia/Kolkata'))
  marketopen = now.replace(hour=9, minute=20, second=0, microsecond=0)
  marketclose = now.replace(hour=20, minute=48, second=0, microsecond=0)
  int_marketclose = now.replace(hour=20, minute=51, second=0, microsecond=0)
  day_end = now.replace(hour=20, minute=30, second=0, microsecond=0)
  if algo_state==False:return
  all_near_options()
  while now < day_end:
    now=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
    next_loop=now.replace(second=0, microsecond=0)+ datetime.timedelta(minutes=1)
    st.session_state['last_check']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0).time()
    login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
    try:
      if now > marketopen and now < marketclose: sub_loop_code(now.minute)
      orderbook,pending_orders=get_order_book()
      position,open_position=get_open_position()
      all_near_options()
      index_ltp_string.text(f"Index Ltp: {print_ltp()}")
      if datetime.datetime.now(tz=gettz('Asia/Kolkata')) < next_loop:
        while datetime.datetime.now(tz=gettz('Asia/Kolkata')).second< 50:
          position,open_position=get_open_position()
          index_ltp_string.text(f"Index Ltp: {print_ltp()}")
          time.sleep(1)
        login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']} Next Check: {next_loop.time()}")
        time.sleep(1+(next_loop-datetime.datetime.now(tz=gettz('Asia/Kolkata'))).seconds)
    except Exception as e:
      logger.info(f"error in loop_code: {e}")
      now=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
      time.sleep(60-now.second+1)

def get_ltp_token(nfo_list,bfo_list):
  try:
    ltp_df=pd.DataFrame(obj.getMarketData(mode="LTP",exchangeTokens={ "BFO": list(bfo_list), "NFO": list(nfo_list),})['data']['fetched'])
    return ltp_df
  except Exception as e:
    ltp_df=pd.DataFrame(columns = ['exchange','tradingSymbol','symbolToken','ltp'])
    return ltp_df

def update_price_orderbook(df):
  for j in range(0,len(df)):
    try:
      if df['ordertag'].iloc[j]=="": df['ordertag'].iloc[j]="GTT Buy OPT 5m:Supertrend Trade"
      if df['averageprice'].iloc[j]!=0:df['price'].iloc[j]=df['averageprice'].iloc[j]
      elif df['price'].iloc[j]==0:
        text=df['text'].iloc[j]
        ordertag=df['ordertag'].iloc[j]+" "
        if 'You require Rs. ' in text and ' funds to execute this order.' in text and type(text)==str :
          abc='-'
          abc=(text.split('You require Rs. '))[1].split(' funds to execute this order.')[0]
          if abc!='-' and int(float(abc)) <= 50000:
            df['price'].iloc[j]=(round(float(abc)/float(df['quantity'].iloc[j]),2))
        if df['price'].iloc[j]==0 and "LTP: " in ordertag:
          abc='-'
          abc=(ordertag.split('LTP: '))[1].split(' ')[0]
          df['price'].iloc[j]=float(abc)
          #df['price'].iloc[j]=float(ordertag.split("LTP: ",1)[1])
        if df['price'].iloc[j]==0:df['price'].iloc[j]='-'
      if df['price'].iloc[j]=='-':
        df['price'].iloc[j]=get_ltp_price(symbol=df['tradingsymbol'].iloc[j],token=df['symboltoken'].iloc[j],exch_seg=df['exchange'].iloc[j])
    except Exception as e:
      pass
  return df

if algo_state:
  loop_code()
if nf_ce:
  indexLtp, ce_strike_symbol,pe_strike_symbol=get_ce_pe_data('NIFTY',indexLtp="-")
  buy_option(ce_strike_symbol,'Manual Buy','5m')
if nf_pe:
  indexLtp, ce_strike_symbol,pe_strike_symbol=get_ce_pe_data('NIFTY',indexLtp="-")
  buy_option(pe_strike_symbol,'Manual Buy','5m')
if bnf_ce:
  indexLtp, ce_strike_symbol,pe_strike_symbol=get_ce_pe_data('BANKNIFTY',indexLtp="-")
  buy_option(ce_strike_symbol,'Manual Buy','5m')
if bnf_pe:
  indexLtp, ce_strike_symbol,pe_strike_symbol=get_ce_pe_data('BANKNIFTY',indexLtp="-")
  buy_option(pe_strike_symbol,'Manual Buy','5m')
if restart:
  pass
login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
orderbook,pending_orders=get_order_book()
position,open_position=get_open_position()
all_near_options()
index_ltp_string.text(f"Index Ltp: {print_ltp()}")
if __name__ == "__main__":
  try:loop_code()
  except Exception as e:
    st.error(f"An error occurred: {e}")
    st.experimental_rerun()
