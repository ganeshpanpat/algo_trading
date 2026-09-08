import datetime, time, math, warnings, re, requests
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from dateutil.tz import gettz
from SmartApi import SmartConnect
from logzero import logger
import pyotp
import warnings
st.set_page_config(page_title="Algo App",layout="wide",initial_sidebar_state="expanded",)
st.markdown("""
  <style>
    .block-container {padding-top: 0rem;padding-bottom: 0rem;padding-left: 2rem;padding-right: 2rem;}
  </style>
  """, unsafe_allow_html=True)
st.text("Welcome To Algo Trading")
import socket
def get_local_ip():
    # Get the system's hostname
    hostname = socket.gethostname()
    # Resolve the hostname to an IP address
    local_ip = socket.gethostbyname(hostname)
    ip_address=st.empty()
    ip_address.text(f"Hostname: {hostname} Local IP Address: {local_ip}")

get_local_ip()

warnings.filterwarnings("ignore")
st.set_page_config(layout="wide")
if 'Logged_in' not in st.session_state:st.session_state['Logged_in']="Guest"
if 'login_time' not in st.session_state:st.session_state['login_time']="login_time"
if 'last_check' not in st.session_state:st.session_state['last_check']="last_check"
if 'market_status' not in st.session_state:st.session_state['market_status']="market_status"
if 'orderbook' not in st.session_state:st.session_state['orderbook']=[]
if 'opt_list' not in st.session_state:st.session_state['opt_list']=[]
if 'options_trade_list' not in st.session_state:st.session_state['options_trade_list']=[]
if 'TopGainers' not in st.session_state:st.session_state['TopGainers']=[]
if 'TopLoosers' not in st.session_state:st.session_state['TopLoosers']=[]
max_attempt=5
login_details=st.empty()
login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']} market_status:{st.session_state['market_status']}")
index_ltp_string=st.empty()
index_ltp_string.text(f"Index Ltp: ")
user='Ganesh'; username = 'G93179'; pwd = '1987'; apikey = 'UQLSkTLs'; token='U4EAZJ3L44CNJHNUZ56R22TPKI'
if "smartapi" not in st.session_state:
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
    st.session_state.smartapi = obj
obj = st.session_state.smartapi
login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
log_tb, order_tb, position_tb, open_odr_tb, setting_tb, token_tb,gainer_tb,looser_tb = st.tabs(["Log","Order Book", "Position",
                "Open Order", "Settings","Token List","Gainers","Loosers"])
with log_tb:
  col1,col2=st.columns([1,9])
  with col1:
    nf_ce=st.button(label="NF CE")
    bnf_ce=st.button(label="BSE CE")
    nf_pe=st.button(label="NF PE")
    bnf_pe=st.button(label="BSE PE")
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
  ind_col1,ind_col2=st.columns([5,1.5])
  indicator_list=['TEMA_EMA_9 Trade','MA_50_ST Trade','ST_7_3 Trade', 'ST_10_2 Trade','ST_10_1 Trade','RSI MA Trade','RSI_60 Trade','MACD Trade','PSAR Trade',
                  'DI Trade','MA Trade','EMA Trade','EMA_5_7 Trade','MA 21 Trade','HMA Trade','RSI_60 Trade','EMA_High_Low Trade',
                  'Two Candle Theory','Multi Time ST Trade','RSI_WMA_9 Trade','High Break Trade','Vwap ST_7_3 Trade']
  with ind_col1:
    index_list=st.multiselect('Select Index',['NIFTY','BANKNIFTY','SENSEX','FINNIFTY'],['NIFTY', 'SENSEX'])
    time_frame_interval = st.multiselect('Select Time Frame',['IDX:5M','IDX:15M','IDX:1M','OPT:5M','OPT:1M','GTT:5M','STK:5M'],['IDX:5M'])
    five_buy_indicator = st.multiselect('5M Indicator',indicator_list,['ST_7_3 Trade'])
    five_opt_buy_indicator = st.multiselect('5M OPT Indicator',indicator_list,['ST_7_3 Trade'])
    gtt_indicator=st.multiselect('GTT Indicator',['5M_ST','5M_ST_10_2','1M_10_1','1M_10_2'],['5M_ST','5M_ST_10_2'])
    one_buy_indicator = st.multiselect('1M Indicator',indicator_list,[])
    one_opt_buy_indicator = st.multiselect('1M OPT Indicator',indicator_list,[])
    fifteen_buy_indicator = st.multiselect('15M Indicator',indicator_list,['MA_50_ST Trade'])
    three_buy_indicator = st.multiselect('3M Indicator',indicator_list,[])
    with ind_col2:
      lots_to_trade=st.number_input(label="Lots To Trade",min_value=1, max_value=10, value=1, step=None)
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
with token_tb:
    token_df=st.empty()
    token_df=st.dataframe(st.session_state['opt_list'],hide_index=True)
