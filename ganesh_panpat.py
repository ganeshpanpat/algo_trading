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
    .block-container {padding-top: 3rem;padding-bottom: 0rem;padding-left: 2rem;padding-right: 2rem;}
  </style>
  """, unsafe_allow_html=True)
st.text("Welcome To Algo Trading")
if 'Logged_in' not in st.session_state:st.session_state['Logged_in']="Guest"
if 'login_time' not in st.session_state:st.session_state['login_time']="login_time"
if 'last_check' not in st.session_state:st.session_state['last_check']="last_check"
if 'fut_list' not in st.session_state:st.session_state['fut_list']=['TCS','SBIN','RELIANCE','SAIL','TRENT','HDFCBANK']
if 'options_trade_list' not in st.session_state:st.session_state['options_trade_list']=[]
if 'orderbook' not in st.session_state:st.session_state['orderbook']=[]
if 'opt_list' not in st.session_state:st.session_state['opt_list']=[]
if 'stk_opt_list' not in st.session_state:st.session_state['stk_opt_list']=[]
if 'near_opt_df' not in st.session_state:st.session_state['near_opt_df']=[]

login_details=st.empty()
login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
index_ltp_string=st.empty()
index_ltp_string.text(f"Index Ltp: ")

log_tb, order_tb, position_tb, open_odr_tb, setting_tb, token_tb, stk_token_tb, near_opt_tb= st.tabs(["Log","Order Book", "Position",
                "Open Order", "Settings","Token List","Stock List",'Near Options'])
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
  ind_col1,ind_col2=st.columns([5,1.5])
  indicator_list=['TEMA_EMA_9 Trade','MA_50_ST Trade','ST_7_3 Trade', 'ST_10_2 Trade','ST_10_1 BB Trade','ST_10_1 Trade','RSI MA Trade','RSI_60 Trade','MACD Trade','PSAR Trade',
                  'DI Trade','MA Trade','EMA Trade','EMA_5_7 Trade','MA 21 Trade','HMA Trade','RSI_60 Trade','EMA_High_Low Trade',
                  'Two Candle Theory','Multi Time ST Trade','RSI_WMA_9 Trade','High Break Trade','Vwap ST_7_3 Trade']
  with ind_col1:
    index_list=st.multiselect('Select Index',['NIFTY','BANKNIFTY','SENSEX','FINNIFTY'],['NIFTY', 'SENSEX', 'BANKNIFTY'])
    fut_list=st.multiselect('Select Future',['TCS','SBIN','RELIANCE','SAIL','TRENT','HDFCBANK'],['TCS','SBIN','RELIANCE','SAIL','TRENT','HDFCBANK'])
    time_frame_interval = st.multiselect('Select Time Frame',['IDX:5M','IDX:15M','IDX:1M','OPT:5M','OPT:1M','GTT:5M','STK:5M'],['IDX:5M','OPT:5M','STK:5M'])
    five_buy_indicator = st.multiselect('5M Indicator',indicator_list,['ST_7_3 Trade'])
    five_opt_buy_indicator = st.multiselect('5M OPT Indicator',indicator_list,['ST_10_1 BB Trade'])
    five_stk_buy_indicator = st.multiselect('5M STK Indicator',indicator_list,[])
    gtt_indicator=st.multiselect('GTT Indicator',['5M_ST','5M_ST_10_2','1M_10_1','1M_10_2'],['5M_ST','5M_ST_10_2'])
    one_buy_indicator = st.multiselect('1M Indicator',indicator_list,[])
    one_opt_buy_indicator = st.multiselect('1M OPT Indicator',indicator_list,[])
    fifteen_buy_indicator = st.multiselect('15M Indicator',indicator_list,[])
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

with stk_token_tb:
    stk_token_df=st.empty()
    stk_token_df=st.dataframe(st.session_state['stk_opt_list'],hide_index=True)

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

def get_token_df():
    url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
    d = requests.get(url).json()
    token_df = pd.DataFrame.from_dict(d)
    token_df['expiry'] = pd.to_datetime(token_df['expiry']).apply(lambda x: x.date())
    token_df = token_df.astype({'strike': float})
    token_df = token_df.sort_values(by=['name', 'strike'])
    st_list=token_df[token_df['name'].isin(fut_list)]
    st_list = st_list[((st_list['exch_seg'] == 'NSE') | (st_list['exch_seg'] == 'BSE')) & (st_list['symbol'].str.endswith('-EQ'))]
    idx_list = token_df[(token_df['token'] == '99926000') | (token_df['token'] == '99919000')]
    combined_list = pd.concat([idx_list, st_list])
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
  
if len(st.session_state['opt_list'])==0 :get_token_df()
token_df.dataframe(st.session_state['opt_list'],hide_index=True)
user='Ganesh'; username = 'G93179'; pwd = '4789'; apikey = 'Rz6IiOsd'; token='U4EAZJ3L44CNJHNUZ56R22TPKI'
user='Kalyani'; username = 'K205244'; pwd = '4789'; apikey = 'lzC7yJmt'; token='YDV6CJI6BEU3GWON7GZTZNU3RM'
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
  login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")


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
    logger.info(f'Error in getting order book {e}')
    order_book_updated.text(f"Error in getting Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)}")
    return None,None
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
def place_order(token,symbol,qty,buy_sell,ordertype='MARKET',price=0,variety='NORMAL',exch_seg='NFO',
                producttype='CARRYFORWARD',triggerprice=0,squareoff=0,stoploss=0,ordertag='-'):
  try:
    orderparams = {"variety": variety,"tradingsymbol": symbol,
                   "symboltoken": token,"transactiontype": buy_sell,
                   "exchange": exch_seg,"ordertype": ordertype,
                   "producttype": producttype,"duration": "DAY",
                   "price": (float(price)),"squareoff":(float(squareoff)),
                   "stoploss": (float(stoploss)),"quantity": str(qty),
                   "triggerprice":(float(triggerprice)),"ordertag":ordertag,"trailingStopLoss":5}

    orderparams =  {"variety": "NORMAL", "tradingsymbol": symbol,
            "symboltoken": str(token), "transactiontype": buy_sell,
            "exchange": exch_seg, "ordertype": ordertype,
            "producttype": "CARRYFORWARD", "duration": "DAY",
            "price": str(price), "squareoff": str(squareoff),
            "stoploss": str(stoploss), "quantity": str(qty),"triggerprice":str(triggerprice)}
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
def buy_option(option_token,option_symbol,exch_seg,lotsize,ltp_price,indicator_strategy="Manual Buy"):
  try:
    if len(indicator_strategy) > 50: indicator_strategy= indicator_strategy[:50]
    else: indicator_strategy= indicator_strategy
    if option_symbol.startswith('NIFTY') or option_symbol.startswith('BANKNIFTY') or option_symbol.startswith('SENSEX'):
      orderId=place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='BUY',ordertype='MARKET',price=str(0),
                          variety='NORMAL',exch_seg=exch_seg,producttype='CARRYFORWARD',ordertag=indicator_strategy)
    else:
      ltp_price=float(get_ltp_price(symbol=option_symbol,token=option_token,exch_seg=exch_seg))
      orderId=place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='BUY',ordertype='LIMIT',price=str(ltp_price),
                          variety='NORMAL',exch_seg=exch_seg,producttype='CARRYFORWARD',ordertag=indicator_strategy)
    if str(orderId)=='Order placement failed':
      telegram_bot_sendtext(f'Order Failed Buy: {option_symbol} Indicator {indicator_strategy}')
      return
    try:
      ltp_price=round(float(get_ltp_price(symbol=option_symbol,token=option_token,exch_seg=exch_seg)),2)
      #target_price,stop_loss=get_sl_tgt(ltp_price,indicator_strategy)
      stop_loss=int(ltp_price*0.7)
      target_price=int(ltp_price*1.5)
      indicator_strategy=indicator_strategy+ " LTP:"+str(int(ltp_price))+"("+str(int(stop_loss))+":"+str(int(target_price))+")"
      buy_msg=(f'Buy: {option_symbol}\nLTP: {ltp_price}\n{indicator_strategy}\nTarget: {target_price} Stop Loss: {stop_loss}')
    except:
      ltp_price=0
    orderbook=obj.orderBook()['data']
    orderbook=pd.DataFrame(orderbook)
    orders= orderbook[(orderbook['orderid'] == orderId)]
    orders_status=orders.iloc[0]['orderstatus']
    telegram_bot_sendtext(buy_msg+"\nOrder Status:" + orders_status)
    if orders_status== 'complete':
     place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='SELL',ordertype='STOPLOSS_LIMIT',price=stop_loss,
                    variety='STOPLOSS',exch_seg=exch_seg,producttype='CARRYFORWARD',triggerprice=stop_loss,squareoff=stop_loss,
                    stoploss=stop_loss, ordertag=str(orderId)+" Stop Loss order Placed")
  except Exception as e:
    logger.info(f"Error in buy_option: {e}")
    telegram_bot_sendtext(f"Error in buy_option: {e}")
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
    #if (symbol_i[0]=="^") or symbol_i[-3:]=='.NS':
    #  df=yfna_data(symbol_i,yf_interval,period)
    #else:
    df=angel_data(token,agl_interval,exch_seg,period)
    now=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None)
    #if now - df.index[-1] > datetime.timedelta(minutes=5):df=angel_data(token,agl_interval,exch_seg,period)
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
                     'TEMA_EMA_9 Trade','RSI_WMA_9 Trade','High Break Trade','Vwap ST_7_3 Trade','MA_50_ST Trade','MA_50 Trade','ST_10_1 BB Trade']
    
    for col in trade_columns:df[col] = '-'
    time_frame = df['Time Frame'][0]
    Symbol = df['Symbol'][0]
    if Symbol in ["^NSEBANK", "BANKNIFTY", "^NSEI", "NIFTY", "SENSEX", "^BSESN"] : symbol_type = "IDX"
    elif Symbol in fut_list: symbol_type="STK"
    else: symbol_type= "OPT"
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
    elif symbol_type=="STK": indicator_list=five_buy_indicator
    else:indicator_list = ['ST_7_3 Trade', 'ST_10_2 Trade']
      
    df['Indicator'] = symbol_type
    df['Trade'] = "-"
    df['Trade End'] = "-"
    sl="-"
    # Ensure that the DataFrame has at least two rows to perform the check
    if len(df) >= 2:
      i = len(df) - 1  # Get the index of the last row
      try:           
        if df.iloc[i-1]['Close'] <= df.iloc[i-1]['Supertrend'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend']:
          df.loc[i, 'ST_7_3 Trade'] = "Buy"
        elif df.iloc[i-1]['Close'] >= df.iloc[i-1]['Supertrend'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend']:
          df.loc[i, 'ST_7_3 Trade'] = "Sell"

        if df.iloc[i]['MACD'] > df.iloc[i]['MACD signal'] and df.iloc[i-1]['MACD'] < df.iloc[i-1]['MACD signal']:
          df.loc[i, 'MACD Trade'] = "Buy"
        elif df.iloc[i]['MACD'] < df.iloc[i]['MACD signal'] and df.iloc[i-1]['MACD'] > df.iloc[i-1]['MACD signal']:
          df.loc[i, 'MACD Trade'] = "Sell"

        if df.iloc[i-1]['Close'] < df.iloc[i-1]['Supertrend_10_2'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend_10_2']:
          df.loc[i, 'ST_10_2 Trade'] = "Buy"
        elif df.iloc[i-1]['Close'] > df.iloc[i-1]['Supertrend_10_2'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend_10_2']:
          df.loc[i, 'ST_10_2 Trade'] = "Sell"

        if df.iloc[i-1]['Close'] < df.iloc[i-1]['Supertrend_10_1'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend_10_1']:
          df.loc[i, 'ST_10_1 Trade'] = "Buy"
        elif df.iloc[i-1]['Close'] > df.iloc[i-1]['Supertrend_10_1'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend_10_1']:
          df.loc[i, 'ST_10_1 Trade'] = "Sell"

        if df.iloc[i-1]['Close'] < df.iloc[i-1]['Supertrend_10_1'] and df.iloc[i]['Close'] > df.iloc[i]['Supertrend_10_1'] and df.iloc[i]['Close'] > df.iloc[i]['MBB']:
          df.loc[i, 'ST_10_1 BB Trade'] = "Buy"
        elif df.iloc[i-1]['Close'] > df.iloc[i-1]['Supertrend_10_1'] and df.iloc[i]['Close'] < df.iloc[i]['Supertrend_10_1'] and df.iloc[i]['Close'] < df.iloc[i]['MBB']:
          df.loc[i, 'ST_10_1 BB Trade'] = "Sell"

        if df.iloc[i-1]['Tema_9'] < df.iloc[i-1]['EMA_9'] and df.iloc[i]['Tema_9'] > df.iloc[i]['EMA_9'] and float(df.iloc[i]['RSI']) >= 55:
          df.loc[i, 'TEMA_EMA_9 Trade'] = "Buy"
        elif df.iloc[i-1]['Tema_9'] > df.iloc[i-1]['EMA_9'] and df.iloc[i]['Tema_9'] < df.iloc[i]['EMA_9']:
          df.loc[i, 'TEMA_EMA_9 Trade'] = "Sell"

        if int(df.iloc[i]['RSI']) >= 60 and int(df.iloc[i-1]['RSI']) < 60:df.loc[i, 'RSI_60 Trade'] = "Buy"
        if int(df.iloc[i]['RSI_9']) >=  int(df.iloc[i]['WMA_RSI_9']) and int(df.iloc[i-1]['RSI_9']) <=  int(df.iloc[i-1]['WMA_RSI_9']) :df.loc[i, 'RSI_WMA_9 Trade'] = "Buy"

        if df['Close'][i] > df['Close'][i-1] and df['Close'][i] > df['Close'][i-2] and df['Close'][i] > df['Close'][i-3] and df['Close'][i] > df['Close'][i-4] and df['Close'][i] > df['Close'][i-5]:
          df['High Break Trade'][i] = "Buy"

        if df.iloc[i-1]['Close'] <= df.iloc[i-1]['MA_50'] and df.iloc[i]['Close'] > df.iloc[i]['MA_50']:
          df.loc[i, 'MA_50 Trade'] = "Buy"
        elif df.iloc[i-1]['Close'] >= df.iloc[i-1]['MA_50'] and df.iloc[i]['Close'] < df.iloc[i]['MA_50']:
          df.loc[i, 'MA_50 Trade'] = "Sell"

        if df.loc[i, 'MA_50 Trade'] == "Buy" and df.loc[i, 'ST_7_3 Trade'] == "Buy":
          df.loc[i, 'MA_50_ST Trade'] = "Buy"
        elif df.loc[i, 'MA_50 Trade'] == "Sell" and df.loc[i, 'ST_7_3 Trade'] == "Sell":
          df.loc[i, 'MA_50_ST Trade'] = "Sell"
    
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
    df['UBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBU_20_2.0']
    df['MBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBM_20_2.0']
    df['LBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBL_20_2.0']
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
def getTokenInfo(idx_symbol,strike_price=0,ce_pe="CE",expiry="-"):
  token_df=st.session_state['opt_list']
  if strike_price==0 or expiry=="-": return None
  filter_df=token_df[((token_df['name'] == idx_symbol) & 
                    ((token_df['exch_seg'] == 'NFO') | (token_df['exch_seg'] == 'BFO')) &
                    (token_df['expiry'] == expiry) & token_df['symbol'].str.endswith(ce_pe))]
  if ce_pe == "CE": filter_df= filter_df[(filter_df['strike'] >= strike_price*100)].sort_values(by=['strike'], ascending=True)
  else: filter_df= filter_df[(filter_df['strike'] <= strike_price*100)].sort_values(by=['strike'], ascending=False)
  return filter_df.iloc[0]
def get_near_options():
  symbol_list=['NIFTY','SENSEX','BANKNIFTY']
  df = pd.DataFrame()
  token_df=st.session_state['opt_list']
  for symbol in symbol_list:
    try:
        indexLtp=get_ltp_price(symbol)
        ltp=indexLtp*100
        if symbol=="BANKNIFTY": expiry_day=st.session_state['bnf_expiry_day']
        elif symbol=="NIFTY": expiry_day=st.session_state['nf_expiry_day']
        elif symbol=="SENSEX": expiry_day=st.session_state['bse_expiry_day']
        a = (token_df[(token_df['name'] == symbol) & (token_df['expiry']==expiry_day) & (token_df['strike']>=ltp) &
                        (token_df['symbol'].str.endswith('CE'))].sort_values(by=['strike']).head(2)).sort_values(by=['strike'], ascending=True)
        a.reset_index(inplace=True)
        a['Serial'] = a['index'] + 1
        a.drop(columns=['index'], inplace=True)
        b=(token_df[(token_df['name'] == symbol) & (token_df['expiry']==expiry_day) & (token_df['strike']<=ltp) &
                        (token_df['symbol'].str.endswith('PE'))].sort_values(by=['strike']).tail(2)).sort_values(by=['strike'], ascending=False)
        b.reset_index(inplace=True)
        b['Serial'] = b['index'] + 1
        b.drop(columns=['index'], inplace=True)
        df=pd.concat([df, a,b])
    except Exception as e:
      print(f"Error in get_near_options {e}")
  df.sort_index(inplace=True)
  st.session_state['near_opt_df']=df
  near_opt_df.dataframe(st.session_state['near_opt_df'],hide_index=True)
  return df

def trade_near_options(time_frame):
  time_frame=str(time_frame)+"m"
  near_option_list=get_near_options()
  for symbol in ['NIFTY','SENSEX','BANKNIFTY']:
    for i in range(0,len(near_option_list)):
      if near_option_list['name'].iloc[i]== symbol:
        try:
            df=get_historical_data(symbol=near_option_list['symbol'].iloc[i],
                                  interval=time_frame,
                                  token=near_option_list['token'].iloc[i],
                                  exch_seg=near_option_list['exch_seg'].iloc[i])
            information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),
                    'Symbol':near_option_list['symbol'].iloc[i],
                    'Datetime':str(df['Datetime'].values[-1]),'Close':df['Close'].values[-1],
                    'Indicator':df['Indicator'].values[-1],
                    'Trade':df['Trade'].values[-1],
                    'Trade End':df['Trade End'].values[-1],
                    'Supertrend':df['Supertrend'].values[-1],
                    'Supertrend_10_2':df['Supertrend_10_2'].values[-1],
                    'RSI':df['RSI'].values[-1],
                    'VWAP':df['VWAP'].values[-1]}
            st.session_state['options_trade_list'].append(information)
            if df['Trade'].values[-1]=="Buy":
              buy_option(near_option_list['token'].iloc[i],near_option_list['symbol'].iloc[i],near_option_list['exch_seg'].iloc[i],
                    str(int(near_option_list['lotsize'].iloc[i])),str(0),indicator_strategy=df['Indicator'].values[-1])
              log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
              break
            log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
            time.sleep(1)
        except Exception as e:
          print(f" Error in trade_near_options {e}")
def index_trade(idx_symbol,interval="5m",token="-",exch_seg="NSE",expiry="-"):
  try:
    fut_data=get_historical_data(symbol=idx_symbol,interval=interval,token=token,exch_seg=exch_seg,candle_type="NORMAL")
    if fut_data is None: return None
    trade=str(fut_data['Trade'].values[-1])
    if trade!="-":
      indicator_strategy=f"{fut_data['Indicator'].values[-1]}"
      indexLtp=fut_data['Close'].values[-1]
      if trade=="Buy":ce_pe="CE"
      else:ce_pe="PE"
      strike_symbol=getTokenInfo(idx_symbol=idx_symbol,strike_price=indexLtp,ce_pe=ce_pe,expiry=expiry)
      buy_option(strike_symbol['token'],strike_symbol['symbol'],strike_symbol['exch_seg'],
                  str(int(strike_symbol['lotsize'])),str(0),indicator_strategy=indicator_strategy)
    information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),
                'Symbol':idx_symbol,
                'Datetime':str(fut_data['Datetime'].values[-1]),'Close':fut_data['Close'].values[-1],
                'Indicator':fut_data['Indicator'].values[-1],
                'Trade':trade,
                'Trade End':fut_data['Trade End'].values[-1],
                'Supertrend':fut_data['Supertrend'].values[-1],
                'Supertrend_10_2':fut_data['Supertrend_10_2'].values[-1],
                'RSI':fut_data['RSI'].values[-1],
                'VWAP':fut_data['VWAP'].values[-1]}
    st.session_state['options_trade_list'].append(information)
    log_holder.dataframe(st.session_state['options_trade_list'],hide_index=True)
  except Exception as e:
    logger.info(f"error in index_trade: {e}")
def sub_loop_code(now_time):
  if now_time.minute%5==0 : st.session_state['options_trade_list']=[]
  if (now_time.minute%5==0 and "IDX:5M" in time_frame_interval):
    if 'BANKNIFTY' in index_list: index_trade(idx_symbol="BANKNIFTY",interval="5m",token="-",exch_seg="NSE",expiry="-")
    if 'NIFTY' in index_list:index_trade(idx_symbol="NIFTY",interval="5m",token="-",exch_seg="NSE",expiry="-")
    if 'SENSEX' in index_list:index_trade(idx_symbol="SENSEX",interval="5m",token="-",exch_seg="BSE",expiry="-")
  if (now_time.minute%15==0 and "IDX:15M" in time_frame_interval):
    if 'BANKNIFTY' in index_list: index_trade(idx_symbol="BANKNIFTY",interval="15m",token="-",exch_seg="NSE",expiry="-")
    if 'NIFTY' in index_list:index_trade(idx_symbol="NIFTY",interval="15m",token="-",exch_seg="NSE",expiry="-")
    if 'SENSEX' in index_list:index_trade(idx_symbol="SENSEX",interval="15m",token="-",exch_seg="BSE",expiry="-")
  if (now_time.minute%5==0 and "OPT:5M" in time_frame_interval): trade_near_options(5)
def loop_code():
  if algo_state:
      now = datetime.datetime.now(tz=gettz('Asia/Kolkata'))
      marketclose = now.replace(hour=14, minute=55, second=0, microsecond=0)
      marketopen = now.replace(hour=0, minute=5, second=0, microsecond=0)
      while now < marketclose and  now  > marketopen:
        try:
          now_time=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
          sub_loop_code(now_time)
          get_order_book()
          get_open_position()
          print_ltp()
        except: pass
        st.session_state['last_check']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0).time()
        login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
        time.sleep(60-datetime.datetime.now().second)
        now_time=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
if nf_ce:
  idx_symbol="NIFTY"
  indexLtp=get_ltp_price(idx_symbol)
  expiry=st.session_state['nf_expiry_day']
  strike_symbol=getTokenInfo(idx_symbol=idx_symbol,strike_price=indexLtp,ce_pe="CE",expiry=expiry)
  buy_option(strike_symbol['token'],strike_symbol['symbol'],strike_symbol['exch_seg'],
                  str(int(strike_symbol['lotsize'])),str(0),indicator_strategy="Manual Buy")
if bnf_ce:
  idx_symbol="BANKNIFTY"
  indexLtp=get_ltp_price(idx_symbol)
  expiry=st.session_state['bnf_expiry_day']
  strike_symbol=getTokenInfo(idx_symbol=idx_symbol,strike_price=indexLtp,ce_pe="CE",expiry=expiry)
  buy_option(strike_symbol['token'],strike_symbol['symbol'],strike_symbol['exch_seg'],
                  str(int(strike_symbol['lotsize'])),str(0),indicator_strategy="Manual Buy")
if nf_pe:
  idx_symbol="NIFTY"
  indexLtp=get_ltp_price(idx_symbol)
  expiry=st.session_state['nf_expiry_day']
  strike_symbol=getTokenInfo(idx_symbol=idx_symbol,strike_price=indexLtp,ce_pe="PE",expiry=expiry)
  buy_option(strike_symbol['token'],strike_symbol['symbol'],strike_symbol['exch_seg'],
                  str(int(strike_symbol['lotsize'])),str(0),indicator_strategy="Manual Buy")
if bnf_pe:
  idx_symbol="BANKNIFTY"
  indexLtp=get_ltp_price(idx_symbol)
  expiry=st.session_state['bnf_expiry_day']
  strike_symbol=getTokenInfo(idx_symbol=idx_symbol,strike_price=indexLtp,ce_pe="PE",expiry=expiry)
  buy_option(strike_symbol['token'],strike_symbol['symbol'],strike_symbol['exch_seg'],
                  str(int(strike_symbol['lotsize'])),str(0),indicator_strategy="Manual Buy")
st.session_state['options_trade_list']=[]
get_order_book()
get_open_position()
print_ltp()
if __name__ == "__main__":
  try:
    loop_code()
  except Exception as e:
    st.error(f"An error occurred: {e}")
    st.experimental_rerun()
