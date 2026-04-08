# Miku AR - 체스보드 위에 미쿠 올리기

카메라 캘리브레이션으로 체스보드의 위치를 추적하고,
웹 브라우저에서 해당 위치에 3D MMD 미쿠 모델을 AR로 오버레이합니다.

---

## 파일 구성

```
mikumikudance/
├── cali.py                          # 캘리브레이션 + cam_data.txt 생성
├── cam_data.txt                     # 캘리브레이션 결과 + 프레임별 카메라 포즈 (JSON)
├── miku_viewer.html                 # AR 웹 뷰어
├── vid2.mp4                         # 체스보드 촬영 영상
├── YYB Hatsune Miku_default/        # 미쿠 PMX 모델
└── Triple Baka/                     # Triple Baka VMD 애니메이션
```

---

## 실행 방법

### 1. cam_data.txt 생성

```
python3 cali.py
```

- vid2.mp4에서 10프레임마다 샘플을 추출해 카메라 캘리브레이션 수행
- 전체 프레임을 순회하며 체스보드가 검출된 프레임의 rvec, tvec을 저장
- 결과: cam_data.txt (JSON)

### 2. 웹 뷰어 실행

```
python3 -m http.server 8080
```

브라우저에서 접속:
```
http://localhost:8080/miku_viewer.html
```

---

## cam_data.txt 구조

```json
{
  "calibration": {
    "rms": 0.123,
    "K": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
    "dist_coeff": [...],
    "img_width": 1080,
    "img_height": 1920
  },
  "video": { "fps": 29.97, "total_frames": 280 },
  "board": { "shape": [10, 7], "cell_size": 0.02 },
  "frames": [
    { "idx": 5, "rvec": [...], "tvec": [...] },
    ...
  ]
}
```

---

## 동작 원리

```
cali.py
  └─ 캘리브레이션 → K, dist_coeff
  └─ solvePnP (프레임별) → rvec, tvec
  └─ cam_data.txt 저장

miku_viewer.html
  └─ cam_data.txt 로드
  └─ three.js + MMDLoader로 미쿠 모델 로드
  └─ 매 프레임: video.currentTime → 프레임 인덱스
             → rvec/tvec 조회
             → OpenCV→OpenGL 좌표 변환
             → three.js 카메라 포즈 적용
             → 체스보드 중심에 미쿠 렌더링
```

### 좌표계 변환 (OpenCV → three.js)

flip = diag(1, -1, -1)

R_c2w = R^T · flip
t_c2w = -R^T · t

---

## 요구사항

Python: opencv-python, numpy
Browser: ES Module 지원 브라우저 (Chrome, Firefox, Safari 최신)

---

## 예시 결과
![screenshot.png](screenshot.png)