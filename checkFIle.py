from fitparse import FitFile
from datetime import timedelta
def get_data(file_path, time_offset_hours=9):
    # 加载 .fit 文件
    fitfile = FitFile(file_path)
    # 初始化变量以存储前一个点的数据
    last_altitude = None
    last_distance = 0
    last_lat = None
    last_lon = None
    last_time = None
    # 遍历文件中的所有记录（每个时间点的数据）
    for record in fitfile.get_messages('record'):
        # 获取记录的速度和时间戳
        speed_data = record.get_value('enhanced_speed')
        power_data = record.get_value('power')
        heartrate_data = record.get_value('heart_rate')
        cadence_data = record.get_value('cadence')
        altitude_data = record.get_value('enhanced_altitude')
        position_lat_data = record.get_value('position_lat')
        position_long_data = record.get_value('position_long')
        distance_data = record.get_value('distance')  # 距离单位为米

        timestamp_data = record.get_value('timestamp')

        if None in [altitude_data, position_lat_data, position_long_data, distance_data]:
            continue  # 如果任何关键数据缺失，跳过当前记录

            # 如果这是第一次迭代，只记录数据
        if last_altitude is None:
            last_altitude, last_distance, last_lat, last_lon = altitude_data, distance_data, position_lat_data, position_long_data
            continue
        # 计算两点之间的水平距离和高度变化
        delta_altitude = altitude_data - last_altitude
        delta_distance = distance_data - last_distance
        if speed_data is not None and timestamp_data is not None and delta_distance > 0:

            # 应用时间偏移
            corrected_time = timestamp_data + timedelta(hours=time_offset_hours)
            # 打印修正后的时间和速度
            # print(f"Time: {corrected_time}, Speed: {speed} m/s")
            # print(f'Time: {corrected_time}, Power: {power} W')
            # print(f'Time: {corrected_time}, Heart Rate: {heartrate}')
            # print(f'Time: {corrected_time}, Cadence: {cadence}')
            # print(f'Time: {corrected_time}, Altitude: {altitude}')
            gradient = (delta_altitude / delta_distance) * 100  # 坡度百分比
            # print(f"Time: {last_time} to {timestamp}, Distance: {last_distance} to {distance} m, Gradient: {gradient:.2f}%")

            speed.append(speed_data)
            heartrate.append(heartrate_data)
            power.append(power_data)
            cadence.append(cadence_data)
            gradient.append(gradient)
            position_lon.append(position_long_data)
            position_lat.append(position_lat_data)
            time_stamp.append(corrected_time)
        # 更新前一个点的数据
        last_altitude, last_distance, last_time = altitude_data, distance_data, timestamp_data

speed_list = []
heartrate_list = []
power_list = []
cadence_list = []
position_lat_list = []
position_lon_list = []
gradient_list =[]
time_stamp_list = []

get_data('Morning_Ride.fit')