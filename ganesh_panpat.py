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
  
