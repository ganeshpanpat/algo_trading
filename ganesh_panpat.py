from SmartApi import SmartConnect
from SmartApi import SmartWebSocket
import threading; import pandas as pd
import pandas_ta as pdta
import json
import requests
import datetime
from dateutil.tz import gettz
import time
import math
import numpy
import warnings
import yfinance as yf
import sys
import pyotp
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import datetime
from dateutil.tz import gettz
import time
import pandas as pd
import yfinance as yf
import math
import re
from logzero import logger

NoneType = type(None)
pd.set_option('mode.chained_assignment', None)
st.set_page_config(page_title="Algo App",layout="wide",initial_sidebar_state="expanded",)
st.markdown("""
  <style>
    .block-container {padding-top: 0.5rem;padding-bottom: 0rem;padding-left: 2rem;padding-right: 5rem;}  
  </style>
  """, unsafe_allow_html=True)
user="Ganesh"
#cnt=st_autorefresh(interval=60*1000,debounce=False,key="Ganesh_refresh")
if 'algo_running' not in st.session_state:st.session_state['algo_running']="Not Running"
if 'algo_last_run' not in st.session_state:st.session_state['algo_last_run']=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
st.session_state['1m_bnf']="-"
st.session_state['1m_nf']="-"
st.session_state['5m_bnf']="-"
st.session_state['5m_nf']="-"
st.session_state['3m_bnf']="-"
st.session_state['3m_nf']="-"
st.session_state['15m_bnf']="-"
st.session_state['15m_nf']="-"
st.session_state['Nifty']="-"
st.session_state['BankNifty']="-"
st.session_state['Nifty_Trade_End']="-"
st.session_state['BankNifty_Trade_End']="-"
if 'options_trade_list' not in st.session_state: st.session_state['options_trade_list']=[]
if 'Near_option_list' not in st.session_state: st.session_state['Near_option_list']=[]
username=st.secrets["username"]
pwd=st.secrets["pwd"]
apikey=st.secrets["apikey"]
token=st.secrets["token"]
if 'user_name' not in st.session_state:
    obj=SmartConnect(api_key=apikey)
    obj.generateSession(username,pwd,pyotp.TOTP(token).now())
    st.write('Login Sucess')
    feedToken=obj.getfeedToken()
    userProfile= obj.getProfile(obj.refresh_token)
    aa= userProfile.get('data')
    st.session_state['user_name']=aa.get('name')
    st.session_state['login_time']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()
    st.session_state['access_token']=obj.access_token
    st.session_state['refresh_token']=obj.refresh_token
    st.session_state['feed_token']=obj.feed_token
    st.session_state['userId']=obj.userId
    st.session_state['api_key']=apikey
obj=SmartConnect(api_key=st.session_state['api_key'],access_token=st.session_state['access_token'],
                 refresh_token=st.session_state['refresh_token'],feed_token=st.session_state['feed_token'],userId=st.session_state['userId'])
st.header(f"Welcome {st.session_state['user_name']}")
last_login=st.empty()
last_login.text(f"Login: {st.session_state['login_time']} Algo: Not Running")
placeholder = st.empty()
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
  tab0, tab1, tab2, tab3, tab4, tab5= st.tabs(["Log","Order_Book", "Position","Algo Trade", "Settings","Near Options"])
  with tab0:log_holder=st.empty()
  with tab1:
    order_book_updated=st.empty()
    order_book_updated.text(f"Orderbook : ")
    order_datatable=st.empty()
  with tab2:position_datatable=st.empty()
  with tab3:
    algo_trade_updated=st.empty()
    algo_trade_updated.text(f"Algo Trade : ")
    algo_datatable=st.empty()
  with tab5:near_option=st.empty()
  with tab4:
    ind_col1,ind_col2,ind_col3,ind_col4=st.columns([5.5,1.5,1.5,1.5])
    indicator_list=['St Trade', 'ST_10_2 Trade', 'RSI MA Trade', 'RSI_60 Trade']
    with ind_col1:
      five_buy_indicator = st.multiselect('Five Minute Indicator',indicator_list,['St Trade', 'ST_10_2 Trade', 'RSI MA Trade', 'RSI_60 Trade'])
      option_buy_indicator = st.multiselect('Option Indicator',indicator_list,['St Trade', 'ST_10_2 Trade'])
      time_frame = st.multiselect('Select Time Frame',['IDX:5M', 'IDX:15M', 'OPT:5M', 'OPT:15M','IDX:1M'],['IDX:5M', 'OPT:5M'])
      three_buy_indicator = st.multiselect('Three Minute Indicator',indicator_list,[])
      one_buy_indicator = st.multiselect('One Minute Indicator',indicator_list,[])
    with ind_col2:
      banknifty_target=st.number_input(label="Bank Nifty Target",min_value=10, max_value=100, value=10, step=None)
      nifty_target=st.number_input(label="Nifty Target",min_value=5, max_value=100, value=5, step=None)
      target_order_type = st.selectbox('Target Order',('Target', 'Stop_Loss', 'NA'),1)
    with ind_col3:
      banknifty_sl=st.number_input(label="Bank Nifty SL",min_value=10, max_value=100, value=10, step=None)
      nifty_sl=st.number_input(label="Nifty SL",min_value=5, max_value=100, value=5, step=None)
      lots_to_trade=st.number_input(label="Lots To Trade",min_value=1, max_value=10, value=1, step=None)
    with ind_col4:
      target_type = st.selectbox('Target Type',('Points', 'Per Cent'),0)
      start_time=st.time_input('Algo Start', datetime.time(9, 20))
      intraday_close=st.time_input('Intraday Close', datetime.time(14, 45))
      algo_stop=st.time_input('Algo Stop', datetime.time(15, 30))
      expiry_days_bnf=st.empty()
      expiry_days_nf=st.empty()

def split_opt_name(options_contract):
  pattern = re.compile(r'([A-Za-z]+)(\d{2}[A-Za-z]+\d{2})(\d+)([CEP]+)')
  match = pattern.match(options_contract)
  if match:
    symboltoken = match.group(1)
    expiry_date = match.group(2)
    strike_price = match.group(3)
    option_type = match.group(4)
    expiry=datetime.datetime.strptime(expiry_date,"%d%b%y").date()
    return symboltoken,expiry_date,strike_price,option_type,expiry
  else:
    return "-","-","-","-","-"

def get_expiry_day(symbol):
  try:
    dt=obj.searchScrip("NFO",symbol)['data']
    token_list=pd.DataFrame.from_dict(dt)
    token_list=token_list[token_list.tradingsymbol.str.endswith('E')]
    token_list['name']="-"
    token_list['expiry']="-"
    token_list['strike']="-"
    token_list['option_type']="-"
    token_list['expiry_day']="-"
    for i in range(0,len(token_list)):
      symboltoken,expiry_date,strike_price,option_type,expiry=split_opt_name(token_list['tradingsymbol'].iloc[i])
      token_list['name'].iloc[i]=symboltoken
      token_list['expiry'].iloc[i]=expiry_date
      token_list['strike'].iloc[i]=strike_price
      token_list['option_type'].iloc[i]=option_type
      token_list['expiry_day'].iloc[i]=expiry
    expiry_day = token_list['expiry_day'].min()
    token_list=token_list[token_list['expiry_day']==expiry_day]
    return token_list['expiry'].iloc[0]
  except Exception as e:
    logger.exception(f"Unable to find expiry date: {e}")
    return "Unable to find expiry date"

if 'bnf_expiry_day' not in st.session_state:
  bnf_expiry_day=get_expiry_day("BANKNIFTY")
  st.session_state['bnf_expiry_day']=bnf_expiry_day
  nf_expiry_day=get_expiry_day("NIFTY")
  st.session_state['nf_expiry_day']=nf_expiry_day
  
def print_ltp():
  try:
    data=pd.DataFrame(obj.getMarketData(mode="OHLC",exchangeTokens={ "NSE": ["99926000","99926009"], "NFO": []})['data']['fetched'])
    data['change']=data['ltp']-data['close']
    print_sting=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()
    for i in range(0,len(data)):
      if data.iloc[i]['tradingSymbol']=="Nifty 50" and int(data.iloc[i]['ltp'])>1:st.session_state['Nifty']=int(data.iloc[i]['ltp'])
      if data.iloc[i]['tradingSymbol']=="Nifty Bank" and int(data.iloc[i]['ltp'])>1:st.session_state['BankNifty']=int(data.iloc[i]['ltp'])
      sym=data.iloc[i]['tradingSymbol']
      sym_ltp=int(data.iloc[i]['ltp'])
      sym_change=int(data.iloc[i]['change'])
      if sym_change>0:
        print_sting=f"{print_sting} {sym} {sym_ltp}({sym_change}↑)"
      else:
        print_sting=f"{print_sting} {sym} {sym_ltp}({sym_change}↓)"
      print_sting=print_sting.replace("Nifty 50","Nifty")
      print_sting=print_sting.replace("Nifty Bank","BankNifty")
      trade_end_msg=f"Trade End: BNF: {st.session_state['BankNifty_Trade_End']}, NF: {st.session_state['Nifty_Trade_End']}"
      placeholder.text(f'{print_sting} BNF Exp: {st.session_state["bnf_expiry_day"]} NF Exp: {st.session_state["nf_expiry_day"]} {trade_end_msg}')
  except Exception as e:
    logger.exception(f"Unable to print_ltp: {e}")
    pass