with gainer_tb:
    gainer_df=st.empty()
with looser_tb:
    looser_df=st.empty()
def telegram_bot_sendtext(bot_message):
  BOT_TOKEN = '5051044776:AAHh6XjxhRT94iXkR4Eofp2PPHY3Omk2KtI'
  BOT_CHAT_ID = '-1001542241163'
  try:
    bot_message=st.session_state['Logged_in']+':\n'+bot_message
    send_text = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + BOT_CHAT_ID + \
                  '&parse_mode=HTML&text=' + bot_message
    response = requests.get(send_text)
  except Exception as e:
    pass

def get_token_df():
    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    d = requests.get(url).json()
    token_df = pd.DataFrame.from_dict(d)
    token_df['expiry'] = pd.to_datetime(token_df['expiry']).apply(lambda x: x.date())
    token_df = token_df.astype({'strike': float})
    token_df = token_df.sort_values(by=['name', 'strike'])
    idx_list = token_df[(token_df['token'] == '99926000') | (token_df['token'] == '99919000')]
    combined_list = pd.concat([idx_list])
    for index, row in combined_list.iterrows():
        symbol_name = row['name']
        nfo_expiry = token_df[
            (token_df['name'] == symbol_name) & ((token_df['exch_seg'] == 'NFO') | (token_df['exch_seg'] == 'BFO')) &
            (token_df['instrumenttype'] != 'FUTIDX') & (token_df['instrumenttype'] != 'FUTSTK')]['expiry'].min()
        combined_list.at[index, 'expiry'] =nfo_expiry
    token_df = token_df[((token_df['exch_seg'] == 'NFO') | (token_df['exch_seg'] == 'BFO'))]
    st.session_state['opt_list']=token_df
    st.session_state['stk_opt_list']=combined_list
    now_dt=datetime.datetime.now(tz=gettz('Asia/Kolkata')).date()-datetime.timedelta(days=0)
    nf_expiry_df = token_df[(token_df['name'] == 'NIFTY') & (token_df['instrumenttype'] == 'OPTIDX') & (token_df['expiry']>=now_dt)]
    st.session_state['nf_expiry_day'] = nf_expiry_df['expiry'].min()
    bnf_expiry_df = token_df[(token_df['name'] == 'BANKNIFTY') & (token_df['instrumenttype'] == 'OPTIDX') & (token_df['expiry']>=now_dt)]
    st.session_state['bnf_expiry_day'] = bnf_expiry_df['expiry'].min()
    bse_expiry_df = token_df[(token_df['name'] == 'SENSEX') & (token_df['instrumenttype'] == 'OPTIDX') & (token_df['expiry']>=now_dt)]
    st.session_state['bse_expiry_day'] = bse_expiry_df['expiry'].min()
  
if len(st.session_state['opt_list'])==0 :
   get_token_df()
   token_df=st.dataframe(st.session_state['opt_list'],hide_index=True)


