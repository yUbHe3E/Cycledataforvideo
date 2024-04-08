import subprocess
import sys

import inquirer

import constant
from activity import FitActivity
from scene import Scene


def render_overlay(filename, template_filename, video_filename):
    activity = FitActivity(filename, template_filename, video_filename)
    print(activity)
    scene = Scene(activity, activity.valid_attributes, template_filename)
    start, end = scene.configs["scene"]["start"], scene.configs["scene"]["end"]
    activity.trim(start, end)
    activity.interpolate(scene.fps)
    scene.build_figures()
    scene.render_video(end - start)


def demo_frame(filename, template_filename, second):
    activity = FitActivity(filename)
    scene = Scene(activity, activity.valid_attributes, template_filename)
    start, end = scene.configs["scene"]["start"], scene.configs["scene"]["end"]
    activity.trim(start, end)
    activity.interpolate(scene.fps)
    scene.build_figures()
    scene.render_demo(end - start, second)
    subprocess.call(["open", scene.frames[0].full_path()])
    return scene


# TODO improve argument handling
if __name__ == "__main__":
    filename = "Morning_Ride.fit"
    template_filename = "safa_brian_a_1280_720.json"
    video_filename = "test.MP4"
    ##添加一个时区
    # template_filename = "safa_brian_a_1280_720.json"
    if len(sys.argv) >= 2:
        if sys.argv[1] == "demo":
            second = int(sys.argv[2]) if len(sys.argv) == 3 else 0
            while True:
                print(
                    f"demoing frame using the {template_filename} template and {filename} gpx file"
                )
                scene = demo_frame(filename, template_filename, second)
                input("enter to re-render:")
                scene.update_configs(template_filename)
    print(
        f"rendering overlay using the {template_filename} template and {filename} gpx file"
    )
    render_overlay(filename, template_filename, video_filename)