print_ltp()

def update_price_orderbook(df):
  for j in range(0,len(df)):
    try:
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
    except Exception as e:
      logger.exception(f"Unable to update_price_orderbook: {e}")
      pass
  return df

def update_order_book():
  try:
    orderbook=obj.orderBook()['data']
    if orderbook==None:
      order_datatable.write("No Order Placed")
      order_book_updated.text(f"Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()}")
      orderbook=pd.DataFrame(columns =['updatetime','orderid','transactiontype','status','symboltoken','tradingsymbol','price','quantity','ordertag'])
    else:
      orderbook=pd.DataFrame(orderbook)
      orderbook=orderbook.sort_values(by = ['updatetime'], ascending = [False], na_position = 'first')
      orderbook=update_price_orderbook(orderbook)
      orderbook['price']=round(orderbook['price'].astype(int),2)
      orderbook['updatetime'] = pd.to_datetime(orderbook['updatetime']).dt.time
      #orderbook['LTP']=''
      #orderbook=update_ltp_buy_df(orderbook)
      order_book_updated.text(f"Orderbook : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()}")
      #order_datatable.table(orderbook[['updatetime','orderid','transactiontype','status','tradingsymbol','price','quantity','ordertag']])
      order_datatable.dataframe(orderbook[['updatetime','orderid','transactiontype','status','tradingsymbol','price','quantity','ordertag']],hide_index=True)
      orderbook=orderbook[['updatetime','orderid','producttype','transactiontype','status','symboltoken','tradingsymbol','price','quantity','ordertag']]
    return orderbook
  except Exception as e:
    logger.exception(f"Unable to update_order_book: {e}")
    pass

def update_position():
  try:
    position=obj.position()['data']
    if position== None:position_datatable.write("No Position")
    else:
     position=pd.DataFrame(position)
     position_datatable.dataframe(position[['tradingsymbol','netqty','buyavgprice','sellavgprice','realised','unrealised','ltp']],hide_index=True)
  except Exception as e:
    logger.exception(f"Unable to update_position: {e}")
    pass

def telegram_bot_sendtext(bot_message):
  BOT_TOKEN = '5051044776:AAHh6XjxhRT94iXkR4Eofp2PPHY3Omk2KtI'
  BOT_CHAT_ID = '-1001542241163'
  bot_message=st.session_state['user_name']+':\n'+bot_message
  send_text = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + BOT_CHAT_ID + \
                '&parse_mode=HTML&text=' + bot_message
  response = requests.get(send_text)

def get_ltp_price(symbol="-",token="-",exch_seg='-'):
  try:
    return obj.getMarketData("LTP",{exch_seg:[token]})['data']['fetched'][0]['ltp']
  except:
    try:
      ltpInfo = obj.ltpData(exch_seg,symbol,token)
      return ltpInfo['data']['ltp']
    except Exception as e:
      logger.exception(f"Unable to get_ltp_price: {e}")
      return "Unable to get LTP"

def get_index_ltp(symbol):
  symbol_i="^NSEI"
  if symbol=="BANKNIFTY" or symbol=="^NSEBANK" or symbol[:4]=="BANK":
    symbol="BANKNIFTY"
    symbol_i="^NSEBANK"
    token=99926000
    exch_seg="NSE"
  elif symbol=="NIFTY" or symbol=="^NSEI" or symbol[:4]=='NIFT':
    symbol="NIFTY"
    symbol_i="^NSEI"
    token=99926009
    exch_seg="NSE"
  try:
    data=yf.Ticker(symbol_i).history(interval='1m',period='1d')
    indexLtp=round(float(data['Close'].iloc[-1]),2)
    #indexLtp=int(yf.Ticker(symbol_i).fast_info['last_price'])
  except Exception as e:
    try:
      data=yf.Ticker(symbol_i).history(interval='1m',period='1d')
      indexLtp=int(data['Close'].iloc[-1])
    except Exception as e:
       try:
          ltpInfo = obj.ltpData('NSE',symbol,token)
          indexLtp = ltpInfo['data']['ltp']
       except Exception as e:
         logger.exception(f"Unable to get_index_ltp: {e}")
  return indexLtp

def place_order(token,symbol,qty,buy_sell,ordertype='MARKET',price=0,variety='NORMAL',exch_seg='NFO',producttype='CARRYFORWARD',
                triggerprice=0,squareoff=0,stoploss=0,ordertag='-'):
  for i in range(0,3):
    try:
      orderparams = {"variety": variety,"tradingsymbol": symbol,"symboltoken": token,"transactiontype": buy_sell,"exchange": exch_seg,
        "ordertype": ordertype,"producttype": producttype,"duration": "DAY","price": int(float(price)),"squareoff":int(float(squareoff)),
        "stoploss": int(float(stoploss)),"quantity": str(qty),"triggerprice":int(float(triggerprice)),"ordertag":ordertag,"trailingStopLoss":5}
      orderId=obj.placeOrder(orderparams)
      print(orderId,orderparams)
      LTP_Price=round(float(get_ltp_price(symbol=symbol,token=token,exch_seg=exch_seg)),2)
      return orderId,LTP_Price
    except Exception as e:
      logger.exception(f"Order placement failed: {e}")
      orderId='Order placement failed'
      LTP_Price='Order placement failed'
  return orderId,LTP_Price

def modify_order(variety,orderid,ordertype,producttype,price,quantity,tradingsymbol,symboltoken,exchange,triggerprice=0,squareoff=0,stoploss=0):
  modifyparams = {"variety": variety,"orderid": orderid,"ordertype": ordertype,"producttype": producttype,
                  "duration": "DAY","price": price,"quantity": quantity,"tradingsymbol":tradingsymbol,
                  "symboltoken":symboltoken,"exchange":exchange,"squareoff":squareoff,"stoploss": stoploss,"triggerprice":triggerprice}
  obj.modifyOrder(modifyparams)
  print('Order modify')

def cancel_order(orderID,variety):
  obj.cancelOrder(orderID,variety=variety)
  print('order cancelled',orderID)

def cancel_all_order(symbol):
  orderbook,pending_orders=get_order_book()
  try:
    if isinstance(orderbook,NoneType)!=True:
      orderlist = orderbook[(orderbook['tradingsymbol'] == symbol) &
                            ((orderbook['orderstatus'] != 'complete') & (orderbook['orderstatus'] != 'cancelled') &
                              (orderbook['orderstatus'] != 'rejected') & (orderbook['orderstatus'] != 'AMO CANCELLED'))]
      orderlist_a = orderbook[(orderbook['tradingsymbol'] == symbol) & (orderbook['variety'] == 'ROBO') &
                              (orderbook['transactiontype'] == 'BUY') & (orderbook['orderstatus'] == 'complete')]
      orderlist=orderlist.append(orderlist_a)
      for i in range(0,len(orderlist)):
        cancel_order(orderlist.iloc[i]['orderid'],orderlist.iloc[i]['variety'])
  except Exception as e:
    print("Error cancel_all_order",e)

def cancel_options_all_order(bnf_signal='-',nf_signal='-'):
  orderbook,pending_orders=get_order_book()
  orderlist = orderbook[((orderbook['orderstatus'] != 'complete') & (orderbook['orderstatus'] != 'cancelled') &
                      (orderbook['orderstatus'] != 'rejected') & (orderbook['orderstatus'] != 'AMO CANCELLED'))]
  orderlist_a = orderbook[(orderbook['variety'] == 'ROBO') & (orderbook['transactiontype'] == 'BUY') & (orderbook['orderstatus'] == 'complete')]
  orderlist=orderlist.append(orderlist_a)
  orderlist=orderlist[['orderid','updatetime','symboltoken','tradingsymbol','exchange','price','variety','quantity','status']]
  for i in range(0,len(orderlist)):
    try:
      tradingsymbol=orderlist['tradingsymbol'].iloc[i]
      if ((bnf_signal=='Sell' and tradingsymbol[-2:]=='CE' and tradingsymbol[:4]=='BANK') or
        (bnf_signal=='Buy' and tradingsymbol[-2:]=='PE' and tradingsymbol[:4]=='BANK') or
        (nf_signal=='Sell' and tradingsymbol[-2:]=='CE' and tradingsymbol[:5]=='NIFTY') or
        (nf_signal=='Buy' and tradingsymbol[-2:]=='PE' and tradingsymbol[:5]=='NIFTY')):
        cancel_order(orderlist['orderid'].iloc[i],orderlist['variety'].iloc[i])
    except Exception as e:
      print("Error in cancel_options_all_order", e)