# Order Book
def get_order_book():
  try:
    for attempt in range(max_attempt):
      try:
        orderbook=obj.orderBook()
        break
      except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt:
          return None,None
    if orderbook!=None:
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
    logger.info(f'Error in getting order book {e}')
    order_book_updated.text(f"Error in getting Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
    return None,None

def get_open_position():
  try:
    for attempt in range(max_attempt):
      try:
        position=obj.position()
        break
      except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt:
          return None,None
    if position!=None:
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

#Orders
def place_order(token,symbol,qty,buy_sell,ordertype='MARKET',price=0,variety='NORMAL',exch_seg='NFO',ordertag='-'):
  try:
    if variety=='NORMAL': triggerprice = squareoff = stoploss = 0
    else: triggerprice = squareoff = stoploss = price * 1.02
    orderparams =  {"variety":variety, "tradingsymbol": symbol,"symboltoken": str(token), "transactiontype": buy_sell,
            "exchange": exch_seg, "ordertype": ordertype,"producttype": "CARRYFORWARD", "duration": "DAY","price": str(price),
            "squareoff": str(squareoff),"stoploss": str(stoploss), "quantity": str(qty),"triggerprice":str(triggerprice),"ordertag":ordertag}
    orderId=obj.placeOrder(orderparams)
    return orderId
  except Exception as e:
    logger.info(f"error in place_order Order placement failed: {e}")
    orderId='Order placement failed'
    telegram_bot_sendtext(f'{buy_sell} Order placement failed : {symbol}')
    return orderId
def modify_order(variety,orderid,ordertype,producttype,price,quantity,tradingsymbol,symboltoken,exchange,
                 triggerprice=0,squareoff=0,stoploss=0):
  try:
    modifyparams = {"variety": variety,"orderid": orderid,
                    "ordertype": ordertype,"producttype": producttype,
                    "duration": "DAY","price": price,
                    "quantity": quantity,"tradingsymbol":tradingsymbol,
                    "symboltoken":symboltoken,"exchange":exchange,
                    "squareoff":squareoff,"stoploss": stoploss,"triggerprice":triggerprice}
    for attempt in range(max_attempt):
      try:
        obj.modifyOrder(modifyparams)
        break
      except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt: break
  except Exception as e:
    logger.info(f"error in modify_order: {e}")
def cancel_order(orderID,variety):
  for attempt in range(max_attempt):
    try:
      obj.cancelOrder(orderID,variety=variety)
      break
    except Exception as e:
      logger.info(f"Attempt {attempt} failed: {e}")
      time.sleep(2)
      if attempt == max_attempt: break
def cancel_all_order(symbol):
  try:
    orderbook,pending_orders=get_order_book()
    if orderbook is not None:
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

#Ltp
def get_yf_ltp(symbol="-",token="-",exch_seg='-'):
  try:
    data=yf.Ticker(symbol).history(interval='1m',period='3d')
    return round(float(data['Close'].iloc[-1]),2)
  except Exception as e:
    logger.info(f"error in get_yf_ltp: {e}")
    return "Unable to get LTP"
def get_angel_ltp(symbol="-",token="-",exch_seg='-'):
  for attempt in range(max_attempt):
    try:
      try:
        market_data = obj.getMarketData("LTP", {"exch_seg": [token]})
        return market_data['data']['fetched'][0]['ltp']
      except Exception as e:
        try:
          ltp_data = obj.ltpData(exch_seg, symbol, token)
          return ltp_data['data']['ltp']
        except Exception as e: return "Unable to get LTP"
      break
    except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt:
          break

def get_ltp_price(symbol="-",token="-",exch_seg='-'):
  try:
    symbol_i="-";ltp="Unable to get LTP"
    if symbol=="BANKNIFTY" or symbol=="^NSEBANK": symbol_i="^NSEBANK";token='99926009';exch_seg='NSE'
    elif symbol=="NIFTY" or symbol=="^NSEI": symbol_i="^NSEI";token='99926000';exch_seg='NSE'
    elif symbol=="SENSEX" or symbol=="^BSESN": symbol_i="^BSESN";token='99919000';exch_seg='BSE'
    if symbol in ['TCS','RELIANCE','HDFCBANK','SAIL','SBIN','TRENT']:symbol_i=symbol + ".NS"
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
    index_ltp_string.text(f"Index Ltp: {print_sting}")
    return print_sting
  except Exception as e:
    logger.info(f"error in print_ltp: {e}")
    return None

#Historical Data
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
    df['Symbol']=symbol
    df=df.round(2)
    if isinstance(df, str) or (isinstance(df, pd.DataFrame)==True and len(df)==0):
      logger.info(f"Yahoo Data Not Found {symbol}")
      return "No data found, symbol may be delisted"
    return df
  except Exception as e:
    logger.info(f"error in yfna_data {symbol}: {e}")
    return None
def angel_data(symbol,token,interval,exch_seg,period=5):
  try:
    to_date= datetime.datetime.now(tz=gettz('Asia/Kolkata'))
    from_date = to_date - datetime.timedelta(days=period)
    fromdate = from_date.strftime("%Y-%m-%d %H:%M")
    todate = to_date.strftime("%Y-%m-%d %H:%M")
    historicParam={"exchange": exch_seg,"symboltoken": token,"interval": interval,"fromdate": fromdate, "todate": todate}
    for attempt in range(1,max_attempt):
      try:
        res_json=obj.getCandleData(historicParam)
        break
      except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt: break
    if res_json== None: return None
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
    df['Symbol']=symbol
    return df
  except Exception as e:
    logger.info(f"error in angel_data : token {token} {e}")
    return None
def get_historical_data(symbol="-",interval='5m',token="-",exch_seg="-",candle_type="NORMAL"):
  try:
    symbol_i="-";df=None
    if (symbol=="^NSEI" or symbol=="NIFTY") : symbol_i,token,exch_seg="^NSEI",99926000,"NSE"
    elif (symbol=="^NSEBANK" or symbol=="BANKNIFTY") : symbol_i,token,exch_seg="^NSEBANK",99926009,"NSE"
    elif (symbol=="^BSESN" or symbol=="SENSEX") : symbol_i,token,exch_seg="^BSESN",99919000,"BSE"
    if symbol in ['TCS','RELIANCE','HDFCBANK','SAIL','SBIN','TRENT']:symbol_i=symbol + ".NS"
    if (interval=="5m" or interval=='FIVE_MINUTE'): period,delta_time,agl_interval,yf_interval=5,5,"FIVE_MINUTE","5m"
    elif (interval=="1m" or interval=='ONE_MINUTE') : period,delta_time,agl_interval,yf_interval=1,1,"ONE_MINUTE","1m"
    elif (interval=="15m" or interval=='FIFTEEN_MINUTE'): period,delta_time,agl_interval,yf_interval=5,15,"FIFTEEN_MINUTE","15m"
    elif (interval=="60m" or interval=='ONE_HOUR'): period,delta_time,agl_interval,yf_interval=30,60,"ONE_HOUR","60m"
    elif (interval=="1d" or interval=='ONE_DAY') : period,delta_time,agl_interval,yf_interval=100,5,"ONE_DAY","1d"
    else:period,delta_time,agl_interval,yf_interval=5,1,"ONE_MINUTE","1m"
    if  symbol[-3:]=='.NS':symbol_i=symbol
    df=angel_data(symbol,token,agl_interval,exch_seg,period)
    #if df is None:df=yfna_data(symbol_i,"5m","5") 
    now=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None)
    last_candle=now.replace(second=0, microsecond=0)- datetime.timedelta(minutes=delta_time)
    df = df[(df.index <= last_candle)]
    df['Time Frame']=yf_interval
    df['Time']=now.time()
    df.index.names = ['']
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()
    df = df.reset_index(drop=True)
    df=df[['Time','Date','Symbol','Datetime','Open','High','Low','Close','Volume','VWAP','Time Frame']]
    df=calculate_indicator(df)
    df=df.round(2)
    return df
  except Exception as e:
    logger.info(f"error in get_historical_data: {e}")
    return None
