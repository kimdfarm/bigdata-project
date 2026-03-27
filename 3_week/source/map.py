import streamlit as st
import pandas as pd
import numpy as np
st.subheader('지도 (st.map)')
map_data= pd.DataFrame(

    np.random.randn(200,2) / [50,50] +[37.5665 , 126.9780],columns=['lat','lon']

)
st.map(map_data)