def buy_option(symbol,indicator_strategy,interval,index_sl="-"):
  try:
    option_token=symbol['symboltoken']
    option_symbol=symbol['tradingsymbol']
    if 'BANKNIFTY' in option_symbol: lotsize=15
    elif "NIFTY" in option_symbol: lotsize=50
    lotsize=int(lotsize*lots_to_trade)
    orderId,ltp_price=place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='BUY',ordertype='MARKET',price=0,
                          variety='NORMAL',exch_seg='NFO',producttype='CARRYFORWARD',ordertag=indicator_strategy)
    if "(" in indicator_strategy and ")" in indicator_strategy:
      stop_loss=(indicator_strategy.split('('))[1].split(':')[0]
      target_price=(indicator_strategy.split(stop_loss+':'))[1].split(')')[0]
      stop_loss=int(float(stop_loss))
      target_price=int(float(target_price))
    elif "Manual" in indicator_strategy:
      sl=banknifty_sl if "BANK" in option_symbol else nifty_sl
      tgt=banknifty_target if "BANK" in option_symbol else nifty_target
      if target_type == 'Points':
        stop_loss=ltp_price-sl
        target_price=ltp_price+tgt
      else:
        stop_loss=ltp_price*(100-sl)/100
        target_price=ltp_price*(100+tgt)/100
    else:
      old_data=get_historical_data(symbol=option_symbol,interval='5m',token=option_token,exch_seg="NFO",candle_type="NORMAL")
      ltp_price=float(old_data['Close'].iloc[-1])
      st_price=float(old_data['Supertrend'].iloc[-1]) if float(old_data['Supertrend'].iloc[-1])<ltp_price else 0
      st_10_price=float(old_data['Supertrend_10_2'].iloc[-1]) if float(old_data['Supertrend_10_2'].iloc[-1])<ltp_price else 0
      stop_loss=int(max(st_price,st_10_price,ltp_price*0.7))
      target_price=int(float(ltp_price)+(float(ltp_price)-float(stop_loss))*2)
      indicator_strategy=indicator_strategy+ " (" +str(stop_loss)+":"+str(target_price)+') '
    if str(orderId)=='Order placement failed': return
    orderbook=obj.orderBook()['data']
    orderbook=pd.DataFrame(orderbook)
    orders= orderbook[(orderbook['orderid'] == orderId)]
    orders_status=orders.iloc[0]['orderstatus']; trade_price=orders.iloc[0]['averageprice']
    if orders_status != 'complete': trade_price='-'
    order_price=ltp_price if trade_price=='-' else trade_price
    if trade_price!='-':
      if target_order_type=="Target":
        place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='SELL',ordertype='LIMIT',price=target_price,
                    variety='NORMAL',exch_seg='NFO',producttype='CARRYFORWARD',ordertag=str(orderId)+" Target order Placed")
      else:
        place_order(token=option_token,symbol=option_symbol,qty=lotsize,buy_sell='SELL',ordertype='STOPLOSS_LIMIT',price=stop_loss,
                    variety='STOPLOSS',exch_seg='NFO',producttype='CARRYFORWARD',triggerprice=stop_loss,squareoff=stop_loss,
                    stoploss=stop_loss, ordertag=str(orderId)+" Stop Loss order Placed")
    buy_msg=(f'Buy: {option_symbol}\nPrice: {trade_price} LTP: {ltp_price}\n{indicator_strategy}\nTarget: {target_price} Stop Loss: {stop_loss}')
    telegram_bot_sendtext(buy_msg)
    logger.info(buy_msg)
  except Exception as e:
    logger.exception(f"Error in buy_option: {e}")
    print('Error in buy_option:',e)

def exit_position(symboltoken,tradingsymbol,qty,ltp_price,sl,ordertag='',producttype='CARRYFORWARD'):
  try:
    if ltp_price==0:
      ltp_price=1
    place_order(token=symboltoken,symbol=tradingsymbol,qty=qty,buy_sell='SELL',ordertype='STOPLOSS_LIMIT',price=sl,
                variety='STOPLOSS',exch_seg='NFO',producttype=producttype,triggerprice=sl,squareoff=sl,stoploss=sl, ordertag=ordertag)
  except Exception as e:
    logger.exception(f"Error in exit_position: {e}")

def get_order_book():
  global orderbook,pending_orders
  try:
    for attempt in range(3):
      try:
        orderbook=obj.orderBook()['data']
        if orderbook!=None: break
      except: pass
    if orderbook!=None: #or isinstance(orderbook,NoneType)!=True
      orderbook= pd.DataFrame.from_dict(orderbook)
      orderbook['updatetime'] = pd.to_datetime(orderbook['updatetime'])
      orderbook=orderbook.sort_values(by = ['updatetime'], ascending = [True], na_position = 'first')
      orderbook = orderbook[(orderbook['exchange'] == 'NFO')]
      #orderbook['price']="-"
      for i in range(0,len(orderbook)):
        if orderbook['ordertag'].iloc[i]=="": orderbook['ordertag'].iloc[i]="-"
        if orderbook['status'].iloc[i]=="complete":
          orderbook['ordertag'].iloc[i]="*" + orderbook['ordertag'].iloc[i]
          orderbook['price'].iloc[i]=orderbook['averageprice'].iloc[i]
  except Exception as e:
    orderbook= pd.DataFrame(columns = ['variety', 'ordertype', 'producttype', 'duration', 'price','triggerprice', 'quantity', 'disclosedquantity',
                'squareoff','stoploss', 'trailingstoploss', 'tradingsymbol', 'transactiontype','exchange', 'symboltoken', 'ordertag', 'instrumenttype',
                'strikeprice','optiontype', 'expirydate', 'lotsize', 'cancelsize', 'averageprice','filledshares', 'unfilledshares', 'orderid', 'text',
                'status','orderstatus', 'updatetime', 'exchtime', 'exchorderupdatetime','fillid', 'filltime', 'parentorderid'])
  pending_orders = orderbook[((orderbook['orderstatus'] != 'complete') & (orderbook['orderstatus'] != 'cancelled') &
                              (orderbook['orderstatus'] != 'rejected') & (orderbook['orderstatus'] != 'AMO CANCELLED'))]
  return orderbook,pending_orders
  
def get_open_position():
  position=obj.position()['data']
  if position!=None:
    position=pd.DataFrame(position)
    position[['realised', 'unrealised']] = position[['realised', 'unrealised']].astype(float)
  else:
    position= pd.DataFrame(columns = ["exchange","symboltoken","producttype","tradingsymbol","symbolname","instrumenttype","priceden",
                                  "pricenum","genden","gennum","precision","multiplier","boardlotsize","buyqty","sellqty","buyamount",
                                  "sellamount","symbolgroup","strikeprice","optiontype","expirydate","lotsize","cfbuyqty","cfsellqty",
                                  "cfbuyamount","cfsellamount","buyavgprice","sellavgprice","avgnetprice","netvalue","netqty","totalbuyvalue",
                                  "totalsellvalue","cfbuyavgprice","cfsellavgprice","totalbuyavgprice","totalsellavgprice","netprice",'realised', 'unrealised'])
  pnl=float(position['realised'].sum())+float(position['unrealised'].sum())
  open_position = position[(position['netqty'] > '0') & (position['instrumenttype'] == 'OPTIDX')]
  return position,open_position
  
