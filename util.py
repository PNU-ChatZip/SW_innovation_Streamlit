from init_data import districts_centers
from io import BytesIO
import pandas as pd

def get_average_center(district_names):
    latitudes = [districts_centers[district][0] for district in district_names]
    longitudes = [districts_centers[district][1] for district in district_names]
    avg_lat = sum(latitudes) / len(latitudes)
    avg_lng = sum(longitudes) / len(longitudes)
    return (avg_lat, avg_lng)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        # 변경된 부분: writer.save() 대신 writer.close() 사용
    processed_data = output.getvalue()

    return processed_data

def get_icon_create_function(color1, color2):
    return """
        function(cluster) {{
            var childCount = cluster.getChildCount();
            var c = 'hsl(' + Math.floor((1 - (childCount / 100)) * {color1}) + ', 100%, 50%)';
            var c2 = 'hsl(' + Math.floor((1 - (childCount / 100)) * {color2}) + ', 100%, 50%)';
            return L.divIcon({{
                html: '<div style="background: linear-gradient(to right, ' + c + ', ' + c2 + '); width: 30px; height: 30px; border-radius: 15px; line-height: 30px; text-align: center; color: #fff;">' + childCount + '</div>',
                className: 'marker-cluster-custom',
                iconSize: L.point(30, 30)
            }});
        }}
    """.format(color1=color1, color2=color2)