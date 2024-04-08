import subprocess
import re
from datetime import datetime, timedelta

def parse_duration(duration_str):
    # 将时长字符串（HH:MM:SS.ms）转换为timedelta对象
    hours, minutes, seconds = map(float, duration_str.split(':'))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def informations(video_file):
    cmd = ['ffmpeg', '-i', video_file]
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    _, stderr = process.communicate()

    # 将stderr转换为字符串
    output = stderr.decode('utf-8')

    # 使用正则表达式提取开始时间、持续时间和分辨率
    creation_time_match = re.search(r'creation_time\s+:\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', output)
    duration_match = re.search(r'Duration:\s+(\d{2}:\d{2}:\d{2}\.\d{2}),', output)
    resolution_match = re.search(r'(\d{3,})x(\d{3,})', output)

    # 解析找到的值
    creation_time = creation_time_match.group(1) if creation_time_match else 'Unknown'
    duration = parse_duration(duration_match.group(1)) if duration_match else 'Unknown'
    width, height = resolution_match.groups() if resolution_match else ('Unknown', 'Unknown')

    # 计算结束时间
    if creation_time != 'Unknown' and duration != 'Unknown':
        start_time = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
        end_time = start_time + duration
    else:
        end_time = 'Unknown'

    return datetime.fromisoformat(creation_time) + timedelta(hours=9), end_time + timedelta(hours=9), width, height

if __name__ == '__main__':
    video_file = 'test.mp4'
    start_time, end_time, width, height = informations(video_file)
    print(f"Start Time: {start_time}")
    print(f"End Time: {end_time}")
    print(f"Resolution: {width}x{height}")
