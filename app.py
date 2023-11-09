import streamlit as st
from streamlit_folium import st_folium
import streamlit.components.v1 as components

import folium
from folium.plugins import MarkerCluster

import pandas as pd
from datetime import datetime, time

import geopandas as gpd
from geopy.geocoders import Nominatim

import requests

from popup import make_popup
from chatbot import typebot_iframe_html
from init_data import daegu_districts, districts_centers, districts_data, process_types, data_categories, data_descriptions, detail_locations_base
from init_data import category_icon_map, category_color_map, status_opacity_map
from init_data import status_description, acc_dict,status_dict
from init_data import get_sample_data
from util import get_average_center
from util import get_icon_create_function
from util import to_excel

# 경고 메시지 숨기기
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(page_title="D-MAP",layout="wide")

ACCIDENT_DATA_URL = "http://waterboom.iptime.org:1101/get-locations"

def fetch_and_format_accident_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # 실제 데이터를 JSON 형태로 변환
            data = response.json()
            # JSON 데이터를 DataFrame으로 변환
            accidents_df = pd.DataFrame(data)
            # 샘플 데이터 형식에 맞추어 컬럼 변환
            formatted_df = pd.DataFrame({
                'user_id': accidents_df['userId'],
                'id' : accidents_df['id'],
                'type': accidents_df['progress'],
                'category': accidents_df['type'],  
                'date': pd.to_datetime(accidents_df['time']),  # 'time'을 datetime 형식으로 변환
                'district': accidents_df['area2'],  # 'district'는 'area2' 값 사용
                'description': accidents_df['type'],  # 'description'은 'type' 값 사용
                'detail_location': accidents_df['road'],
                'location': list(zip(accidents_df['latitude'], accidents_df['longitude']))  # 'location'은 'latitude'와 'longitude'를 튜플로 묶음
            })
            return formatted_df
        else:
            st.error("Failed to fetch data")
            return pd.DataFrame()
    except Exception as e:
        st.error(e)
        return pd.DataFrame()

def init_district_data():
    if 'page' not in st.session_state:
        st.session_state.page = 0
    
    # 날짜 범위 선택
    if 'date_range' not in st.session_state:
        st.session_state['date_range'] = []

    if 'time_range' not in st.session_state:
        st.session_state['time_range'] = (time(8, 00), time(17, 00))
    
    if 'type_filter' not in st.session_state:
        st.session_state['type_filter'] = process_types
        
    for status in process_types:
        key = f'type_filter_{status}'
        if key not in st.session_state:
            st.session_state[key] = True
            
    if 'init_data_loaded' not in st.session_state:
        # DataFrame 생성
        # accidents_df = fetch_and_format_accident_data(ACCIDENT_DATA_URL)
        # forthole_df = fetch_and_format_accident_data(FORTHOLE_DATA_URL)
        # accidents_df = pd.concat([accidents_df, forthole_df])
        
        #accidents_df = get_sample_data(0,50)
        accidents_df = fetch_and_format_accident_data(ACCIDENT_DATA_URL)
        
        EMD = gpd.read_file('LSMD_ADM_SECT_UMD_daegu\LSMD_ADM_SECT_UMD_27_202309.shp', encoding='cp949')
        st.session_state['yi4326'] = EMD.to_crs(epsg=4326)

        # 세션 상태에 데이터 저장
        st.session_state['accidents_df'] = accidents_df
        st.session_state['init_data_loaded'] = True
    else:
        # 세션 상태에서 데이터 로드
        accidents_df = st.session_state['accidents_df']
        yi4326 = st.session_state['yi4326']

# 지도 생성 함수
def create_map(data, district_name=None, marker=False):
    clusters = {}
    with st.spinner('Wait for it...'):
        # 만약 특정 지역구가 선택되면 해당 지역구의 중심으로 지도 중심 설정
        if district_name and all(name in districts_centers for name in district_name):
            center_location = get_average_center(district_name)
            m = folium.Map(location=center_location, zoom_start=13.5)  # zoom level은 적절히 조정
        else:
            m = folium.Map(location=[35.8715404, 128.6012396], zoom_start=11)
        
        if marker==1:
            clusters = {
                '차량 사고': MarkerCluster(icon_create_function=get_icon_create_function(0, 45)).add_to(m),
                '도로 막힘': MarkerCluster(icon_create_function=get_icon_create_function(30, 75)).add_to(m),
                '포트홀': MarkerCluster(icon_create_function=get_icon_create_function(220, 120)).add_to(m)
            }
            
        if district_name:
            # 각 지역구에 속하는 행정동 리스트 추출
            dong_list = []
            for district in district_name:
                dong_list.extend(districts_data.get(district, []))
            dong_geo = st.session_state['yi4326'][st.session_state['yi4326']['COL_ADM_SE'].isin(dong_list)]
            for _, row in dong_geo.iterrows():
                geojson = folium.GeoJson(
                    row['geometry'],
                    name=row['EMD_NM'],
                    style_function=lambda x: {'fillColor': 'green', 'color': 'green', 'weight': 2, 'fillOpacity': 0.1}
                )
                geojson.add_child(folium.Tooltip(row['EMD_NM']))
                geojson.add_to(m)
        
        for _, accident in data.iterrows():
            icon_color = category_color_map[accident['category']]
            icon_opacity = status_opacity_map[accident['type']]
            icon = folium.Icon(color=icon_color, icon=category_icon_map[accident['category']], prefix='fa')

            status_class = {
            'finished': 'status-complete',
            'checked': 'status-hold',
            'discovered': 'status-pending'
            }[accident['type']]
            iframe = folium.IFrame(html=make_popup(accident, status_class, status_description), width=200, height=200)
            popup = folium.Popup(iframe, max_width=2650)
            
            if marker == 1:
                data_marker = folium.Marker(
                    location=accident['location'],
                    popup=popup,
                    icon=icon,
                    tooltip=f"{accident['category']} - {accident['date'].strftime('%Y-%m-%d')}",
                    opacity=icon_opacity
                )
                clusters[accident['category']].add_child(data_marker)
            else:
                folium.Marker(
                    location=accident['location'],
                    popup=popup,
                    icon=icon,
                    tooltip=f"{accident['category']} - {accident['date'].strftime('%Y-%m-%d')}",
                    opacity=icon_opacity
                ).add_to(m)

        folium.LayerControl().add_to(m)
    return m