def get_historical_data(symbol="-",interval='5m',token="-",exch_seg="-",candle_type="NORMAL"):
  try:
    if (symbol=="^NSEI" or symbol=="NIFTY") : symbol,token,exch_seg="^NSEI",99926000,"NSE"
    elif (symbol=="^NSEBANK" or symbol=="BANKNIFTY") : symbol,token,exch_seg="^NSEBANK",99926009,"NSE"
    if symbol[3:]=='-EQ': symbol=symbol[:-3]+".NS"
    odd_candle,odd_interval,df=False,'','No Data Found'
    if (interval=="5m" or interval=='FIVE_MINUTE'): period,delta_time,agl_interval,yf_interval,odd_interval=7,5,"FIVE_MINUTE","5m",'5m'
    elif (interval=="15m" or interval=='FIFTEEN_MINUTE'): period,delta_time,agl_interval,yf_interval,odd_interval=10,15,"FIFTEEN_MINUTE","15m",'15m'
    elif (interval=="60m" or interval=='ONE_HOUR'): period,delta_time,agl_interval,yf_interval,odd_interval=30,60,"ONE_HOUR","60m",'60m'
    elif (interval=="1m" or interval=='ONE_MINUTE') : period,delta_time,agl_interval,yf_interval,odd_interval=7,1,"ONE_MINUTE","1m",'1m'
    elif (interval=="1d" or interval=='ONE_DAY') : period,delta_time,agl_interval,yf_interval,odd_interval=100,5,"ONE_DAY","1d",'1d'
    else:
      period,delta_time,agl_interval,yf_interval,odd_candle=7,1,"ONE_MINUTE","1m",True
      for i in interval:
        if(i.isdigit()): odd_interval+=i
      delta_time=int(odd_interval)
      odd_interval+='m'
    #if (symbol[0]=="^" or "NS" in symbol) and symbol !="-":
    #  df=yfna_data(symbol,yf_interval,str(period)+"d")
    if isinstance(df, str):
      to_date= datetime.datetime.now(tz=gettz('Asia/Kolkata'))
      from_date = to_date - datetime.timedelta(days=period)
      fromdate = from_date.strftime("%Y-%m-%d %H:%M")
      todate = to_date.strftime("%Y-%m-%d %H:%M")
      df=angel_data(token,agl_interval,exch_seg,fromdate,todate)
    if odd_candle ==True:
      df=df.groupby(pd.Grouper(freq=odd_interval+'in')).agg({"Date":"first","Datetime":"first","Open": "first", "High": "max",
                                                        "Low": "min", "Close": "last","Volume": "sum"})
      df=df[(df['Open']>0)]
    now=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None)
    last_candle=now.replace(second=0, microsecond=0)- datetime.timedelta(minutes=delta_time)
    df = df[(df['Date_Time'] <= last_candle)]
    df['Time Frame']=odd_interval
    if candle_type=="HEIKIN_ASHI": df=calculate_heikin_ashi(df)
    #df['VWAP']=pdta.vwap(high=df['High'],low=df['Low'],close=df['Close'],volume=df['Volume'])
    df['VWAP']="-"
    df=df[['Date','Datetime','Open','High','Low','Close','Volume','VWAP','Time Frame']]
    df['Symbol']=symbol
    df=calculate_indicator(df)
    df=df.round(2)
    return df
  except Exception as e:
    logger.exception(f"Error in get_historical_data: {e}")

def yfna_data(symbol,interval,period):
  try:
    df=yf.Ticker(symbol).history(interval=interval,period=period)
    df['Datetime'] = df.index
    df['Datetime']=df['Datetime'].dt.tz_localize(None)
    df=df.reset_index(drop=True)
    df['Date_Time']=df['Datetime']
    df['Date']=df['Datetime'].dt.strftime('%m/%d/%y')
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.time
    df=df[['Date_Time','Date','Datetime','Open','High','Low','Close','Volume']]
    if isinstance(df, str) or (isinstance(df, pd.DataFrame)==True and len(df)==0):
      print("Yahoo Data Not Found")
      return "No data found, symbol may be delisted"
    return df
  except Exception as e:
    print("Yahoo Data Not Found")
    logger.exception(f"Error in yfna_data: {e}")
    return "No data found, symbol may be delisted"
  
def angel_data(token,interval,exch_seg,fromdate,todate):
  try:
    historicParam={"exchange": exch_seg,"symboltoken": token,"interval": interval,"fromdate": fromdate, "todate": todate}
    res_json=obj.getCandleData(historicParam)
    df = pd.DataFrame(res_json['data'], columns=['timestamp','O','H','L','C','V'])
    df = df.rename(columns={'timestamp':'Datetime','O':'Open','H':'High','L':'Low','C':'Close','V':'Volume'})
    df['Datetime'] = df['Datetime'].apply(lambda x: datetime.datetime.fromisoformat(x))
    #df['Datetime'] = pd.to_datetime(df['Datetime'],format = '%Y-%m-%d %H:%M:%S')
    df['Datetime']=df['Datetime'].dt.tz_localize(None)
    df['Date_Time']=df['Datetime']
    df['Date']=df['Datetime'].dt.strftime('%m/%d/%y')
    df['Datetime'] = pd.to_datetime(df['Datetime']).dt.time
    df=df[['Date_Time','Date','Datetime','Open','High','Low','Close','Volume']]
    if isinstance(df, str) or (isinstance(df, pd.DataFrame)==True and len(df)==0):
      print("Angel Data Not Found")
      return "No data found, symbol may be delisted"
    return df
  except Exception as e:
    print("Angel Data Not Found")
    logger.exception(f"Error in Angel Data Not Found: {e}")
    return "No data found, symbol may be delisted"

