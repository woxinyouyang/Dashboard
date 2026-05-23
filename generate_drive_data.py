"""
生成驾驶舱模拟器虚拟测试数据CSV
- 2分钟 = 120秒
- 40帧/秒，共4800帧
- 每帧25ms
"""
import csv
import numpy as np
from scipy.interpolate import CubicSpline

np.random.seed(42)

dt = 0.025  # 25ms
n = 4800
t = np.arange(n) * dt  # 0, 0.025, 0.050, ..., 119.975

# ============================================================
# 1. 速度曲线设计 (m/s) — 核心物理量，通过平滑样条插值
# ============================================================
t_brk = np.array([0, 3, 7, 12, 18, 25, 33, 42, 50, 58, 65, 72, 82, 92, 100, 108, 115, 120])
v_brk = np.array([0, 0, 1.5, 5, 10, 17, 24, 27, 25, 23, 24, 27, 28, 22, 14, 6, 2, 0])

cs_v = CubicSpline(t_brk, v_brk, bc_type=((1, 0.0), (1, 0.0)))
speed = cs_v(t)
speed = np.maximum(speed, 0)  # 不会为负

# ============================================================
# 2. 纵向加速度 (X轴加速度) = 速度的导数
# ============================================================
ax_body = np.gradient(speed, dt)

# ============================================================
# 3. 偏航角 (Yaw) — 转向路径
# ============================================================
yaw_t = np.array([0, 35, 45, 55, 65, 72, 80, 120])
yaw_v = np.array([0, 0, 0.4, 0.55, 0.55, 0.3, 0, 0])  # rad
cs_yaw = CubicSpline(yaw_t, yaw_v, bc_type=((1, 0.0), (1, 0.0)))
yaw = cs_yaw(t)

# ============================================================
# 4. 世界坐标系位置 (速度在world frame积分)
# ============================================================
pos_x = np.zeros(n)
pos_y = np.zeros(n)
pos_z = np.zeros(n)  # 平坦路面

for i in range(1, n):
    v_world_x = speed[i-1] * np.cos(yaw[i-1])
    v_world_y = speed[i-1] * np.sin(yaw[i-1])
    pos_x[i] = pos_x[i-1] + v_world_x * dt
    pos_y[i] = pos_y[i-1] + v_world_y * dt

# ============================================================
# 5. 车身坐标系速度 (ShaftSpeed)
# ============================================================
vx_body = speed  # 前进方向
vy_body = np.zeros(n)
vz_body = np.zeros(n)

yaw_rate = np.gradient(yaw, dt)
for i in range(n):
    if abs(yaw_rate[i]) > 0.001 and speed[i] > 0.5:
        slip_angle = 0.025 * np.sign(yaw_rate[i])  # ~1.4度侧偏角
        vy_body[i] = speed[i] * slip_angle

# ============================================================
# 6. 车身坐标系加速度 (ShaftAcceleration)
# ============================================================
ay_body = np.gradient(vy_body, dt)
az_body = np.zeros(n) + np.random.normal(0, 0.02, n)  # 垂直振动

# 补充向心加速度: ay = v * yaw_rate
for i in range(n):
    if speed[i] > 0.5:
        ay_body[i] += speed[i] * yaw_rate[i]

# ============================================================
# 7. 姿态角: Roll(侧倾), Pitch(俯仰)
# ============================================================
roll = np.zeros(n)
for i in range(n):
    if speed[i] > 0.5:
        roll[i] = -0.04 * yaw[i] * min(speed[i] / 20, 1.5)
pitch = -0.012 * ax_body  # 加速抬头(-), 刹车点头(+)
roll = np.clip(roll, -0.1, 0.1)
pitch = np.clip(pitch, -0.08, 0.08)

# ============================================================
# 8. 角速度
# ============================================================
ang_vel_x = np.gradient(roll, dt)
ang_vel_y = np.gradient(pitch, dt)
ang_vel_z = yaw_rate

# ============================================================
# 9. 角加速度
# ============================================================
ang_acc_x = np.gradient(ang_vel_x, dt)
ang_acc_y = np.gradient(ang_vel_y, dt)
ang_acc_z = np.gradient(ang_vel_z, dt)

# ============================================================
# 10. 控制输入: Throttle / Brake / Steering
# ============================================================
throttle = np.zeros(n)
brake = np.zeros(n)
steering = np.zeros(n)

