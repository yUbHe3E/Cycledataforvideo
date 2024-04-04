import json
import numpy as np
from scipy.interpolate import interp1d
import constant
# from videoinformation import informations


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
        self.get_data(file_path)
        self.valid_attributes = ['speed', 'heartrate', 'power', 'cadence', 'gradient', 'course', 'elevation']#, 'time_stamp', 'position_lat', 'position_lon',]
        self.template_filename = template_filename
        self.video_filename = video_filename


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


        ###检查时间一致性###
        # 计算时间戳之间的间隔
        intervals = np.diff(self.time_stamp).astype('timedelta64[s]').astype(int)

        # 检查间隔是否一致
        interval_set = set(intervals)
        if len(interval_set) == 1:
            print(f"All timestamps are evenly spaced with an interval of {intervals[0]} seconds.")
        else:
            print(f"Timestamps are not evenly spaced. Found {len(interval_set)} different intervals.")
            #查找并打印间隔不一致的时间戳
            print("Inconsistent timestamp intervals found at:")
            for i in range(1, len(intervals)):
                if intervals[i] != intervals[i - 1]:
                    print(
                        f"{i},Change at {self.time_stamp[i]}: Interval changed from {intervals[i - 1]} to {intervals[i]} seconds")
                    print(f"Speed before change", self.speed[i])
                    print(f"c before change", self.cadence[i])
        ##################这些地方自动暂停了，心率自动差值，速度踏频功率设置为0，坡度保持，路径如何处理？
        numb_of_points = len(self.speed)


        fit_start_time = self.time_stamp[0]
        fit_end_time = self.time_stamp[-1]
        print(fit_start_time, '/', fit_end_time, '/', (fit_end_time - fit_start_time).total_seconds(), '/n', self.time_stamp[100])
        # video_start_time, video_end_time, width, height = informations(self.video_filename) # add video informations from here
        #
        # # 加载 JSON 文件
        # with open(self.template_filename, 'r') as file:
        #     config = json.load(file)
        # # 修改配置值
        # config['scene']['start'] = 0  # 设置实际的开始时间
        # config['scene']['end'] = 1000  # 设置实际的结束时间
        # config['scene']['width'] = width  # 设置实际的视频宽度
        # config['scene']['height'] = height  # 设置实际的视频高度
        # # 写回 JSON 文件
        # with open(self.template_filename, 'w') as file:
        #     json.dump(config, file, indent=4)

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