def native_supertrend(df: pd.DataFrame, period: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
    col_name = f"Supertrend_{int(period)}_{int(multiplier)}"
    # 1. Structural True Range computation
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift(1)).abs()
    lc = (df["Low"] - df["Close"].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)

    # 2. Modern exponential smoothing calculation
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()

    # 3. Handle base bands
    hl2 = (df["High"] + df["Low"]) / 2
    basic_ub = hl2 + (multiplier * atr)
    basic_lb = hl2 - (multiplier * atr)

    # Extract arrays to navigate around Python 3.14 structural loop bottlenecks
    close_arr = df["Close"].to_numpy()
    bub_arr = basic_ub.to_numpy()
    blb_arr = basic_lb.to_numpy()

    final_ub = np.zeros(len(df))
    final_lb = np.zeros(len(df))
    st_line = np.zeros(len(df))
    direction = np.ones(len(df))

    # Initialize seeds
    final_ub[0], final_lb[0] = bub_arr[0], blb_arr[0]

    # 4. Process band corrections
    for i in range(1, len(df)):
        final_ub[i] = (
            bub_arr[i]
            if bub_arr[i] < final_ub[i - 1] or close_arr[i - 1] > final_ub[i - 1]
            else final_ub[i - 1]
        )
        final_lb[i] = (
            blb_arr[i]
            if blb_arr[i] > final_lb[i - 1] or close_arr[i - 1] < final_lb[i - 1]
            else final_lb[i - 1]
        )

        if direction[i - 1] == 1:
            if close_arr[i] < final_lb[i]:
                direction[i], st_line[i] = -1, final_ub[i]
            else:
                direction[i], st_line[i] = 1, final_lb[i]
        else:
            if close_arr[i] > final_ub[i]:
                direction[i], st_line[i] = 1, final_lb[i]
            else:
                direction[i], st_line[i] = -1, final_ub[i]

    df[col_name] = st_line
    return df
