import numpy as np
import cv2 as cv
import json

# ─────────────────────────────────────────────
# 캘리브레이션
# ─────────────────────────────────────────────
def select_imgs_from_vids(vid_file, f_interval=10):
    vid = cv.VideoCapture(vid_file)
    selected_imgs = []
    if vid.isOpened():
        frame_cnt = 0
        while True:
            valid, img = vid.read()
            if not valid:
                break
            if not frame_cnt:
                selected_imgs.append(img)
            frame_cnt = (frame_cnt + 1) % f_interval
    return selected_imgs

def calib_cam(imgs, board_shape, cell_size):
    img_pts = []
    for img in imgs:
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        complete, pts = cv.findChessboardCorners(gray, board_shape)
        if complete:
            img_pts.append(pts)

    obj = [[x, y, 0] for y in range(board_shape[1]) for x in range(board_shape[0])]
    obj_pts = [np.array(obj, dtype=np.float32) * cell_size] * len(img_pts)

    return cv.calibrateCamera(obj_pts, img_pts, gray.shape[::-1], None, None)

def print_calib_result(cal_data):
    rms, K, dist_coeff, rvecs, tvecs = cal_data
    print("\n## Camera Calibration Results")
    print(f"  RMS error : {rms:.4f}")
    print(f"  fx, fy    : {K[0,0]:.2f}, {K[1,1]:.2f}")
    print(f"  cx, cy    : {K[0,2]:.2f}, {K[1,2]:.2f}")
    print(f"  dist_coeff: {dist_coeff[0].round(4)}")
    print(f"  num images: {len(rvecs)}")

# ─────────────────────────────────────────────
# 카메라 데이터 저장
# ─────────────────────────────────────────────
def save_cam_data(vid_file, cal_data, board_shape, cell_size, out_file="cam_data.txt"):
    """
    캘리브레이션 결과 + 프레임별 카메라 위치(rvec, tvec)를
    JSON 형식으로 out_file에 저장.
    체스보드가 검출된 프레임만 frames 배열에 포함.
    """
    rms, K, dist_coeff, _, _ = cal_data

    obj = [[x, y, 0] for y in range(board_shape[1]) for x in range(board_shape[0])]
    obj_pts = np.array(obj, dtype=np.float32) * cell_size

    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    vid = cv.VideoCapture(vid_file)
    if not vid.isOpened():
        print("영상 파일을 열 수 없어요.")
        return

    img_w  = int(vid.get(cv.CAP_PROP_FRAME_WIDTH))
    img_h  = int(vid.get(cv.CAP_PROP_FRAME_HEIGHT))
    fps    = vid.get(cv.CAP_PROP_FPS)
    total  = int(vid.get(cv.CAP_PROP_FRAME_COUNT))

    frames = []
    frame_idx = 0
    found_cnt = 0

    print(f"  프레임 처리 중 (총 {total}개)...")
    while True:
        valid, frame = vid.read()
        if not valid:
            break

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        complete, img_pts = cv.findChessboardCorners(gray, board_shape)

        if complete:
            img_pts = cv.cornerSubPix(gray, img_pts, (11, 11), (-1, -1), criteria)
            _, rvec, tvec = cv.solvePnP(obj_pts, img_pts, K, dist_coeff)
            frames.append({
                "idx":  frame_idx,
                "rvec": rvec.ravel().tolist(),   # [rx, ry, rz]
                "tvec": tvec.ravel().tolist(),   # [tx, ty, tz]
            })
            found_cnt += 1

        frame_idx += 1
        if frame_idx % 30 == 0:
            print(f"    {frame_idx}/{total} 프레임 완료 (검출: {found_cnt}개)")

    vid.release()

    data = {
        "calibration": {
            "rms":        round(rms, 6),
            "K":          K.tolist(),
            "dist_coeff": dist_coeff.ravel().tolist(),
            "img_width":  img_w,
            "img_height": img_h,
        },
        "video": {
            "file":         vid_file,
            "fps":          fps,
            "total_frames": frame_idx,
        },
        "board": {
            "shape":     list(board_shape),
            "cell_size": cell_size,
        },
        "frames": frames,   # 검출된 프레임만 포함 (idx 기준으로 조회)
    }

    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n  cam_data.txt 저장 완료!")
    print(f"  총 {frame_idx}프레임 중 {found_cnt}프레임 체스보드 검출됨")


# ─────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────
BOARD_SHAPE = (10, 7)
CELL_SIZE   = 0.02   # 2cm
VID_FILE    = "./vid2.mp4"

print("캘리브레이션 중...")
imgs     = select_imgs_from_vids(VID_FILE)
cal_data = calib_cam(imgs, BOARD_SHAPE, CELL_SIZE)
print_calib_result(cal_data)

print("\n카메라 데이터 저장 중...")
save_cam_data(VID_FILE, cal_data, BOARD_SHAPE, CELL_SIZE)
