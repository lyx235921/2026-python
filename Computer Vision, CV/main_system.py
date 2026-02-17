import cv2
import mediapipe as mp
import numpy as np
import time
from ultralytics import YOLO

# ================= 配置区域 =================
# 阈值设置 (已按你的要求调整)
EAR_THRESHOLD = 0.10  # 闭眼阈值 (越小越难触发)
MAR_THRESHOLD = 0.50  # 打哈欠阈值
CLOSED_FRAME_THRESH = 15  # 连续闭眼多少帧报警
PHONE_CONF_THRESH = 0.5  # YOLO检测手机的置信度

# ================= 1. 初始化模型 =================
print("正在加载 YOLOv8 模型 (用于检测手机)...")
yolo_model = YOLO('yolov8n.pt')  # 自动下载或加载本地

print("正在初始化 MediaPipe (用于检测人脸)...")
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ================= 2. 辅助函数 =================
def calculate_ratio(landmarks, indices, w, h):
    """通用纵横比计算"""
    coords = []
    for i in indices:
        lm = landmarks[i]
        coords.append([lm.x * w, lm.y * h])
    coords = np.array(coords)
    v1 = np.linalg.norm(coords[1] - coords[5])
    v2 = np.linalg.norm(coords[2] - coords[4])
    h_dist = np.linalg.norm(coords[0] - coords[3])
    if h_dist == 0: return 0.0
    return (v1 + v2) / (2.0 * h_dist)


def calculate_mar(landmarks, indices, w, h):
    """嘴部张开度计算"""
    p_left = np.array([landmarks[indices[0]].x * w, landmarks[indices[0]].y * h])
    p_right = np.array([landmarks[indices[1]].x * w, landmarks[indices[1]].y * h])
    p_top = np.array([landmarks[indices[2]].x * w, landmarks[indices[2]].y * h])
    p_bottom = np.array([landmarks[indices[3]].x * w, landmarks[indices[3]].y * h])
    h_dist = np.linalg.norm(p_left - p_right)
    v_dist = np.linalg.norm(p_top - p_bottom)
    if h_dist == 0: return 0.0
    return v_dist / h_dist


# 关键点索引
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [61, 291, 13, 14]

# ================= 3. 主循环 =================
cap = cv2.VideoCapture(0)
# 降低分辨率以保证双模型同时运行的帧率
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

frame_counter = 0  # 闭眼计数器

print("✅ 系统完全启动！驾驶员监控中...")

while True:
    success, frame = cap.read()
    if not success: break

    # 翻转画面
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # ---------------- A. YOLO 手机检测 ----------------
    # 只检测 'cell phone' (COCO id: 67)
    # verbose=False 不打印日志，stream=True 提速
    yolo_results = yolo_model(frame, stream=True, verbose=False, classes=[67], conf=PHONE_CONF_THRESH)

    phone_detected = False
    for r in yolo_results:
        boxes = r.boxes
        for box in boxes:
            # 画出手机框
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, "PHONE", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            phone_detected = True

    # ---------------- B. MediaPipe 疲劳检测 ----------------
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_results = face_mesh.process(rgb_frame)

    # 默认状态
    status = "SAFE"
    color = (0, 255, 0)  # Green

    avg_ear = 0.0
    mar = 0.0

    if mp_results.multi_face_landmarks:
        for face_landmarks in mp_results.multi_face_landmarks:
            landmarks = face_landmarks.landmark

            # 计算指标
            left_ear = calculate_ratio(landmarks, LEFT_EYE, w, h)
            right_ear = calculate_ratio(landmarks, RIGHT_EYE, w, h)
            avg_ear = (left_ear + right_ear) / 2.0
            mar = calculate_mar(landmarks, MOUTH, w, h)

            # 画出面部网格 (显得技术很强)
            mp.solutions.drawing_utils.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_tesselation_style()
            )

            # --- 核心判定逻辑 (优先级: 睡觉 > 哈欠 > 玩手机) ---
            if avg_ear < EAR_THRESHOLD:
                frame_counter += 1
                if frame_counter >= CLOSED_FRAME_THRESH:
                    status = "DANGER: SLEEPING"
                    color = (0, 0, 255)  # Red

            elif mar > MAR_THRESHOLD:
                frame_counter = 0
                status = "WARNING: YAWNING"
                color = (0, 165, 255)  # Orange

            elif phone_detected:
                frame_counter = 0
                status = "ILLEGAL: PHONE USE"
                color = (255, 0, 255)  # Magenta (紫色)

            else:
                frame_counter = 0
                status = "SAFE"
                color = (0, 255, 0)

    # ---------------- C. 仪表盘 UI 绘制 ----------------
    # 顶部黑条背景
    cv2.rectangle(frame, (0, 0), (w, 50), (0, 0, 0), -1)

    # 状态显示
    cv2.putText(frame, f"STATUS: {status}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    # 数据显示 (右侧)
    info_str = f"EAR: {avg_ear:.2f} | MAR: {mar:.2f} | Phone: {'YES' if phone_detected else 'NO'}"
    cv2.putText(frame, info_str, (w - 450, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # ---------------- D. 报警反馈 ----------------
    if "DANGER" in status or "WARNING" in status or "ILLEGAL" in status:
        # 屏幕边框闪烁效果
        cv2.rectangle(frame, (0, 0), (w, h), color, 10)

    cv2.imshow('Advanced Driver Monitoring System (ADMS)', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()