def native_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculates Wilder's RSI using native pandas math."""
    col_name = f"RSI_{float(period)}"

    # 1. Calculate price changes
    delta = df["Close"].diff()

    # 2. Separate gains and losses
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # 3. Use Exponential Moving Average (EMA) for Wilder's smoothing
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    # 4. Calculate Relative Strength (RS) and RSI
    # Adding a tiny float (1e-10) prevents an error if avg_loss is 0
    rs = avg_gain / (avg_loss + 1e-10)
    df[col_name] = 100 - (100 / (1 + rs))

    return df
def native_moving_average(df: pd.DataFrame, period: int = 20, ma_type: str = "SMA") -> pd.DataFrame:
    """Calculates Simple (SMA) or Exponential (EMA) Moving Average."""
    col_name = f"{ma_type.upper()}_{float(period)}"
    if ma_type.upper() == "EMA":
        # Calculates Exponential Moving Average
        df[col_name] = df["Close"].ewm(span=period, adjust=False).mean()
    else:
        # Defaults to Simple Moving Average
        df[col_name] = df["Close"].rolling(window=period).mean()
    return df
def calculate_indicator(df):
  try:
    df = native_supertrend(df, period=7, multiplier=3.0)
    df = native_supertrend(df, period=10, multiplier=2.0)
    df = native_supertrend(df, period=10, multiplier=1.0)
    df = native_rsi(df, period=14)
    df = native_moving_average(df, period=50,ma_type="SMA")
    df = df.round(decimals=2)
    df=get_trade_info(df)
    return df
  except Exception as e:
    logger.info(f"Error in calculate Indicator: {e}")
    return df
def get_trade_info(df):
  trade_columns = ['Trade','Indicator','Trade End','ST_7_3 Trade','ST_10_2 Trade','ST_10_1 Trade']
  for col in trade_columns:df[col] = '-'
  try:
    if len(df) >= 2:
      i = len(df) - 1
      prev = df.iloc[i-1]
      curr = df.iloc[i]
      close_prev = prev['Close']
      close_curr = curr['Close']
      # ---- Supertrend 7_3 ----
      if close_prev <= prev['Supertrend_7_3'] and close_curr > curr['Supertrend_7_3']: df.loc[i, 'ST_7_3 Trade'] = "Buy"
      elif close_prev >= prev['Supertrend_7_3'] and close_curr < curr['Supertrend_7_3']: df.loc[i, 'ST_7_3 Trade'] = "Sell"
      # ---- Supertrend 10_2 ----
      if close_prev <= prev['Supertrend_10_2'] and close_curr > curr['Supertrend_10_2']: df.loc[i, 'ST_10_2 Trade'] = "Buy"
      elif close_prev >= prev['Supertrend_10_2'] and close_curr < curr['Supertrend_10_2']: df.loc[i, 'ST_10_2 Trade'] = "Sell"
      # ---- Supertrend 10_1 ----
      if close_prev <= prev['Supertrend_10_1'] and close_curr > curr['Supertrend_10_1']: df.loc[i, 'ST_10_1 Trade'] = "Buy"
      elif close_prev >= prev['Supertrend_10_1'] and close_curr < curr['Supertrend_10_1']: df.loc[i, 'ST_10_1 Trade'] = "Sell"

      # ---- Final Trade ----
      for indicator_trade in ['ST_7_3 Trade','ST_10_2 Trade','ST_10_1 Trade']:
        trade_val = df.loc[i, indicator_trade]
        if trade_val in ("Buy", "Sell"):
          df.loc[i, 'Trade'] = trade_val
          df.loc[i, 'Trade End'] = trade_val
          df.loc[i, 'Indicator'] = indicator_trade
          break
  except Exception as e: logger.error(e)
  return df

