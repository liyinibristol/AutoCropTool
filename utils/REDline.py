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

# ========== 用户配置区 ==========
parser = argparse.ArgumentParser("ZERO-TIG")
parser.add_argument('--input_dir', type=str, default=r"")
parser.add_argument('--out_dir', type=str, default=r"")
parser.add_argument('--iso', default=800, type=int)
parser.add_argument('--REDLINE_CMD', type=str, default='REDline')

args = parser.parse_args()

# ========== 功能函数 ==========

def process_r3d_file(r3d_path: Path):
    """调用 REDline 处理单个 R3D 文件"""
    basename = r3d_path.stem
    out_dir = Path(args.out_dir) / basename
    out_dir.mkdir(parents=True, exist_ok=True)

    # # 输出文件名前缀
    # out_prefix = str(out_dir / "frame_")

    # REDline 命令
    cmd = [
        args.REDLINE_CMD,
        "--i", str(r3d_path),
        "--outDir", str(out_dir),
        "--format", "1",              # 1 = TIFF
        "--iso", str(args.iso),
        "--NR", "0",                  # 关闭降噪
        "--resizeX", "4096",            # 下采样 1/2
        "--resizeY", "2160",            # 下采样 1/2
        "--filter", "5",              # Catmull-Rom
        "--decodeThreads", "8",    # 全质量解码
        # "--useRMD", "1",              # 使用相机元数据
        # "--pipeline", "PrimaryDevelopment"  # 只做 debayer，不做 IPP2 处理
        # "--frameCount", "60",
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


def batch_process():
    """批量处理输入文件夹中的所有 R3D 文件"""
    input_dir = Path(args.input_dir)
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
            process_r3d_file(f)


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

if __name__ == "__main__":
    # batch_process()
    single_process()
