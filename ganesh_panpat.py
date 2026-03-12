import streamlit as st
import numpy
import requests
import datetime
from dateutil.tz import gettz
import pandas as pd
from SmartApi.smartConnect import SmartConnect
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