#Trade
def getTokenInfo(idx_symbol,strike_price=0,ce_pe="CE",expiry="-"):
  token_df=st.session_state['opt_list']
  if strike_price==0 or expiry=="-": return None
  filter_df=token_df[((token_df['name'] == idx_symbol) & 
                    ((token_df['exch_seg'] == 'NFO') | (token_df['exch_seg'] == 'BFO')) &
                    (token_df['expiry'] == expiry) & token_df['symbol'].str.endswith(ce_pe))]
  if ce_pe == "CE":
    filter_df= filter_df[(filter_df['strike'] >= strike_price*100)].sort_values(by=['strike'], ascending=True)
  else:
    filter_df= filter_df[(filter_df['strike'] <= strike_price*100)].sort_values(by=['strike'], ascending=False)
  return filter_df.iloc[0]
def index_trade(idx_symbol,interval="5m",token="-",exch_seg="NSE",expiry="-"):
  try:
    fut_data=get_historical_data(symbol=idx_symbol,interval=interval,token=token,exch_seg=exch_seg,candle_type="NORMAL")
    if fut_data is None: return None
    trade=str(fut_data['Trade'].values[-1])
    if trade!="-":
      indicator_strategy=f"{fut_data['Indicator'].values[-1]}"
      indexLtp=fut_data['Close'].values[-1]
      if expiry=="-":
        if idx_symbol=="NIFTY": expiry=st.session_state['nf_expiry_day']
        elif idx_symbol=="SENSEX": expiry=st.session_state['bse_expiry_day']
      if trade=="Buy":ce_pe="CE"
      else:ce_pe="PE"
      strike_symbol=getTokenInfo(idx_symbol=idx_symbol,strike_price=indexLtp,ce_pe=ce_pe,expiry=expiry)
      buy_option(strike_symbol['token'],strike_symbol['symbol'],
                     strike_symbol['exch_seg'],str(int(strike_symbol['lotsize'])),str(0),
                     indicator_strategy=indicator_strategy)
    information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),
                'Symbol':fut_data['Symbol'].values[-1],
                'Datetime':str(fut_data['Datetime'].values[-1]),'Close':fut_data['Close'].values[-1],
                'Indicator':fut_data['Indicator'].values[-1],
                'Trade':trade,
                'Trade End':fut_data['Trade End'].values[-1],
                'Supertrend':fut_data['Supertrend_7_3'].values[-1],
                'Supertrend_10_2':fut_data['Supertrend_10_2'].values[-1],
                'Supertrend_10_1':fut_data['Supertrend_10_1'].values[-1],
                'RSI':fut_data['RSI_14.0'].values[-1],
                'VWAP':fut_data['VWAP'].values[-1]}
    st.session_state['options_trade_list'].append(information)
    log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
  except Exception as e:
    logger.info(f"error in index_trade: {e}")