for i, time in enumerate(t):
    # Throttle
    if time < 3:
        throttle[i] = 0
    elif time < 8:
        throttle[i] = 0.2 * (time - 3) / 5
    elif time < 12:
        throttle[i] = 0.2 + 0.2 * (time - 8) / 4
    elif time < 25:
        throttle[i] = 0.4
    elif time < 33:
        throttle[i] = 0.4 - 0.15 * (time - 25) / 8
    elif time < 42:
        throttle[i] = 0.25
    elif time < 55:
        throttle[i] = 0.18
    elif time < 65:
        throttle[i] = 0.22
    elif time < 82:
        throttle[i] = 0.25 + 0.1 * (time - 72) / 10
    elif time < 92:
        throttle[i] = 0.2
    elif time < 100:
        throttle[i] = 0.1 * (1 - (time - 92) / 8)
    else:
        throttle[i] = 0

    # Brake
    if 92 <= time < 100:
        brake[i] = 0.15 + 0.2 * (time - 92) / 8
    elif 100 <= time < 110:
        brake[i] = 0.35 + 0.25 * (time - 100) / 10
    elif 110 <= time < 118:
        brake[i] = 0.6 + 0.2 * (time - 110) / 8
    elif time >= 118:
        brake[i] = 0.8
    else:
        brake[i] = 0

    # Steering (positive = right)
    if 35 <= time < 45:
        steering[i] = 0.2 * (time - 35) / 10
    elif 45 <= time < 58:
        steering[i] = 0.2
    elif 58 <= time < 72:
        steering[i] = 0.2 * (1 - (time - 58) / 14)
    elif 72 <= time < 80:
        steering[i] = -0.05 * (time - 72) / 8
    else:
        steering[i] = 0
    steering[i] += np.random.normal(0, 0.003)

# ============================================================
# 11. Gear (挡位)
# ============================================================
gear = np.ones(n, dtype=int)
speed_kmh = speed * 3.6
for i in range(n):
    if speed_kmh[i] < 1:
        gear[i] = 1
    elif speed_kmh[i] < 12:
        gear[i] = 2
    elif speed_kmh[i] < 25:
        gear[i] = 3
    elif speed_kmh[i] < 45:
        gear[i] = 4
    elif speed_kmh[i] < 70:
        gear[i] = 5
    else:
        gear[i] = 6

# ============================================================
# 12. Revolution (引擎回转数, RPM)
# ============================================================
gear_ratios = {1: 380, 2: 240, 3: 170, 4: 125, 5: 95, 6: 78}
revolution = np.zeros(n)
for i in range(n):
    if speed[i] < 0.2:
        revolution[i] = 750 + np.random.normal(0, 15)
    else:
        gr = gear_ratios[gear[i]]
        base_rpm = 750 + speed_kmh[i] * gr
        acc_boost = max(0, ax_body[i] * 120)
        revolution[i] = base_rpm + acc_boost + np.random.normal(0, 10)
revolution = np.clip(revolution, 650, 6500)

# ============================================================
# 13. SpeedMeter (km/h)
# ============================================================
speed_meter = speed_kmh + np.random.normal(0, 0.15, n)

# ============================================================
# 14. Mileage (里程, km)
# ============================================================
mileage_start = 12345.6
mileage = mileage_start + np.cumsum(speed * dt) / 1000

# ============================================================
# 15. RoadCurvature / RoadSlope / VehicleOffset
# ============================================================
road_curvature = np.zeros(n)
for i in range(n):
    if 35 <= t[i] < 72 and speed[i] > 1:
        if t[i] < 50:
            progress = (t[i] - 35) / 15
        else:
            progress = max(0, 1 - (t[i] - 50) / 22)
        road_curvature[i] = 0.0025 * progress * min(speed[i] / 15, 1.5)

road_slope = np.zeros(n)
vehicle_offset = np.zeros(n)
for i in range(1, n):
    vehicle_offset[i] = vehicle_offset[i-1] * 0.997 + np.random.normal(0, 0.005)

# ============================================================
# 16. Parking
# ============================================================
parking = np.zeros(n)
parking[t >= 118.5] = 1.0