def filter_accidents():
    try:
        with st.spinner('Wait for it...'):
            st.session_state['accidents_df'] = fetch_and_format_accident_data(ACCIDENT_DATA_URL)
            df = st.session_state['accidents_df']
            df['time'] = df['date'].dt.time
            
            date_filter = [pd.to_datetime(date).to_pydatetime() for date in st.session_state['date_range']] if len(st.session_state['date_range']) == 2 else None
            current_category = st.session_state['category_select_key']
            current_districts = st.session_state['districts_select_key']
            current_types = st.session_state['type_filter']
            current_time_range = st.session_state['time_range']
            
            time_condition = (df['time'] >= current_time_range[0]) & (df['time'] <= current_time_range[1])
            date_condition = (df['date'] >= date_filter[0]) & (df['date'] <= date_filter[1]) if date_filter else True
            category_condition = (df['category'] == current_category) if current_category != '전체' else True
            district_condition = df['district'].isin(current_districts)
            type_condition = df['type'].isin(current_types) if current_types else False
            
            final_condition = category_condition & district_condition & type_condition & date_condition & time_condition
            df = df[final_condition].drop(columns=['time'])
            # 최종 조건을 사용하여 데이터를 필터링하고 반환합니다.
        return df

    except:
        return pd.DataFrame()

def download_excel(df):
    excel_file = to_excel(df)
    st.download_button(
        label="Excel 파일 다운로드",
        data=excel_file,
        file_name="data.xlsx",
        mime="application/vnd.ms-excel"
    )

# 체크박스 상태를 업데이트하는 함수 정의
def update_type_filter():
    st.session_state['type_filter'] = [t for t in process_types if st.session_state[f'type_filter_{t}']]
    filter_accidents()

def select_all_districts():
    st.session_state['districts_select_key'] = daegu_districts

def main():
    init_district_data()
    # 사이드바 설정
    st.sidebar.title("교통 불편 사항 검색")
    category = st.sidebar.selectbox(
        '사고 카테고리',
        options=['전체'] + data_categories,
        key='category_select_key',
        on_change=filter_accidents
    )
     # 사고 데이터에서 'type' 컬럼의 고유값을 리스트로 가져옴
    columns = st.sidebar.columns(len(status_dict))
    st.sidebar.write("진행 상태")
    # 체크박스로 필터링 옵션 추가
    for i, (status, description) in enumerate(status_dict.items()):
        with columns[i]:
            st.checkbox(status, value=st.session_state[f'type_filter_{description}'],
                    key=f'type_filter_{description}',
                    on_change=update_type_filter)

    st.session_state['date_range'] = st.sidebar.date_input(
        '날짜 범위 선택',
        [],
        key='date_range_key',
        on_change=filter_accidents
    )

    st.session_state['time_range'] = st.sidebar.slider(
    "시간대 선택",
    value=(time(8, 00), time(17, 00)),  # 기본값은 오전 8시부터 오후 5시까지
    format="HH:mm"  # 24시간 형식으로 표시
    )
    
    # 시군구 선택
    if st.sidebar.button("모든 구 선택"):
        select_all_districts()
    
    selected_districts = st.sidebar.multiselect(
        '시군구 선택',
        options=daegu_districts,
        default=daegu_districts,
        key='districts_select_key',
        on_change=filter_accidents
    )
    
    st.title(" 🌐 D - MAP")

    filtered_data = filter_accidents()
    if not filtered_data.empty:
        st.sidebar.write("선택된 시간대:", st.session_state['time_range'][0], "부터", st.session_state['time_range'][1], "까지")
        st.sidebar.write(f"검색된 데이터 : {len(filtered_data)} 개", filtered_data)
    else:
        st.sidebar.write("필터 조건에 맞는 데이터가 없습니다.")
    
    col1, col2, space, col3 = st.columns([1.2,1,2.2,2])

    # 첫 번째 열에 "전체 데이터 보기" 버튼 배치
    with col1:
        if st.button("전체 데이터 보기"):
            st.session_state.page = 0

    # 두 번째 열에 "클러스터 보기" 버튼 배치
    with col2:
        if st.button("클러스터 보기"):
            st.session_state.page = 1

    # 세 번째 열에 엑셀 다운로드 버튼 배치
    with col3:
        download_excel(filtered_data)

    map_fig = create_map(filtered_data, district_name=st.session_state['districts_select_key'],marker=st.session_state.page)

    st_folium(map_fig, width='100%')
    
    #components.html(typebot_iframe_html, height=600)

if __name__ == '__main__':
    main()