def buy_option(option_token,option_symbol,exch_seg,lotsize,ltp_price,indicator_strategy="Manual Buy"):
  try:
    if option_symbol.startswith('NIFTY') or option_symbol.startswith('BANKNIFTY') or option_symbol.startswith('SENSEX'):
      ordertype='MARKET';price=0
    else:
      ordertype='LIMIT'
      price=float(get_ltp_price(symbol=option_symbol,token=option_token,exch_seg=exch_seg))
    orderId=place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell="BUY",
                        ordertype=ordertype,price=price,variety='NORMAL',
                        exch_seg=exch_seg,ordertag=indicator_strategy)
    if str(orderId)=='Order placement failed':
      telegram_bot_sendtext(f'Order Failed Buy: {option_symbol} Indicator {indicator_strategy}')
      return
    try:
      ltp_price=round(float(get_ltp_price(symbol=option_symbol,token=option_token,exch_seg=exch_seg)),2)
      stop_loss=int(ltp_price*0.7)
      target_price=int(ltp_price*1.5)
    except:
      ltp_price=0
    for attempt in range(1,max_attempt):
      try:
        orderbook=obj.orderBook()['data']
        break
      except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt: break
        return
    orderbook=pd.DataFrame(orderbook)
    orders= orderbook[(orderbook['orderid'] == orderId)]
    if orders.empty:return
    orders_status=orders.iloc[0]['orderstatus']
    if orders_status== 'complete':
     place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='SELL',ordertype='STOPLOSS_LIMIT',price=stop_loss,
                    variety='STOPLOSS',exch_seg=exch_seg,producttype='CARRYFORWARD',triggerprice=stop_loss,squareoff=stop_loss,
                    stoploss=stop_loss, ordertag=str(orderId)+" Stop Loss order Placed")
  except Exception as e:
    logger.info(f"Error in buy_option: {e}")
    telegram_bot_sendtext(f"Error in buy_option: {e}")

def get_top_gainer():
  for attempt in range(max_attempt):
    try:
      gainerdata=pd.DataFrame(obj.gainersLosers(params = {"datatype": "PercPriceGainers","expirytype": "NEAR"})['data']).sort_values(by='percentChange')
      gainer_df.dataframe(gainerdata,hide_index=True)
      break
    except Exception as e:
        logger.info(f"Attempt {attempt} failed: {e}")
        time.sleep(2)
        if attempt == max_attempt: break

def get_top_looser():
  for attempt in range(max_attempt):
    try:
      looserdata=pd.DataFrame(obj.gainersLosers(params = {"datatype": "PercPriceLoosers","expirytype": "NEAR"})['data']).sort_values(by='percentChange')
      looser_df.dataframe(looserdata,hide_index=True)
      break
    except Exception as e:
      logger.info(f"Attempt {attempt} failed: {e}")
      time.sleep(2)
      if attempt == max_attempt: break

def update_gainer_looser():
  get_top_gainer()
  get_top_looser()
      
  
def update_app_info():
    get_order_book()
    get_open_position()
    print_ltp()
    log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)

#Loop
def sub_loop_code(now_time):
  if (now_time.minute%5==0 and "IDX:5M" in time_frame_interval):
        st.session_state['options_trade_list']=[]
        index_trade(idx_symbol="NIFTY",interval="5m",token="-",exch_seg="NSE",expiry="-")
        index_trade(idx_symbol="SENSEX",interval="5m",token="-",exch_seg="BSE",expiry="-")

def loop_code():
    if algo_state:
      now = datetime.datetime.now(tz=gettz('Asia/Kolkata'))
      marketclose = now.replace(hour=20, minute=50, second=0, microsecond=0)
      marketopen = now.replace(hour=9, minute=15, second=0, microsecond=0)
      st.session_state['market_status']="Open"
      st.session_state['last_check']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0).time()
      login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']} Market Status:{st.session_state['market_status']}")
      while algo_state:
        now = datetime.datetime.now(tz=gettz('Asia/Kolkata'))
        if now < marketclose and now > marketopen :
          try:
            now = datetime.datetime.now(tz=gettz('Asia/Kolkata'))
            sub_loop_code(now)
          except Exception as e:
            logger.error(f"An error occurred: {e}")
        else:
          st.session_state['market_status']="Closed"
        update_app_info()
        logger.info(now.replace(microsecond=0).time())
        st.session_state['last_check']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0).time()
        login_details.text(f"Welcome:{st.session_state['Logged_in']} Last Check:{st.session_state['last_check']} Market Status:{st.session_state['market_status']}")
        time.sleep(60-datetime.datetime.now().second+1)
#update_gainer_looser()
update_app_info()
if __name__ == "__main__":
  try:
    loop_code()
  except Exception as e:
    st.error(f"An error occurred: {e}")
    st.experimental_rerun()
