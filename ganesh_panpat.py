import streamlit as st
import numpy
import requests
import datetime
from dateutil.tz import gettz
import pandas as pd
from SmartApi import SmartConnect
import pyotp
from logzero import logger
import warnings
import time
import re
import yfinance as yf
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
login_details.text(f"Welcome:{st.session_state['Logged_in']} Login:{st.session_state['login_time']} Last Check:{st.session_state['last_check']}")
log_tb, order_tb, position_tb, open_odr_tb, setting_tb, token_tb, stk_token_tb, near_opt_tb= st.tabs(["Log","Order Book", "Position",
                "Open Order", "Settings","Token List","Stock List",'Near Options'])
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
    fut_list=st.multiselect('Select Future',['TCS','SBIN','RELIANCE','SAIL','TRENT','HDFCBANK'],['TCS','SBIN','RELIANCE','SAIL','TRENT','HDFCBANK'])
    time_frame_interval = st.multiselect('Select Time Frame',['IDX:5M','IDX:15M','IDX:1M','OPT:5M','OPT:1M','GTT:5M','STK:5M'],['IDX:5M','OPT:5M','STK:5M'])
    five_buy_indicator = st.multiselect('5M Indicator',indicator_list,['ST_7_3 Trade'])
    five_opt_buy_indicator = st.multiselect('5M OPT Indicator',indicator_list,['ST_7_3 Trade'])
    five_stk_buy_indicator = st.multiselect('5M STK Indicator',indicator_list,['MA_50_ST Trade','ST_7_3 Trade'])
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
