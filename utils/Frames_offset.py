#!/usr/bin/env python3
"""
Batch REDline converter:
Converts all .R3D files in a folder to half-resolution TIFF sequences
using Catmull-Rom interpolation.
"""

import os
import subprocess
from pathlib import Path
import argparse
import csv
import glob

import cv2
import numpy as np

# ========== 用户配置区 ==========
parser = argparse.ArgumentParser("ZERO-TIG")
parser.add_argument('--input_dir', type=str, default=r"")
parser.add_argument('--out_dir', type=str, default=r"")
parser.add_argument('--iso', default=800, type=int)
parser.add_argument('--REDLINE_CMD', type=str, default='REDline')
parser.add_argument('--fps', type=int, default=25)

args = parser.parse_args()

# ========== 功能函数 ==========

def process_r3d_file(r3d_path: Path):
    """调用 REDline 处理单个 R3D 文件"""
    basename = r3d_path.name
    Abs_TC = None

    # # 输出文件名前缀
    # out_prefix = str(out_dir / "frame_")

    # REDline 命令
    cmd = [
        args.REDLINE_CMD,
        "--i", str(r3d_path),
        "--useMeta",
        "--printMeta", "1"
    ]

    print(f"Processing: {r3d_path.name}")
    print("Command:", " ".join(cmd))

    try:
        results = subprocess.run(cmd, capture_output=True, text=True)
        for line in results.stdout.splitlines():
            if line.strip().startswith("Abs TC"):
                print(f"Abs TC: {line}")
                Abs_TC = line
    except subprocess.CalledProcessError as e:
        print(e)

    return Abs_TC


def batch_process():
    """批量处理输入文件夹中的所有 R3D 文件"""
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input path doesn't exist: {input_dir}")
    video_folders = sorted(input_dir.glob("*.RDC"))
    if not video_folders:
        print("No .RDC file found.")
        return


    #  文件
    save_path = os.path.join(args.out_dir, 'Abs_TC.txt')
    output_file = open(save_path, 'w')

    for video_folder in video_folders:
        video_path = Path(video_folder)
        r3d_files = sorted(video_path.glob("*.R3D"))
        if not r3d_files:
            print("No .R3D file found.")
            return

        print(f"Find {len(r3d_files)} R3D Files")
        text_line = process_r3d_file(r3d_files[0])

        output_file.write(text_line)
        output_file.write("\n")

    output_file.close()



def compute_offset(normal_file, low_file):
    output_path = os.path.join(args.out_dir, 'Offset_TC_004.txt')
    output_file = open(output_path, 'w')
    output_file.write("Normal_offset\tLow_offset\n")

    normal_offset = 0
    low_offset = 0

    with open(normal_file, 'r') as f:
        normal_lines = f.readlines()
    with open(low_file, 'r') as f:
        low_lines = f.readlines()

    assert len(normal_lines) == len(low_lines)

    for idx in range(len(normal_lines)):
        normal_line = normal_lines[idx]
        low_line = low_lines[idx]
        normal_list = [int(x) for x in normal_line.split(':')[-3:]]
        low_list = [int(x) for x in low_line.split(':')[-3:]]

        # compute offset
        diff_list = list(np.array(normal_list) - np.array(low_list))
        diff = diff_list[0]*60*args.fps + diff_list[1]*args.fps + diff_list[2]
        if diff < 0:
            normal_offset = -diff
            low_offset = 0
        else:
            normal_offset = 0
            low_offset = diff

        output_file.write(f"{normal_offset}\t{low_offset}\n")

    output_file.close()
    return normal_offset, low_offset

def select_frms():
    data_dir = Path(r"/data1/Dataset/Esprit")
    offset_file_path = data_dir / "Offset_TC_003.txt"
    low_dir = data_dir / "Low_light/B003"
    normal_dir = data_dir / "Normal_light/A003"
    save_dir = r"../data/"

    with open(offset_file_path, 'r') as f:
        offset_lines = f.readlines()
    offsets = []
    for line in offset_lines[1:]:
        offset = line.strip().split("\t")
        offsets.append([int(x) for x in offset])

    normal_videos = os.listdir(normal_dir)
    normal_videos.sort()
    low_videos = os.listdir(low_dir)
    low_videos.sort()
    for idx in range(len(offsets)):
        normal_offset, low_offset = offsets[idx]
        save_path = os.path.join(save_dir, str(normal_dir)[-3:]+"_"+str(idx+1).zfill(3))
        print(save_path)
        os.makedirs(save_path, exist_ok=True)
        if normal_offset > 100 or low_offset > 100:
            continue

        normal_video = normal_videos[idx]
        normal_img_name = "_".join(normal_video.split("_")[:-1])+"."+str(normal_offset).zfill(6)+".tif"
        normal_img_path = os.path.join(normal_dir, normal_video, normal_img_name)
        normal_img = cv2.imread(normal_img_path)
        cv2.imwrite(os.path.join(save_path, "normal_light.png"), normal_img)

        low_video = low_videos[idx]
        low_img_name = "_".join(low_video.split("_")[:-1]) + "." + str(low_offset).zfill(6) + ".tif"
        low_img_path = os.path.join(low_dir, low_video, low_img_name)
        low_img = cv2.imread(low_img_path)
        low_img = low_img[:, ::-1, :]
        cv2.imwrite(os.path.join(save_path, "low_light.png"), low_img)
        print(normal_img_path, low_img_path)



if __name__ == "__main__":
    # batch_process()

    # normal_file = Path(r"/data1/Dataset/Esprit/Normal_light/Abs_TC_004.txt")
    # low_file = Path(r"/data1/Dataset/Esprit/Low_light/Abs_TC_004.txt")
    # compute_offset(normal_file, low_file)

    select_frms()