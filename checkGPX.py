import gpxpy
from fitparse import FitFile
def read_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                data = {
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'elevation': point.elevation,
                    'time': point.time
                }

                # 添加扩展数据，如功率
                if point.extensions:
                    for child in point.extensions[0]:
                        data[child.tag] = child.text

                print(data)

# 调用函数读取 GPX 文件
# 替换 'your_file.gpx' 为你的 GPX 文件路径
read_gpx('Lunch_Ride.gpx')