def get_trade_info(df):
  for i in ['St Trade','MACD Trade','PSAR Trade','DI Trade','MA Trade','EMA Trade','BB Trade','Trade','Trade End',
            'Rainbow MA','Rainbow Trade','MA 21 Trade','ST_10_2 Trade','Two Candle Theory','HMA Trade','VWAP Trade',
            'EMA_5_7 Trade','ST_10_4_8 Trade','EMA_High_Low Trade','RSI MA Trade','RSI_60 Trade']:df[i]='-'
  if df['Time Frame'][0]=="3m" or df['Time Frame'][0]=="THREE MINUTE" or df['Time Frame'][0]=="3min": df['Time Frame']="3m";time_frame="3m"
  elif df['Time Frame'][0]=="5m" or df['Time Frame'][0]=="FIVE MINUTE" or df['Time Frame'][0]=="5min": df['Time Frame']="5m";time_frame="5m"
  elif df['Time Frame'][0]=="15m" or df['Time Frame'][0]=="FIFTEEN MINUTE" or df['Time Frame'][0]=="15min": df['Time Frame']="15m";time_frame="15m"
  elif df['Time Frame'][0]=="1m" or df['Time Frame'][0]=="ONE MINUTE" or df['Time Frame'][0]=="1min": df['Time Frame']="1m";time_frame="1m"
  time_frame=df['Time Frame'][0]
  Symbol=df['Symbol'][0]
  df['Brahmastra']=''
  logger.info(type(df['Close'].iloc[-1]))
  for i in range(len(df)-10,len(df)):
    try:
      #df['Date'][i]=df['Datetime'][i].strftime('%Y.%m.%d')
      if df['Close'][i-1]<=df['Supertrend'][i-1] and df['Close'][i]> df['Supertrend'][i]: df['St Trade'][i]="Buy"
      elif df['Close'][i-1]>=df['Supertrend'][i-1] and df['Close'][i]< df['Supertrend'][i]: df['St Trade'][i]="Sell"

      if df['MACD'][i]>df['MACD signal'][i] and df['MACD'][i-1]< df['MACD signal'][i-1]: df['MACD Trade'][i]="Buy"
      elif df['MACD'][i]<df['MACD signal'][i] and df['MACD'][i-1]> df['MACD signal'][i-1]: df['MACD Trade'][i]="Sell"

      if df['Close'][i-1]<=df['PSAR'][i-1] and df['Close'][i]> df['PSAR'][i]: df['PSAR Trade'][i]="Buy"
      elif df['Close'][i-1]>=df['PSAR'][i-1] and df['Close'][i]< df['PSAR'][i]: df['PSAR Trade'][i]="Sell"

      if df['PLUS_DI'][i-1]<=df['MINUS_DI'][i-1] and df['PLUS_DI'][i]> df['MINUS_DI'][i]: df['DI Trade'][i]="Buy"
      elif df['PLUS_DI'][i-1]>=df['MINUS_DI'][i-1] and df['PLUS_DI'][i]< df['MINUS_DI'][i]: df['DI Trade'][i]="Sell"

      if df['MA_50'][i-1]<=df['MA_200'][i-1] and df['MA_50'][i]> df['MA_200'][i]: df['MA Trade'][i]="Buy"
      elif df['MA_50'][i-1]>=df['MA_200'][i-1] and df['MA_50'][i]< df['MA_200'][i]: df['MA Trade'][i]="Sell"

      if df['EMA_12'][i-1]<=df['EMA_26'][i-1] and df['EMA_12'][i]> df['EMA_26'][i]: df['EMA Trade'][i]="Buy"
      elif df['EMA_12'][i-1]>=df['EMA_26'][i-1] and df['EMA_12'][i]< df['EMA_26'][i]: df['EMA Trade'][i]="Sell"

      if df['EMA_5'][i-1]<=df['EMA_7'][i-1] and df['EMA_5'][i]> df['EMA_7'][i]: df['EMA_5_7 Trade'][i]="Buy"
      elif df['EMA_5'][i-1]>=df['EMA_7'][i-1] and df['EMA_5'][i]< df['EMA_7'][i]: df['EMA_5_7 Trade'][i]="Sell"

      if df['Close'][i-1]< df['MA_21'][i-1] and df['Close'][i]> df['MA_21'][i]: df['MA 21 Trade'][i]="Buy"
      elif df['Close'][i-1]> df['MA_21'][i-1] and df['Close'][i]< df['MA_21'][i]: df['MA 21 Trade'][i]="Sell"

      if df['Close'][i-1]< df['Supertrend_10_2'][i-1] and df['Close'][i]> df['Supertrend_10_2'][i]: df['ST_10_2 Trade'][i]="Buy"
      elif df['Close'][i-1]> df['Supertrend_10_2'][i-1] and df['Close'][i]< df['Supertrend_10_2'][i]: df['ST_10_2 Trade'][i]="Sell"

      if df['HMA_21'][i-1]< df['HMA_55'][i-1] and df['HMA_21'][i]> df['HMA_55'][i]: df['HMA Trade'][i]="Buy"
      elif df['HMA_21'][i-1]> df['HMA_55'][i-1] and df['HMA_21'][i]< df['HMA_55'][i]: df['HMA Trade'][i]="Sell"

      if int(df['RSI'][i])>=60 and int(df['RSI'][i-1]) < 60 : df['RSI_60 Trade'][i]="Buy"

      if int(df['RSI'][i])>=60 or int(df['RSI'][i])<=40:
        if df['Close'][i-1]<df['EMA_High'][i-1] and df['Close'][i] > df['EMA_High'][i]: df['EMA_High_Low Trade'][i]="Buy"
        if df['Close'][i-1]>df['EMA_Low'][i-1] and df['Close'][i]<df['EMA_Low'][i]: df['EMA_High_Low Trade'][i]="Sell"

      if (df['Close'][i-1]<df['Open'][i-1] and df['Close'][i]< df['Open'][i] and
        df['Close'][i]< df['Supertrend_10_2'][i] and df['RSI'][i]<=40 and df['VWAP'][i]>df['Close'][i] and
        df['Close'][i]<df['WMA_20'][i] and df['Volume'][i]>1000):
        df['Two Candle Theory'][i]='Sell'
      elif (df['Close'][i-1] > df['Open'][i-1] and df['Close'][i] > df['Open'][i] and
        df['Close'][i] > df['Supertrend_10_2'][i] and df['RSI'][i] >= 50 and df['VWAP'][i]<df['Close'][i] and
        df['Close'][i]>df['WMA_20'][i] and df['Volume'][i]>1000):
        df['Two Candle Theory'][i]='Buy'

      RSI=df['RSI'][i];          ST=df['St Trade'][i]
      MACD=df['MACD Trade'][i];  EMA=df['EMA Trade'][i]
      MA=df['MA 21 Trade'][i];   ST_10_2=df['ST_10_2 Trade'][i]
      RSI_60=df['RSI_60 Trade'][i]
      Two_Candle_Theory=df['Two Candle Theory'][i]; HMA_Trade=df['HMA Trade'][i]
      EMA_5_7_Trade=df['EMA_5_7 Trade'][i];EMA_High_Low=df['EMA_High_Low Trade'][i]

      df['Brahmastra'][i]=' Brahmastra' if (ST==MACD or ST_10_2==MACD) and MACD!="-" else ''
      if time_frame=="1m" or time_frame=="ONE_MINUTE" or time_frame=="1min":
        if (ST=="Buy" or MACD=="Buyy" or EMA=="Buyy" or MA=="Buyy" or ST_10_2=="Buyy" or EMA_High_Low=="Buy") and (int(RSI)<=40 or int(RSI)>=60) :
          df['Trade'][i]="Buy"; df['Trade End'][i]="Buyy"
        elif (ST=="Sell" or MACD=="Selll" or EMA=="Selll" or MA=="Selll" or ST_10_2=="Selll" or EMA_High_Low=="Sell") and (int(RSI)<=40 or int(RSI)>=60):
          df['Trade'][i]="Sell"; df['Trade End'][i]="Selll"

      elif time_frame=="3m" or time_frame=="THREE_MINUTE" or time_frame=="3min" or time_frame=="Candle Pattern":
        if Two_Candle_Theory=="Buy" :
          df['Trade'][i]="Buy"; df['Trade End'][i]="Buy"
        elif Two_Candle_Theory=="Sell":
          df['Trade'][i]="Sell"; df['Trade End'][i]="Sell"

      elif time_frame=="5m" or time_frame=="FIVE_MINUTE" or time_frame=="5min":
        if (ST=="Buy" or EMA=="Buyy" or MA=="Buyy" or ST_10_2=="Buy" or HMA_Trade=="Buyy" or MA=='Buyy' or RSI_60=="Buyy"):
          df['Trade'][i]="Buy"; df['Trade End'][i]="Buy"
        elif (ST=="Sell" or EMA=="Selll" or MA=="Selll" or ST_10_2=="Sell" or HMA_Trade=="Selll" or MA=='Selll'):
          df['Trade'][i]="Sell"; df['Trade End'][i]="Sell"
        #if EMA_High_Low=="Buy":df['Trade'][i]="Buy";df['Trade End'][i]="Buy"
        #if EMA_High_Low=="Sell":df['Trade'][i]="Sell";df['Trade End'][i]="Sell"

      elif time_frame=="15m" or time_frame=="FIFTEEN_MINUTE" or time_frame=="15min":
        if (ST=="Buy" or MACD=="Buyy" or EMA=="Buyy" or MA=="Buyy" or ST_10_2=="Buy" or RSI_60=="Buyy"):
          df['Trade'][i]="Buy"; df['Trade End'][i]="Buy"
        elif (ST=="Sell" or MACD=="Selll" or EMA=="Selll" or MA=="Selll" or ST_10_2=="Sell"):
          df['Trade'][i]="Sell"; df['Trade End'][i]="Sell"

      if 'FUT' in Symbol:
        if df['Close'][i-1]< df['VWAP'][i-1] and df['Close'][i]> df['VWAP'][i]: df['VWAP Trade'][i]="Buy"
        elif df['Close'][i-1]> df['VWAP'][i-1] and df['Close'][i]< df['VWAP'][i]: df['VWAP Trade'][i]="Sell"

    except Exception as e:
      logger.exception(f"Error in get_trade_info: {e}")
  df['ADX']=df['ADX'].round(decimals = 2)
  df['ADX']= df['ADX'].astype(str)
  df['Atr']=df['Atr'].round(decimals = 2)
  df['Atr']= df['Atr'].astype(str)
  df['RSI']=df['RSI'].round(decimals = 2)
  df['RSI']= df['RSI'].astype(str)
  symbol_type="IDX" if Symbol=="^NSEBANK" or Symbol=="BANKNIFTY" or Symbol=="^NSEI" or Symbol=="NIFTY" else "OPT"
  df['Indicator']=(symbol_type+" "+df['Trade']+" "+df['Time Frame']+":"+" ST:"+df['St Trade']+" EMA:"+df['EMA Trade']+" MACD:"+df['MACD Trade']+
                   " ST_10_2:"+df['ST_10_2 Trade']+ " MA_21:"+df['MA 21 Trade']+" Two Candle Theory:"+df['Two Candle Theory']+" RSI_60:"+df['RSI_60 Trade'])
  df['RSI']= df['RSI'].astype(float)
  df['Indicator'] = df['Indicator'].str.replace(' ST:-','')
  df['Indicator'] = df['Indicator'].str.replace(' EMA:-','')
  df['Indicator'] = df['Indicator'].str.replace(' MA:-','')
  df['Indicator'] = df['Indicator'].str.replace(' MACD:-','')
  df['Indicator'] = df['Indicator'].str.replace(' ST_10_2:-','')
  df['Indicator'] = df['Indicator'].str.replace(' HMA:-','')
  df['Indicator'] = df['Indicator'].str.replace(' MA_21:-','')
  df['Indicator'] = df['Indicator'].str.replace(' EMA_5_7 Trade:-','')
  df['Indicator'] = df['Indicator'].str.replace(' EMA_5_7:-','')
  df['Indicator'] = df['Indicator'].str.replace(' VWAP:-','')
  df['Indicator'] = df['Indicator'].str.replace(' EMA_H_L:-','')
  df['Indicator'] = df['Indicator'].str.replace(' Two Candle Theory:-','')
  df['Indicator'] = df['Indicator'].str.replace(' RSI_60:-','')
  df['Indicator'] = df['Indicator'].str.replace(':Buy',',')
  df['Indicator'] = df['Indicator'].str.replace(':Sell',',')
  df['Indicator'] = df['Indicator'].str.replace('3m Two Candle Theory:','2 Candle Theory:')
  df["Indicator"] = df["Indicator"].str[:-1]
  return df
  
