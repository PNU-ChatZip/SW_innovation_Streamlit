from folium.map import Marker
from streamlit_folium import st_folium

import streamlit as st
import folium
from datetime import datetime
from folium import IFrame

import pandas as pd
import random

from geopy.geocoders import Nominatim

def geocoding_reverse(lat_lng_str): 
    geolocoder = Nominatim(user_agent = 'South Korea', timeout=None)
    address = geolocoder.reverse(lat_lng_str)

    return address

# 부산의 구 리스트
busan_districts = [
    '중구', '서구', '동구', '영도구', '부산진구', '동래구', '남구', '북구',
    '해운대구', '사하구', '금정구', '강서구', '연제구', '수영구', '사상구'
]
districts_centers = {
    '중구': (35.10321667, 129.0345083),
    '서구': (35.09483611, 129.022010),
    '동구': (35.13589444, 129.059175),
    '영도구': (35.08811667, 129.0701861),
    '부산진구': (35.15995278, 129.0553194),
    '동래구': (35.20187222, 129.0858556),
    '남구': (35.13340833, 129.0865),
    '북구': (35.19418056, 128.992475),
    '해운대구': (35.16001944, 129.1658083),
    '사하구': (35.10142778, 128.9770417),
    '금정구': (35.24007778, 129.0943194),
    '강서구': (35.20916389, 128.9829083),
    '연제구': (35.17318611, 129.082075),
    '수영구': (35.14246667, 129.115375),
    '사상구': (35.14946667, 128.9933333)
}


# 샘플 데이터 생성
sample_data = {
    'category': ['교통사고', '교통체증', '포트홀'],
    'date': pd.date_range(start="2023-01-01", periods=100, freq='D').to_pydatetime().tolist(),
    'district': random.choices(busan_districts, k=100),
    'description': ['사고 발생', '체증 심함', '포트홀 발생'],
    'location': [(random.uniform(35.05, 35.20), random.uniform(128.97, 129.15)) for _ in range(100)]
}

if 'init_data_loaded' not in st.session_state:
    # DataFrame 생성
    accidents_df = pd.DataFrame({
        'category': random.choices(sample_data['category'], k=100),
        'date': random.choices(sample_data['date'], k=100),
        'district': random.choices(sample_data['district'], k=100),
        'description': random.choices(sample_data['description'], k=100),
        'location': sample_data['location']
    })
    address = geocoding_reverse('35.22055713598362, 129.08256383249707')
    print(address)
    # 세션 상태에 데이터 저장
    st.session_state['accidents_df'] = accidents_df
    st.session_state['init_data_loaded'] = True
else:
    # 세션 상태에서 데이터 로드
    accidents_df = st.session_state['accidents_df']

def get_average_center(district_names):
    latitudes = [districts_centers[district][0] for district in district_names]
    longitudes = [districts_centers[district][1] for district in district_names]
    avg_lat = sum(latitudes) / len(latitudes)
    avg_lng = sum(longitudes) / len(longitudes)
    return (avg_lat, avg_lng)

# 지도 생성 함수
def create_map(data, district_name=None):
    # 만약 특정 지역구가 선택되면 해당 지역구의 중심으로 지도 중심 설정
    if district_name and all(name in districts_centers for name in district_name):
        center_location = get_average_center(district_name)
        m = folium.Map(location=center_location, zoom_start=13.5)  # zoom level은 적절히 조정
    else:
        m = folium.Map(location=[35.15, 129.05], zoom_start=11)

    for _, accident in data.iterrows():
        iframe = folium.IFrame(html=f"""
        <div style="font-family: Arial; text-align: center;">
            <h4>{accident['category']} 사고</h4>
            <hr style="margin: 1px;">
            <p><strong>날짜:</strong> {accident['date'].strftime('%Y-%m-%d')}</p>
            <p><strong>시군구:</strong> {accident['district']}</p>
            <p><strong>설명:</strong> {accident['description']}</p>
        </div>
        """, width=200, height=200)
        popup = folium.Popup(iframe, max_width=2650)
        folium.Marker(
            location=accident['location'],
            popup=popup,
            tooltip=f"{accident['category']} - {accident['date'].strftime('%Y-%m-%d')}"
        ).add_to(m)
    return m

def filter_accidents():
    date_filter = st.session_state['date_range'] if len(st.session_state['date_range']) == 2 else None
    current_category = st.session_state['category_select_key']
    current_districts = st.session_state['districts_select_key']
    
    if current_category and current_districts:
        if date_filter:
            return accidents_df[
                (accidents_df['category'] == current_category if current_category != '전체' else True) &
                (accidents_df['date'].between(date_filter[0], date_filter[1])) &
                (accidents_df['district'].isin(current_districts))
            ]
        else:
            return accidents_df[
                (accidents_df['category'] == current_category if current_category != '전체' else True) &
                (accidents_df['district'].isin(current_districts))
            ]
    else:
        return pd.DataFrame()

# 사이드바 설정
st.sidebar.title("사고 검색 옵션")
category = st.sidebar.selectbox(
    '사고 카테고리',
    options=['전체'] + sample_data['category'],
    key='category_select_key',
    on_change=filter_accidents
)

# 날짜 범위 선택
if 'date_range' not in st.session_state:
    st.session_state['date_range'] = []

st.session_state['date_range'] = st.sidebar.date_input(
    '날짜 범위 선택',
    [],
    key='date_range_key',
    on_change=filter_accidents
)

# 시군구 선택
selected_districts = st.sidebar.multiselect(
    '시군구 선택',
    options=busan_districts,
    default=busan_districts,
    key='districts_select_key',
    on_change=filter_accidents
)

# CSS를 사용하여 사이드바의 너비를 조정
st.markdown(
    """
    <style>
    .css-1d391kg {
        width: 350px; /* 원하는 너비로 설정 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 사이드바에 데이터프레임을 표시
df = pd.DataFrame({'A': [1, 2, 3, 4], 'B': [5, 6, 7, 8]})
st.sidebar.dataframe(df)

st.markdown(
    """
    <script>
        const sidebar = window.parent.document.querySelector('.sidebar .sidebar-collapse-control');
        if (sidebar) {
            sidebar.click();
        }
    </script>
    """,
    unsafe_allow_html=True
)

filtered_data = filter_accidents()
map_fig = create_map(filtered_data, district_name=st.session_state['districts_select_key'])

st_folium(map_fig, width=725)

