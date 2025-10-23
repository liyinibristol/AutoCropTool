import sys
import os
import numpy as np
import cv2
from PIL.ImageChops import overlay
from matplotlib import pyplot as plt


def mapping_of(src, dst):
    """
    Alignment method mapping normal-light img to low-light img.
    :param src: Low-light img
    :param dst: GT img
    :return: 3*3 array as perspective matrix
    """
    assert src.shape == dst.shape
    mtx = np.array([[1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1]])

    return mtx

def mapping_feature_pts(src, dst, method='ORB', min_matches=10):
    assert src.shape == dst.shape
    mtx = np.array([[1, 0, 0],
                    [0, 1, 0],
                    [0, 0, 1]])

    # 初始化特征检测器
    if method == 'SIFT':
        detector = cv2.SIFT_create()
    elif method == 'ORB':
        detector = cv2.ORB_create(nfeatures=5000)
    elif method == 'AKAZE':
        detector = cv2.AKAZE_create()
    elif method == 'BRISK':
        detector = cv2.BRISK_create()
    else:
        raise ValueError("不支持的检测方法，请选择: 'SIFT', 'ORB', 'AKAZE', 'BRISK'")

    src_gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    dst_gray = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)

    kp1, des1 = detector.detectAndCompute(src_gray, None)
    kp2, des2 = detector.detectAndCompute(dst_gray, None)

    if des1 is None or des2 is None:
        print("No keypoints detected.")
        return mtx

    # 特征匹配
    if method == 'SIFT' or method == 'AKAZE':
        # 对于 SIFT 和 AKAZE 使用 FLANN 匹配器
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
    else:
        # 对于 ORB 和 BRISK 使用暴力匹配器
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    if method == 'SIFT' or method == 'AKAZE':
        matches = matcher.knnMatch(des1, des2, k=2)
        # 应用 Lowe's ratio test
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
    else:
        matches = matcher.match(des1, des2)
        # 按距离排序
        matches = sorted(matches, key=lambda x: x.distance)
        # 取前 80% 的匹配点
        good_matches = matches[:int(len(matches) * 0.8)]
    print(f"找到 {len(good_matches)} 个良好匹配")

    if len(good_matches) < min_matches:
        print(f"匹配点数量不足 {min_matches}，无法计算变换矩阵")
        return mtx

    # 提取匹配点的坐标
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 使用 RANSAC 计算单应性矩阵
    mtx, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

    # 统计内点数量
    inlier_count = np.sum(mask)
    print(f"内点数量: {inlier_count}/{len(good_matches)}")

    h, w = dst.shape[:2]
    registered_img = cv2.warpPerspective(dst, mtx, (w, h))
    visualize_registration(src, dst, registered_img, kp1, kp2, good_matches, mask)

    return mtx


def visualize_registration(img1, img2, registered_img, kp1, kp2, matches, mask):
    """可视化配准结果"""
    # 创建匹配可视化
    draw_params = dict(matchColor=(0, 255, 0),  # 绿色匹配线
                       singlePointColor=None,
                       matchesMask=mask.ravel().tolist() if mask is not None else None,
                       flags=2)

    img_matches = cv2.drawMatches(img1, kp1, img2, kp2, matches, None, **draw_params)

    # 创建配准结果对比
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # 原始图像1
    axes[0, 0].imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    axes[0, 0].set_title('参考图像')
    axes[0, 0].axis('off')

    # 原始图像2
    axes[0, 1].imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    axes[0, 1].set_title('待配准图像')
    axes[0, 1].axis('off')

    # 配准后的图像
    axes[1, 0].imshow(cv2.cvtColor(registered_img, cv2.COLOR_BGR2RGB))
    axes[1, 0].set_title('配准后的图像')
    axes[1, 0].axis('off')

    # 特征匹配可视化
    axes[1, 1].imshow(cv2.cvtColor(img_matches, cv2.COLOR_BGR2RGB))
    axes[1, 1].set_title('特征匹配')
    axes[1, 1].axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    src = cv2.imread(r"/home/ub24017/MyCodes/AutoCropTool/data/001_014/low_light_cropped.png")
    dst = cv2.imread(r"/home/ub24017/MyCodes/AutoCropTool/data/001_014/normal_light_cropped.png")

    mtx = mapping_feature_pts(src, dst, "ORB")
    # 应用透视变换

    h, w = dst.shape[:2]
    registered_img = cv2.warpPerspective(dst, mtx, (w, h))
    overlay = cv2.addWeighted(src, 0.5, registered_img, 0.5, 0)

    pass