def calculate_indicator(df):
  try:
    df['RSI']=pdta.rsi(df['Close'],timeperiod=14)
    df['UBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBU_20_2.0']
    df['MBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBM_20_2.0']
    df['LBB']=pdta.bbands(df['Close'],length=20, std=2, ddof=0)['BBL_20_2.0']
    df['MACD']=pdta.macd(close=df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)['MACD_12_26_9']
    df['MACD signal']=pdta.macd(close=df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)['MACDs_12_26_9']
    df['Macdhist']=pdta.macd(close=df['Close'], fastperiod=12, slowperiod=26, signalperiod=9)['MACDh_12_26_9']
    df['Supertrend']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=7,multiplier=3)['SUPERT_7_3.0']
    df['Supertrend_10_2']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=2)['SUPERT_10_2.0']
    df['PSAR']=pdta.psar(high=df['High'],low=df['Low'],acceleration=0.02, maximum=0.2)['PSARl_0.02_0.2']
    df['ADX']=pdta.adx(df['High'],df['Low'],df['Close'],14)['ADX_14']
    df['MINUS_DI']=pdta.adx(df['High'],df['Low'],df['Close'],14)['DMN_14']
    df['PLUS_DI']=pdta.adx(df['High'],df['Low'],df['Close'],14)['DMP_14']
    df['MA_200']=df['Close'].rolling(200).mean()
    df['MA_50']=df['Close'].rolling(50).mean()
    df['EMA_12']=pdta.ema(df['Close'],length=12)
    df['EMA_26']=pdta.ema(df['Close'],length=26)
    df['EMA_13']=pdta.ema(df['Close'],length=13)
    df['EMA_5']=pdta.ema(df['Close'],length=5)
    df['EMA_7']=pdta.ema(df['Close'],length=7)
    df['MA_1']=df['Close'].rolling(1).mean()
    df['MA_2']=df['Close'].rolling(2).mean()
    df['MA_3']=df['Close'].rolling(3).mean()
    df['MA_4']=df['Close'].rolling(4).mean()
    df['MA_5']=df['Close'].rolling(5).mean()
    df['MA_6']=df['Close'].rolling(6).mean()
    df['MA_7']=df['Close'].rolling(7).mean()
    df['MA_8']=df['Close'].rolling(8).mean()
    df['MA_9']=df['Close'].rolling(9).mean()
    df['MA_10']=df['Close'].rolling(10).mean()
    df['MA_21']=pdta.ema(df['Close'],length=21)
    df['WMA_20']=pdta.wma(df['Close'],length=20)
    df['Atr']=pdta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)
    df['HMA_21']=pdta.hma(df['Close'],length=21)
    df['HMA_55']=pdta.hma(df['Close'],length=55)
    df['RSI_MA']=df['RSI'].rolling(14).mean()
    df['Supertrend_10_4']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=4)['SUPERT_10_4.0']
    df['Supertrend_10_8']=pdta.supertrend(high=df['High'],low=df['Low'],close=df['Close'],length=10,multiplier=8)['SUPERT_10_8.0']
    df['EMA_High']=pdta.ema(df['High'],length=21)
    df['EMA_Low']=pdta.ema(df['Low'],length=21)
    #df = df.round(decimals=2)
    df=get_trade_info(df)
    return df
  except Exception as e:
    logger.exception(f"Error in calculate Indicator: {e}")
    print("Error in calculate Indicator",e)
    return df

def calculate_heikin_ashi(df):
  for i in range(2,len(df)):
    o=df['Open'][i-0]
    h=df['High'][i-0]
    l=df['Low'][i-0]
    c=df['Close'][i-0]
    df['Open'][i]=(o+c)/2
    df['Close'][i]=(o+h+l+c)/4
  return df

def get_ce_pe_data(symbol,indexLtp,ce_pe="CE"):
    indexLtp=float(indexLtp) if indexLtp!="-" else get_index_ltp(symbol)
    if symbol=='BANKNIFTY' or symbol=='^NSEBANK':
        symbol='BANKNIFTY'
        ATMStrike = math.floor(indexLtp/100)*100
        expiry_day=st.session_state['bnf_expiry_day']
    elif symbol=='NIFTY' or symbol=='^NSEI':
        symbol='NIFTY'
        val2 = math.fmod(indexLtp, 50)
        val3 = 50 if val2 >= 25 else 0
        ATMStrike = indexLtp - val2 + val3
        expiry_day=st.session_state['nf_expiry_day']
    opt_symbol=symbol + expiry_day + str(int(ATMStrike)) + ce_pe
    strike_symbol=obj.searchScrip("NFO",opt_symbol)['data'][0]
    return strike_symbol

def index_trade(symbol="-",interval="-",candle_type="NORMAL",token="-",exch_seg="-"):
  try:
    fut_data=get_historical_data(symbol,interval=interval,token=token,exch_seg=exch_seg,candle_type=candle_type)
    trade=str(fut_data['Trade'].values[-1])
    trade_end=str(fut_data['Trade End'].values[-1])
    if trade!="-":
      indicator_strategy=fut_data['Indicator'].values[-1]
      indexLtp=fut_data['Close'].values[-1]
      interval_yf=fut_data['Time Frame'].values[-1]
      if trade=="Buy" : strike_symbol=get_ce_pe_data(symbol,indexLtp=indexLtp,ce_pe="CE")
      elif trade=="Sell" : strike_symbol=get_ce_pe_data(symbol,indexLtp=indexLtp,ce_pe="PE")
      buy_option(strike_symbol,indicator_strategy,interval)
    if symbol=="^NSEBANK" or symbol=="BANKNIFTY":
      n_symbol="bnf"
      st.session_state['BankNifty_Trade_End']=trade_end
    else:
      n_symbol="nf"
      st.session_state['Nifty_Trade_End']=trade_end
    information_name=interval + "_" + n_symbol
    information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),'Symbol':symbol,
                 'Datetime':str(fut_data['Datetime'].values[-1]),'Close':fut_data['Close'].values[-1],'Indicator':fut_data['Indicator'].values[-1],
                 'Trade':fut_data['Trade'].values[-1],'Trade End':fut_data['Trade End'].values[-1],'Supertrend':fut_data['Supertrend'].values[-1],
                'Supertrend_10_2':fut_data['Supertrend_10_2'].values[-1],'RSI':fut_data['RSI'].values[-1]}
    st.session_state['options_trade_list'].append(information)
    st.session_state[information_name]=information
    return fut_data
  except Exception as e:
    logger.exception(f"Error in index trade: {e}")
    print('Error in index trade:',symbol,e)

def manual_buy(index_symbol,ce_pe="CE",index_ltp="-"):
  try:
    if index_ltp=="-":
      if index_symbol=="BANKNIFTY" or index_symbol=="^NSEBANK": index_ltp=st.session_state['BankNifty']
      if index_symbol=="NIFTY" or index_symbol=="^NSEI": index_ltp=st.session_state['Nifty']
    if index_ltp=="-": index_ltp=get_index_ltp(index_symbol)
    strike_symbol=get_ce_pe_data(index_symbol,index_ltp,ce_pe)
    buy_option(strike_symbol,"Manual Buy","5m")
  except Exception as e:
    logger.exception(f"Error in manual_buy: {e}")
    print(e)

def get_near_option_list():
  options_trade=[]
  for i in range(0,2):
    for symbol in ['BANKNIFTY','NIFTY']:
      for ce_pe in ['CE','PE']:
        if symbol=='BANKNIFTY':
          expiry_day=st.session_state['bnf_expiry_day']
          index_ltp=st.session_state['BankNifty']
          diff=100
        elif symbol=='NIFTY':
          expiry_day=st.session_state['nf_expiry_day']
          index_ltp=st.session_state['Nifty']
          diff=50
        index_ltp=diff*round(index_ltp/diff)
        if ce_pe=="CE":strike_price=index_ltp+(i*diff)
        else:strike_price=index_ltp-(i*diff)
        opt_symbol=symbol+expiry_day+str(int(strike_price))+ce_pe
        for j in range(0,3):
          try:
            strike_symbol=obj.searchScrip("NFO",opt_symbol)['data'][0]
            options_trade.append(strike_symbol)
            time.sleep(0.5)
            break
          except Exception as e:
            pass
  st.session_state['Near_option_list']=options_trade
  near_option.empty()
  with near_option.container():
    st.write(f"Near Option List : {datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()}")
    #print_string=""
    #for i in st.session_state['Near_option_list']:
    #  print_string=(f'''{print_string}  \n {i}''')
    #st.write(print_string)
    st.dataframe(pd.DataFrame.from_dict(st.session_state['Near_option_list']),hide_index=True)
