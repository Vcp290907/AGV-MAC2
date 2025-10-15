#!/usr/bin/env python3
import os, sys, glob
import cv2
import numpy as np

def main(img_dir):
    patterns = ["*.jpg","*.jpeg","*.png","*.bmp"]
    files=[]
    for p in patterns:
        files += glob.glob(os.path.join(img_dir, p))
    files = sorted(files)
    if not files:
        print(f"No images in {img_dir}")
        return 1

    # Candidate dictionaries (OpenCV names)
    dict_names = [
        'DICT_4X4_50','DICT_4X4_100','DICT_4X4_250','DICT_4X4_1000',
        'DICT_5X5_50','DICT_5X5_100','DICT_5X5_250','DICT_5X5_1000',
        'DICT_6X6_50','DICT_6X6_100','DICT_6X6_250','DICT_6X6_1000',
        'DICT_7X7_50','DICT_7X7_100','DICT_7X7_250','DICT_7X7_1000',
        'DICT_APRILTAG_16h5','DICT_APRILTAG_25h9','DICT_APRILTAG_36h10','DICT_APRILTAG_36h11'
    ]

    results = {name: [] for name in dict_names}
    for f in files:
        img = cv2.imread(f)
        if img is None:
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        for name in dict_names:
            try:
                DICT = getattr(cv2.aruco, name)
                dictionary = cv2.aruco.getPredefinedDictionary(DICT)
                try:
                    det_params = cv2.aruco.DetectorParameters()
                except AttributeError:
                    det_params = cv2.aruco.DetectorParameters_create()
                try:
                    detector = cv2.aruco.ArucoDetector(dictionary, det_params)
                    corners, ids, _ = detector.detectMarkers(gray)
                except Exception:
                    corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=det_params)
                count = 0 if ids is None else int(len(ids))
                results[name].append(count)
            except Exception:
                results[name].append(-1)

    # summarize
    print(f"Tested {len(files)} images")
    best = []
    for name in dict_names:
        vals = results[name]
        valid = [v for v in vals if v>=0]
        if not valid:
            continue
        avg = np.mean(valid)
        mx = np.max(valid)
        print(f"{name:>24}: avg {avg:.2f} max {mx} counts -> {valid[:10]}{'...' if len(valid)>10 else ''}")
        best.append((avg, mx, name))
    best.sort(reverse=True)
    if best:
        print("\nTop candidates:")
        for row in best[:5]:
            print(row)

if __name__=='__main__':
    img_dir = sys.argv[1] if len(sys.argv)>1 else './agv-raspberry/scripts/capturas_pi'
    raise SystemExit(main(img_dir))
