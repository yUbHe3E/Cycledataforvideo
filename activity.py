import json
import numpy as np
from scipy.interpolate import interp1d
import constant
import numpy as np
from datetime import timedelta
from videoinformation import informations


def gpx_attribute_map(filename="gpx_attribute_map.json"):
    with open(filename, "r") as file:
        return json.load(file)


class FitActivity:
    def __init__(self, file_path, template_filename, video_filename):
        self.speed = []
        self.heartrate = []
        self.power = []
        self.cadence = []
        self.position_lat = []
        self.position_lon = []
        self.gradient = []
        self.time_stamp = []
        self.elevation = []
        self.course = []

        self.valid_attributes = ['speed', 'heartrate', 'power', 'cadence', 'gradient', 'course', 'elevation']#, 'time_stamp', 'position_lat', 'position_lon',]
        self.template_filename = template_filename
        self.video_filename = video_filename
        self.get_data(file_path)


    def get_data(self, file_path, time_offset_hours=9):
        from fitparse import FitFile
        from datetime import timedelta
        fitfile = FitFile(file_path)
        last_altitude = None
        last_distance = 0
        last_lat = None
        last_lon = None
        last_time = None

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

            # if None in [altitude_data, position_lat_data, position_long_data, distance_data]:
            #     continue  # 如果任何关键数据缺失，跳过当前记录

                # 如果这是第一次迭代，只记录数据
            if last_altitude is None:
                last_altitude, last_distance, last_lat, last_lon = altitude_data, distance_data, position_lat_data, position_long_data
                continue
            if position_lat_data is not None and position_long_data is not None:
                self.course.append((position_lat_data, position_long_data))

            # 计算两点之间的水平距离和高度变化
            delta_altitude = altitude_data - last_altitude
            delta_distance = distance_data - last_distance
            # if speed_data is not None and timestamp_data is not None and delta_distance > 0:
                # 应用时间偏移
            corrected_time = timestamp_data + timedelta(hours=time_offset_hours)
            if delta_distance == 0:
                gradient = 0
            else:
                gradient = (delta_altitude / delta_distance) * 100
            self.speed.append(speed_data)
            self.heartrate.append(heartrate_data)
            self.power.append(power_data)
            self.cadence.append(cadence_data)
            self.gradient.append(gradient)
            self.position_lon.append(position_long_data)
            self.position_lat.append(position_lat_data)
            self.time_stamp.append(corrected_time)
            self.elevation.append(altitude_data)
                # 更新前一个点的数据
            last_altitude, last_distance, last_time = altitude_data, distance_data, timestamp_data
        # 插入时间
        self.check_and_supplement_data()

        video_start, video_end, width, height = informations(self.video_filename)
        print(video_start, video_end, width, height)
        start_point = int((video_start - self.time_stamp[0]).total_seconds() + 1)
        end_point = int((video_end - self.time_stamp[0]).total_seconds() + 1)
        print(start_point, end_point)
        # 加载 JSON 文件
        with open('templates/' + self.template_filename, 'r') as file:
            config = json.load(file)
        # 修改配置值
        config['scene']['start'] = start_point  # 设置实际的开始时间
        config['scene']['end'] = end_point  # 设置实际的结束时间
        config['scene']['width'] = int(width)  # 设置实际的视频宽度
        config['scene']['height'] = int(height)  # 设置实际的视频高度
        # 写回 JSON 文件
        with open('templates/' + self.template_filename, 'w') as file:
            json.dump(config, file, indent=4)

    def interpolate(self, fps: int):
        def helper(data):
            data.append(2 * data[-1] - data[-2])
            x = np.arange(len(data))
            interp_func = interp1d(x, data)
            new_x = np.arange(x[0], x[-1], 1 / fps)
            return interp_func(new_x).tolist()

        for attribute in self.valid_attributes:
            if attribute in constant.NO_INTERPOLATE_ATTRIBUTES:
                continue
            data = getattr(self, attribute)
            if attribute == constant.ATTR_COURSE:
                new_lat = helper([ele[0] for ele in data])
                new_lon = helper([ele[1] for ele in data])
                new_data = list(zip(new_lat, new_lon))
            else:
                new_data = helper(data)
            setattr(self, attribute, new_data)

    def trim(self, start, end):
        for attribute in self.valid_attributes:
            data = getattr(self, attribute)
            if start > len(data):
                print(
                    f"invalid scene start value in config. Value should be less than {len(data)}. Current value is {start}"
                )
                exit(1)
            if end > len(data) or end < start:
                print(
                    f"invalid scene end value in config. Value should be less than {len(data)} and greater than {start}. Current value is {end}"
                )
                exit(1)
            setattr(self, attribute, data[start:end])

    def check_and_supplement_data(self):
        # 计算时间戳之间的间隔
        intervals = np.diff(self.time_stamp).astype('timedelta64[s]').astype(int)
        supplement_points = []

        # 收集需要补充数据的点和间隔数量
        for i in range(1, len(self.time_stamp)):
            if intervals[i - 1] > 1:
                supplement_points.append((i, intervals[i - 1]))

        # 从后向前补充数据，以避免索引偏移
        for index, interval in reversed(supplement_points):
            self.supplement_data_at(index, interval)

    def supplement_data_at(self, index, interval):
        num_points_to_insert = interval - 1

        # 特殊处理时间戳
        start_time = self.time_stamp[index - 1]
        interpolated_times = [start_time + timedelta(seconds=i) for i in range(1, num_points_to_insert + 1)]

        # 将时间戳插入到 self.time_stamp 中
        self.time_stamp[index:index] = interpolated_times

        # 对心率进行线性插值，如果心率数据存在
        if self.heartrate[index - 1] is not None and self.heartrate[index] is not None:
            start_hr = self.heartrate[index - 1]
            end_hr = self.heartrate[index]
            interpolated_hrs = np.linspace(start_hr, end_hr, num_points_to_insert + 2)[1:-1]
        else:
            interpolated_hrs = [0] * num_points_to_insert  # 如果心率数据缺失，则用0填充
        self.heartrate[index:index] = interpolated_hrs

        # 对速度、踏频、功率设置为0
        for attr in ['speed', 'cadence', 'power']:
            attr_list = getattr(self, attr)
            attr_list[index:index] = [0] * num_points_to_insert

        # 坡度和位置可以选择保持前一个值，或者执行其他逻辑
        for attr in ['gradient', 'position_lat', 'position_lon']:
            attr_list = getattr(self, attr)
            if attr_list[index - 1] is not None:
                attr_list[index:index] = [attr_list[index - 1]] * num_points_to_insert
            else:
                attr_list[index:index] = [0] * num_points_to_insert  # 或者用其他逻辑填充

        # 海拔数据可以保持前一个值，或者根据需要进行插值或填充
        if self.elevation[index - 1] is not None and self.elevation[index] is not None:
            start_elevation = self.elevation[index - 1]
            end_elevation = self.elevation[index]
            interpolated_elevations = np.linspace(start_elevation, end_elevation, num_points_to_insert + 2)[1:-1]
        else:
            interpolated_elevations = [0] * num_points_to_insert  # 如果海拔数据缺失，则用0填充
        self.elevation[index:index] = interpolated_elevations