def near_option_trade(interval):
  if st.session_state['Near_option_list']==[]:get_near_option_list()
  #options_trade=[]
  for i in st.session_state['Near_option_list']:
    try:
      token=i['symboltoken']
      symbol=i['tradingsymbol']
      fut_data=get_historical_data(symbol,interval=interval,token=token,exch_seg='NFO')
      indicator_strategy=fut_data['Indicator'].values[-1]
      if (fut_data['St Trade'].values[-1]=="Buy" or fut_data['ST_10_2 Trade'].values[-1]=="Buy"):buy_option(i,indicator_strategy,"5m")
      information={'Time':str(datetime.datetime.now(tz=gettz('Asia/Kolkata')).time().replace(microsecond=0)),'Symbol':symbol,
                 'Datetime':str(fut_data['Datetime'].values[-1]),'Close':fut_data['Close'].values[-1],'Indicator':fut_data['Indicator'].values[-1],
                 'Trade':fut_data['Trade'].values[-1],'Trade End':fut_data['Trade End'].values[-1],'Supertrend':fut_data['Supertrend'].values[-1],
                'Supertrend_10_2':fut_data['Supertrend_10_2'].values[-1],'RSI':fut_data['RSI'].values[-1]}
      #options_trade.append(information)
      st.session_state['options_trade_list'].append(information)
    except Exception as e:
      logger.exception(f"Error in near_option_trade: {e}")
      pass

def update_todays_trade(todays_trade_log):
  #g_todays_trade_log=todays_trade_log[['updatetime','tradingsymbol','price','Stop Loss','Target','LTP','Status','Sell','Profit','Profit %','ordertag','Sell Indicator']]
  #g_todays_trade_log = g_todays_trade_log.rename(columns={'updatetime':'Time','tradingsymbol':'Symbol','price':'Price','Stop Loss':'SL','Target':'TGT','Profit %':'PL%','ordertag':'Buy Indicator'})
  #g_todays_trade_log=todays_trade_log[['updatetime','tradingsymbol','price','Stop Loss','Target','LTP','Status','Exit Time','Sell','Profit','Profit %','ordertag','Sell Indicator']]
  pl=("Realised:"+str(int(todays_trade_log[(todays_trade_log['Trade Status']=='Closed')]['Profit'].sum())) +
            " Unrealised:"+str(int(todays_trade_log[(todays_trade_log['Trade Status']!='Closed')]['Profit'].sum())))
  algo_trade_updated.text(f"Algo Trade: {datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()} {pl}")
  todays_trade_log=todays_trade_log[['updatetime','tradingsymbol','price','quantity','ordertag','Sell','Target','Stop Loss','LTP','Trade Status',
                            'Profit','Exit Time','Sell Indicator']]
  algo_datatable.dataframe(todays_trade_log,hide_index=True)
  #algo_datatable.table(todays_trade_log)

def update_target_sl(buy_df):
  global order_history,target_history
  for i in range(0,len(buy_df)):
    try:
      if "(" in buy_df['ordertag'].iloc[i] and ")" in buy_df['ordertag'].iloc[i]:
        sl=(buy_df['ordertag'].iloc[i].split('('))[1].split(':')[0]
        tgt=(buy_df['ordertag'].iloc[i].split(sl+':'))[1].split(')')[0]
        buy_df['Stop Loss'].iloc[i]=sl
        buy_df['Target'].iloc[i]=tgt
      else:
        buy_df['Stop Loss'].iloc[i]=buy_df['price'].iloc[i]*0.7
        buy_df['Target'].iloc[i]=buy_df['price'].iloc[i]*1.5
    except Exception as e:
      print('Error found in ',e)
  buy_df['Stop Loss']=round(buy_df['Stop Loss'].astype(int),2)
  buy_df['Target']=round(buy_df['Target'].astype(int),2)
  return buy_df

def get_ltp_token(tokenlist):
  try:
    ltp_df=pd.DataFrame(obj.getMarketData(mode="LTP",exchangeTokens={ "NSE": ["99926000","99926009"], "NFO": list(tokenlist)})['data']['fetched'])
    return ltp_df
  except Exception as e:
    logger.exception(f"Error in get_ltp_token: {e}")
    ltp_df=pd.DataFrame(columns = ['exchange','tradingSymbol','symbolToken','ltp'])
    return ltp_df
  
def update_ltp_buy_df(buy_df):
  tokenlist=buy_df['symboltoken'].values.tolist()
  ltp_df=get_ltp_token(numpy.unique(tokenlist))
  for i in range(0,len(buy_df)):
    try:
      symboltoken=(buy_df['symboltoken'].iloc[i])
      n_ltp_df=ltp_df[ltp_df['symbolToken']==symboltoken]
      if len(n_ltp_df)!=0:
        buy_df['LTP'].iloc[i]=n_ltp_df['ltp'].iloc[0]
      else:
        buy_df['LTP'].iloc[i]=get_ltp_price(symbol=buy_df['tradingsymbol'].iloc[i],token=buy_df['symboltoken'].iloc[i],exch_seg=buy_df['exchange'].iloc[i])
      #buy_df['LTP'].iloc[i]=round(buy_df['LTP'].iloc[i],2)
    except Exception as e:
      pass
  buy_df['LTP']=round(buy_df['LTP'].astype(int),2)
  return buy_df

def ganesh_sl_trail():
  global todays_trade_log
  for i in range(0,len(todays_trade_log)):
    if todays_trade_log['Status'].iloc[i]=="Pending":
      try:
        ordertag=todays_trade_log['ordertag'].iloc[i]
        symbol=todays_trade_log['tradingsymbol'].iloc[i]
        token=todays_trade_log['symboltoken'].iloc[i]
        exchange=todays_trade_log['exchange'].iloc[i]
        price=float(todays_trade_log['price'].iloc[i])
        if "1m" in todays_trade_log['ordertag'].iloc[i]: interval="1m"
        elif "5m" in todays_trade_log['ordertag'].iloc[i]: interval="5m"
        else: interval="15m"
        old_data=get_historical_data(symbol=symbol,interval=interval,token=token,exch_seg=exchange,candle_type="NORMAL")
        st_10_2=float(old_data['Supertrend_10_2'].iloc[-1])
        st_7_3=float(old_data['Supertrend'].iloc[-1])
        ema_low=float(old_data['EMA_Low'].iloc[-1])
        close_price=float(old_data['Close'].iloc[-1])
        old_sl=todays_trade_log['Stop Loss'].iloc[i]
        if st_7_3 < close_price: todays_trade_log['Stop Loss'].iloc[i]=st_7_3
        elif st_10_2 < close_price: todays_trade_log['Stop Loss'].iloc[i]=st_10_2
        else: todays_trade_log['Stop Loss'].iloc[i]=max(price,close_price)*0.7
      except Exception as e:
        logger.exception(f"Error in sl_trail: {e}")
        print(e)

def get_profit_loss(buy_df):
  for i in range(0,len(buy_df)):
    if buy_df['Trade Status'].iloc[i]=='Pending':
      buy_df['Profit'].iloc[i]=int(buy_df['quantity'].iloc[i])*(int(buy_df['LTP'].iloc[i])-int(buy_df['price'].iloc[i]))
    else:
      buy_df['Profit'].iloc[i]=int(buy_df['quantity'].iloc[i])*(int(buy_df['Sell'].iloc[i])-int(buy_df['price'].iloc[i]))
  buy_df['Profit']=round(buy_df['Profit'].astype(int),2)
  return buy_df

