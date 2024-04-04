import subprocess
import json

def informations(video_file):
    # 调用exiftool获取视频的元数据
    process = subprocess.Popen(['exiftool', '-json', video_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    if process.returncode != 0:
        print(f"Error: {err}")
        return None

    # 解析JSON输出以获取数据
    metadata = json.loads(out)[0]

    # 查找开始和结束时间的字段可能需要根据视频文件的具体情况调整
    # 这里只是举个例子，实际字段可能有所不同
    start_time = metadata.get('CreateDate', 'Unknown')
    duration = metadata.get('Duration', 'Unknown')

    return start_time, duration,

# 使用示例
video_file = 'example.mp4'
start_time, duration = informations(video_file)
print(f"Start Time: {start_time}")
print(f"Duration: {duration}")