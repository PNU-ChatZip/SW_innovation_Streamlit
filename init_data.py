import random
import pandas as pd

acc_dict = {'차량 사고':'accident', '도로 막힘':'traffic_jam', '포트홀':'forthole'}
status_description = {'finished':'완료', 'checked':'처리중', 'discovered':'발견'}
status_dict = {'발견':'discovered','처리중':'checked','완료':'finished'}   

category_icon_map = {
        '차량 사고': 'car',
        '도로 막힘': 'hourglass-half',
        '포트홀': 'wrench'
    }
category_color_map = {
    '차량 사고': 'red',
    '도로 막힘': 'orange',
    '포트홀': 'blue'
}
status_opacity_map = {
    'finished': 0.4,     # 완료 상태는 불투명
    'checked': 0.7,      # 확인 상태는 중간 투명도
    'discovered': 1.0    # 발견 상태는 높은 투명도
}

# 대구의 구 리스트
daegu_districts = [
    '중구','동구','서구','남구','북구','수성구','달서구','달성군','군위군'
]
districts_centers = {
    '달서구': (35.82845261, 128.53382715),  # 달서구의 두 좌표의 평균값
    '수성구': (35.856779905, 128.6317839),  # 수성구의 두 좌표의 평균값
    '남구': (35.84621351, 128.597702),  # 남구의 좌표
    '달성군': (35.77475029, 128.4313995),  # 달성군의 좌표
    '군위군' : (36.1530284, 128.6493142),
    '동구': (35.88682728, 128.6355584),  # 동구의 좌표
    '북구': (35.8858646, 128.5828924),  # 북구의 좌표
    '서구': (35.87194054, 128.5591601),  # 서구의 좌표
    '중구': (35.86952722, 128.6061745)  # 중구의 좌표
}

districts_data = {
        '중구':['27110'],
        '동구':['27140'],
        '서구':['27170'],
        '남구':['27200'],
        '북구':['27230'],
        '수성구':['27260'],
        '달서구':['27290'],
        '달성군':['27710'],
        '군위군':['27720']
}
process_types = ['discovered', 'checked', 'finished']
data_categories = ['차량 사고', '도로 막힘', '포트홀']
data_descriptions = ['사고 발생', '체증 심함', '포트홀 발생']
detail_locations_base = ['대구광역시 중구 대청동 1-', '대구광역시 중구 대청동 2-', '대구광역시 중구 대청동 3-']

def get_sample_data(seed,n):   
    random.seed(seed)
    num_items = n

    # Shuffle types, categories, and descriptions for each item
    types = random.choices(process_types, k=num_items)
    categories = random.choices(data_categories, k=num_items)
    descriptions = random.choices(data_descriptions, k=num_items)

    # Create detailed locations with random numbering
    detail_locations = [base + str(random.randint(1, 100)) for base in random.choices(detail_locations_base, k=num_items)]

    # Generate random locations around Daegu's coordinates
    locations = [(random.uniform(35.8, 35.95), random.uniform(128.5, 128.7)) for _ in range(num_items)]

    # Create the sample_data dictionary
    sample_data = {
        'id': list(range(1, num_items + 1)),
        'type': types,
        'category': categories,
        'date': pd.date_range(start="2023-01-01", periods=num_items, freq='W').tolist(),
        'district': random.choices(daegu_districts, k=num_items),
        'description': descriptions,
        'detail_location': detail_locations,
        'location': locations
    }

    return pd.DataFrame(sample_data)