def check_target_sl(buy_df):
  for i in range(0,len(buy_df)):
    try:
      if buy_df['Trade Status'].iloc[i]=='Pending':
        symboltoken=buy_df['symboltoken'].iloc[i]
        tradingsymbol=buy_df['tradingsymbol'].iloc[i]
        qty=buy_df['quantity'].iloc[i]
        ltp_price=buy_df['LTP'].iloc[i]
        orderid=buy_df['orderid'].iloc[i]
        if int(float(ltp_price)) <= int(float(buy_df['Stop Loss'].iloc[i])):
          logger.info(f"Exit {tradingsymbol} orderid: {orderid} stop loss: {ltp_price}")
          exit_position(symboltoken,tradingsymbol,qty,ltp_price,ltp_price,ordertag=str(orderid)+" Stop Loss Hit LTP: "+str(float(ltp_price)))
          buy_df['Trade Status'].iloc[i]="Stop Loss Hit"
        elif int(float(ltp_price)) >= int(float(buy_df['Target'].iloc[i])):
          logger.info(f"Exit {tradingsymbol} orderid: {orderid} Target: {ltp_price}")
          exit_position(symboltoken,tradingsymbol,qty,ltp_price,ltp_price,ordertag=str(orderid)+" Target Hit LTP: "+str(float(ltp_price)))
          buy_df['Trade Status'].iloc[i]="Target Hit"
        elif ((st.session_state['BankNifty_Trade_End']=='Sell' and tradingsymbol[-2:]=='CE' and tradingsymbol[:4]=='BANK') or
              (st.session_state['BankNifty_Trade_End']=='Buy' and tradingsymbol[-2:]=='PE' and tradingsymbol[:4]=='BANK') or
              (st.session_state['Nifty_Trade_End']=='Sell' and tradingsymbol[-2:]=='CE' and tradingsymbol[:5]=='NIFTY') or
              (st.session_state['Nifty_Trade_End']=='Buy' and tradingsymbol[-2:]=='PE' and tradingsymbol[:5]=='NIFTY')):
              logger.info(f"Exit {tradingsymbol} orderid: {orderid} Target: {ltp_price}")
              exit_position(symboltoken,tradingsymbol,qty,ltp_price,ltp_price,ordertag=str(orderid)+" Indicator Exit LTP: "+str(float(ltp_price)))
              buy_df['Trade Status'].iloc[i]="Indicator Exit"
        else:
          fut_data=get_historical_data(tradingsymbol,interval="5m",token=symboltoken,exch_seg='NFO')
          Indicator=fut_data['Indicator'].values[-1]
          if (fut_data['St Trade'].values[-1]=="Sell" or fut_data['ST_10_2 Trade'].values[-1]=="Sell"):
            logger.info(f"Exit {tradingsymbol} orderid: {orderid} Target: {ltp_price}")
            exit_position(symboltoken,tradingsymbol,qty,ltp_price,ltp_price,ordertag=str(orderid)+ " " +Indicator +" Exit LTP: "+str(float(ltp_price)))
            buy_df['Trade Status'].iloc[i]="Opt Indicator Exit"
          else:
            if int(ltp_price)> int(fut_data['Supertrend'].values[-1]):buy_df['Stop Loss'].iloc[i]=int(fut_data['Supertrend'].values[-1])
            elif int(ltp_price)> int(fut_data['Supertrend_10_2'].values[-1]):buy_df['Stop Loss'].iloc[i]=int(fut_data['Supertrend_10_2'].values[-1])
    except Exception as e:
      logger.exception(f"Error in check_target_sl: {e}")
      pass
  return buy_df
        
def get_todays_trade(orderbook):
  try:
    buy_df=orderbook[(orderbook['transactiontype']=="BUY") & ((orderbook['status']=="complete") | (orderbook['status']=="rejected"))]
    sell_df=orderbook[(orderbook['transactiontype']=="SELL") & ((orderbook['status']=="complete") | (orderbook['status']=="rejected"))]
    sell_df['Remark']='-'
    buy_df['Sell']='-'
    buy_df['Target']='-'
    buy_df['Stop Loss']='-'
    buy_df['LTP']='-'
    buy_df['Trade Status']='Pending'
    buy_df['Profit']='-'
    buy_df['Exit Time']=datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(hour=15, minute=30, second=0, microsecond=0,tzinfo=None)
    buy_df['Exit Time'] = pd.to_datetime(buy_df['Exit Time']).dt.time
    buy_df['Sell Indicator']='-'
    buy_df=update_ltp_buy_df(buy_df)
    buy_df=update_target_sl(buy_df)
    for i in range(0,len(buy_df)):
      symbol=buy_df['tradingsymbol'].iloc[i]
      updatetime=buy_df['updatetime'].iloc[i]
      orderid=buy_df['orderid'].iloc[i]
      if buy_df['Trade Status'].iloc[i]=='Pending':
        for k in range(0,len(sell_df)):
          if (sell_df['tradingsymbol'].iloc[k]==symbol and sell_df['updatetime'].iloc[k] >= updatetime and sell_df['Remark'].iloc[k] =='-' and
              buy_df['status'].iloc[i]==sell_df['status'].iloc[k] and str(orderid) in sell_df['ordertag'].iloc[k]):
            buy_df['Sell'].iloc[i]=sell_df['price'].iloc[k]
            buy_df['Exit Time'].iloc[i]=sell_df['updatetime'].iloc[k]
            buy_df['Sell Indicator'].iloc[i]=sell_df['ordertag'].iloc[k]
            buy_df['Trade Status'].iloc[i]='Closed'; sell_df['Remark'].iloc[k]='Taken'
            break
    for i in range(0,len(buy_df)):
      symbol=buy_df['tradingsymbol'].iloc[i]
      updatetime=buy_df['updatetime'].iloc[i]
      orderid=buy_df['orderid'].iloc[i]
      if buy_df['Trade Status'].iloc[i]=='Pending':
        for j in range(0,len(sell_df)):
          if (sell_df['tradingsymbol'].iloc[j]==symbol and sell_df['updatetime'].iloc[j] >= updatetime and sell_df['Remark'].iloc[j] =='-' and
              buy_df['status'].iloc[i]==sell_df['status'].iloc[j]):
            buy_df['Sell'].iloc[i]=sell_df['price'].iloc[j]
            buy_df['Exit Time'].iloc[i]=sell_df['updatetime'].iloc[j]
            buy_df['Sell Indicator'].iloc[i]=sell_df['ordertag'].iloc[j]
            buy_df['Trade Status'].iloc[i]='Closed'; sell_df['Remark'].iloc[j]='Taken'
            break
    buy_df=get_profit_loss(buy_df)
    buy_df=check_target_sl(buy_df)
    todays_trade_log=buy_df[['updatetime','tradingsymbol','producttype','price','quantity','ordertag','Sell','Target','Stop Loss','LTP','Trade Status',
                            'Profit','Exit Time','Sell Indicator']]
    todays_trade_log=todays_trade_log.sort_values(by = ['Trade Status', 'updatetime'], ascending = [False, True], na_position = 'first')
    update_todays_trade(todays_trade_log)
    return todays_trade_log
  except Exception as e:
    logger.exception(f"Error in todays_trade_log: {e}")
    pass
def update_app():
  try:
    log_holder.empty()
    with log_holder.container():
      st.write(f"Log: {datetime.datetime.now(tz=gettz('Asia/Kolkata')).replace(microsecond=0, tzinfo=None).time()}",unsafe_allow_html=True)
      st.dataframe(pd.DataFrame.from_dict(st.session_state['options_trade_list']),hide_index=True)
    orderbook=update_order_book()
    update_position()
    get_todays_trade(orderbook)
    print_ltp()
  except:
    pass
if nf_ce: manual_buy("NIFTY",'CE',st.session_state['Nifty'])
if bnf_ce: manual_buy("BANKNIFTY",'CE',st.session_state['BankNifty'])
if nf_pe: manual_buy("NIFTY",'PE',st.session_state['Nifty'])
if bnf_pe: manual_buy("BANKNIFTY",'PE',st.session_state['BankNifty'])

if algo_state:
  now_time=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
  intradayclose = now_time.replace(hour=20, minute=50, second=0, microsecond=0)
  marketopen = now_time.replace(hour=9, minute=19, second=0, microsecond=0)
  marketclose = now_time.replace(hour=20, minute=30, second=0, microsecond=0)
  while True:
    try:
      now_time=datetime.datetime.now(tz=gettz('Asia/Kolkata'))
      last_login.text(f"Login: {st.session_state['login_time']} Algo: {st.session_state['algo_running']} Last run : {now_time.time()}")
      if now_time>marketopen and now_time < intradayclose:
        if now_time.minute%5==0:
          st.session_state['options_trade_list']=[]
          if "IDX:5M" in time_frame:
            bnf_5m_trade=index_trade('BANKNIFTY','5m')
            nf_5m_trade=index_trade('NIFTY','5m')
          if "OPT:5M" in time_frame:
            near_option_trade('5m')
        if now_time.minute%15==0:
          if "IDX:15M" in time_frame:
            bnf_15m_trade=index_trade('BANKNIFTY','15m')
            nf_15m_trade=index_trade('NIFTY','15m')
        st.session_state['algo_running']="Market Open"
      elif now_time>marketopen and now_time < marketclose:
        st.session_state['algo_running']="Intraday Market Closed"
      else:
        st.session_state['algo_running']="Market Closed"
      update_app()
      get_near_option_list()
      time.sleep(61-datetime.datetime.now(tz=gettz('Asia/Kolkata')).second)
    except Exception as e:
      logger.exception(f"Error in main loop: {e}")
      print(e)

update_app()
if restart:
  for key in st.session_state.keys():
    del st.session_state[key]
  st.rerun()