# ============================================================
# 17. 传感器噪声
# ============================================================
loc_x = pos_x + np.random.normal(0, 0.002, n)
loc_y = pos_y + np.random.normal(0, 0.002, n)
loc_z = pos_z + np.random.normal(0, 0.001, n)
ax_body_n = ax_body + np.random.normal(0, 0.008, n)
ay_body_n = ay_body + np.random.normal(0, 0.008, n)
az_body_n = az_body + np.random.normal(0, 0.005, n)

# ============================================================
# 18. 时间戳生成 (从 08:30:00:000 开始，每步+25ms)
# ============================================================
start_ms_total = 8 * 3600000 + 30 * 60000  # 08:30:00:000
timestamps = []
for i in range(n):
    ms = start_ms_total + i * 25
    h = (ms // 3600000) % 24
    rem = ms % 3600000
    m = rem // 60000
    rem2 = rem % 60000
    s = rem2 // 1000
    remain_ms = rem2 % 1000
    timestamps.append(f"{h:02d}:{m:02d}:{s:02d}:{remain_ms:03d}")

# ============================================================
# 19. 写入 CSV
# ============================================================
headers = [
    '序号', 'TimeStamp',
    'Location_X', 'Location_Y', 'Location_Z',
    'Pitch', 'Yaw', 'Roll',
    'VehicleOffset', 'RoadCurvature', 'RoadSlope',
    'ShaftAcceleration_X', 'ShaftAcceleration_Y', 'ShaftAcceleration_Z',
    'ShaftSpeed_X', 'ShaftSpeed_Y', 'ShaftSpeed_Z',
    'AngularVelocity_X', 'AngularVelocity_Y', 'AngularVelocity_Z',
    'AngularAcceleration_X', 'AngularAcceleration_Y', 'AngularAcceleration_Z',
    'Revolution', 'SpeedMeter', 'Gear', 'Mileage',
    'Steering', 'Throttle', 'Brake', 'Parking'
]

output_path = r'D:\YYClaw\驾驶展示页\driving_sim_test_data.csv'

with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for i in range(n):
        writer.writerow([
            i + 1,
            timestamps[i],
            f"{loc_x[i]:.4f}", f"{loc_y[i]:.4f}", f"{loc_z[i]:.4f}",
            f"{pitch[i]:.5f}", f"{yaw[i]:.5f}", f"{roll[i]:.5f}",
            f"{vehicle_offset[i]:.4f}", f"{road_curvature[i]:.6f}", f"{road_slope[i]:.6f}",
            f"{ax_body_n[i]:.4f}", f"{ay_body_n[i]:.4f}", f"{az_body_n[i]:.4f}",
            f"{vx_body[i]:.4f}", f"{vy_body[i]:.6f}", f"{vz_body[i]:.6f}",
            f"{ang_vel_x[i]:.6f}", f"{ang_vel_y[i]:.6f}", f"{ang_vel_z[i]:.6f}",
            f"{ang_acc_x[i]:.6f}", f"{ang_acc_y[i]:.6f}", f"{ang_acc_z[i]:.6f}",
            f"{revolution[i]:.1f}", f"{speed_meter[i]:.2f}", str(gear[i]),
            f"{mileage[i]:.4f}",
            f"{steering[i]:.4f}", f"{throttle[i]:.4f}", f"{brake[i]:.4f}", f"{parking[i]:.4f}",
        ])

print(f"CSV已生成：{output_path}")
print(f"行数：{n}，列数：{len(headers)}")
print(f"\n--- 数据预览（前5行）---")
for j, h in enumerate(headers):
    print(f"{h:25s}", end="")
print()
for i in range(5):
    with open(output_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if idx == i + 1:
                for val in row:
                    print(f"{val:25s}", end="")
                print()
                break

print(f"\n--- 物理规律校验 ---")
print(f"速度从 {speed[0]:.2f} m/s 到 {speed[-1]:.2f} m/s")
print(f"最大速度: {np.max(speed)*3.6:.2f} km/h (在 {np.argmax(speed)*dt:.1f}s)")
print(f"最大纵向加速度: {np.max(ax_body):.3f} m/s²")
print(f"最大侧向加速度(含向心): {np.max(np.abs(ay_body)):.3f} m/s²")
print(f"总行驶里程: {(mileage[-1] - mileage_start):.3f} km")
print(f"最大引擎转速: {np.max(revolution):.0f} RPM")
print(f"换挡次数: {np.sum(np.diff(gear) != 0)}")
