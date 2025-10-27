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
import cv2
from glob import glob
from PIL import Image

# ========== 用户配置区 ==========
parser = argparse.ArgumentParser("ZERO-TIG")
parser.add_argument('--input_dir', type=str, default=r"")
parser.add_argument('--out_dir', type=str, default=r"")
parser.add_argument('--iso', default=800, type=int)
parser.add_argument('--REDLINE_CMD', type=str, default='REDline')

args = parser.parse_args()

# ========== 功能函数 ==========

def process_r3d_file(r3d_path: Path, output_dir, ISO, is_flip=False):
    """调用 REDline 处理单个 R3D 文件"""
    basename = r3d_path.stem
    basename = "_".join(basename.split("_")[:-1])
    out_dir = Path(output_dir) / basename
    out_dir.mkdir(parents=True, exist_ok=True)

    # # 输出文件名前缀
    # out_prefix = str(out_dir / "frame_")

    # REDline 命令
    cmd = [
        args.REDLINE_CMD,
        "--i", str(r3d_path),
        "--outDir", str(out_dir),
        "--format", "1",              # 1 = TIFF
        "--iso", str(ISO),
        "--NR", "0",                  # 关闭降噪
        "--resizeX", "4096",            # 下采样 1/2
        "--resizeY", "2160",            # 下采样 1/2
        "--filter", "5",              # Catmull-Rom
        "--decodeThreads", "8",    # 全质量解码
        # "--useRMD", "1",              # 使用相机元数据
        # "--pipeline", "PrimaryDevelopment"  # 只做 debayer，不做 IPP2 处理
        # "--frameCount", "60",
        "--forceFlipHorizontal", str(int(is_flip))
    ]

    print(f"Processing: {r3d_path.name}")
    print("Command:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print(f"Done: {basename}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {r3d_path.name}: {e}")


# def sort_files(r3d_files):
#     idx_dict = []
#     for r3d_file in r3d_files:
#         file_name = os.path.basename(r3d_file).split(".")[0]
#         idx = int(file_name.split("_")[-1])
#         idx_dict.append((idx, r3d_file))
#
#     sorted_idx = sorted(idx_dict, key=lambda x: x[0])
#     return sorted_idx


def batch_process(input_dir, output_dir, ISO, is_flip=False):
    """批量处理输入文件夹中的所有 R3D 文件"""
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input path doesn't exist: {input_dir}")
    video_folders = sorted(input_dir.glob("*.RDC"))
    if not video_folders:
        print("No .RDC file found.")
        return
    for video_folder in video_folders:
        video_path = Path(video_folder)
        r3d_files = sorted(video_path.glob("*.R3D"))
        if not r3d_files:
            print("No .R3D file found.")
            return

        print(f"Find {len(r3d_files)} R3D Files")
        for f in r3d_files:
            process_r3d_file(f, output_dir, ISO, is_flip)
            break


def single_process():
    """批量处理输入文件夹中的所有 R3D 文件"""
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"Input path doesn't exist: {input_dir}")

    r3d_files = sorted(input_dir.glob("*.R3D"))
    if not r3d_files:
        print("No .R3D file found.")
        return

    print(f"Find {len(r3d_files)} R3D Files")
    for f in r3d_files:
        process_r3d_file(f)
        break

def rename_lists(name_lists:list, offset):
    name_lists.sort()
    name_lists = name_lists[offset:]

    for i in range(len(name_lists)):
        frm_path = name_lists[i]
        parent, frm_name = os.path.split(frm_path)
        frm_basic, frm_old_idx, frm_suffix = frm_name.split(".")
        frm_new_idx = str(i).zfill(6)
        frm_new_basename = ".".join([frm_basic, frm_new_idx, frm_suffix])

        old_path = Path(frm_path)
        new_path = Path(os.path.join(parent, frm_new_basename))
        old_path.rename(new_path)


def get_subdirectories_walk(root_dir):
    subdirs = []

    try:
        if not os.path.exists(root_dir):
            print(f"Wrong: '{root_dir}' does not exist.")
            return []

        # 使用os.walk遍历目录树
        for root, dirs, files in os.walk(root_dir):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                abs_path = os.path.abspath(dir_path)
                subdirs.append(abs_path)

        return subdirs

    except Exception as e:
        print(f"Wrong folder: {e}")
        return []

def frms_post_processing(normal_dir, low_dir, offset_file_path):

    with open(offset_file_path, 'r') as f:
        offset_lines = f.readlines()
    offsets = []
    for line in offset_lines[1:]:
        offset = line.strip().split("\t")
        offsets.append([int(x) for x in offset])

    normal_videos = get_subdirectories_walk(normal_dir)
    normal_videos.sort()
    low_videos = get_subdirectories_walk(low_dir)
    low_videos.sort()
    for idx in range(len(offsets)):
        video_idx, normal_offset, low_offset = offsets[idx]
        # save_path = os.path.join(save_dir, str(normal_dir)[-3:]+"_"+str(idx+1).zfill(3))
        # print(save_path)
        # os.makedirs(save_path, exist_ok=True)
        if normal_offset > 100 or low_offset > 100:
            print(f"Skipping {normal_offset}-{low_offset}")
            continue


        normal_video_dir = normal_videos[idx]
        print(f"Processing: {normal_video_dir}")
        normal_img_lists = glob(os.path.join(normal_video_dir, "*.tif"))
        rename_lists(normal_img_lists, normal_offset)


        low_video_dir = low_videos[idx]
        print(f"Processing: {low_video_dir}")
        low_img_lists = glob(os.path.join(low_video_dir, "*.tif"))
        rename_lists(low_img_lists, low_offset)


if __name__ == "__main__":
    """Step 1"""
    # ISO = 12800 # 800 for normal light, 12800 for low light
    low_input_dir = r"/data2/B003"
    low_output_dir = r"/data1/Dataset/Esprit/Video_frames/Low_light"
    batch_process(low_input_dir, low_output_dir, 12800, is_flip=True)

    normal_input_dir = r"/data2/A003"
    normal_output_dir = r"/data1/Dataset/Esprit/Video_frames/Normal_light"
    batch_process(low_input_dir, low_output_dir, 800, is_flip=False)

    """Step 2 Rename img"""
    # data_dir = Path(r"/data1/Dataset/Esprit/Video_frames")
    # offset_file_path = Path(r"/data1/Dataset/Esprit/Offset_TC_003.txt")
    # low_dir = Path(r"/data1/Dataset/Esprit/Video_frames/Low_light")
    # normal_dir = Path(r"/data1/Dataset/Esprit/Video_frames/Normal_light")
    # frms_post_processing(normal_dir, low_dir, offset_file_path)
