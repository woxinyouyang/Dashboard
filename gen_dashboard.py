"""
生成驾驶模拟器数据可视化仪表盘 (单页HTML)
V2: 增加CSV文件选择 + 字号增大 + 雷达图修复
"""
import csv
import json

CSV_PATH = r'D:\YYClaw\驾驶展示页\driving_sim_test_data.csv'
OUTPUT_PATH = r'D:\YYClaw\驾驶展示页\dashboard.html'

# 读取CSV
with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    headers = next(reader)
    rows = list(reader)

n = len(rows)
dt = 0.025
col_map = {h: i for i, h in enumerate(headers)}

def get_col(name):
    idx = col_map[name]
    return [float(r[idx]) for r in rows]

def get_col_int(name):
    idx = col_map[name]
    return [int(float(r[idx])) for r in rows]

data = {
    't': [i*dt for i in range(n)],
    'x': get_col('Location_X'), 'y': get_col('Location_Y'), 'z': get_col('Location_Z'),
    'p': get_col('Pitch'), 'yaw': get_col('Yaw'), 'r': get_col('Roll'),
    'vx': get_col('ShaftSpeed_X'), 'vy': get_col('ShaftSpeed_Y'),
    'ax': get_col('ShaftAcceleration_X'), 'ay': get_col('ShaftAcceleration_Y'), 'az': get_col('ShaftAcceleration_Z'),
    'rpm': get_col('Revolution'), 'spd': get_col('SpeedMeter'), 'gear': get_col_int('Gear'),
    'thr': get_col('Throttle'), 'brk': get_col('Brake'), 'str': get_col('Steering'), 'park': get_col('Parking'),
    'wz': get_col('AngularVelocity_Z'), 'waz': get_col('AngularAcceleration_Z'),
    'cur': get_col('RoadCurvature'), 'off': get_col('VehicleOffset'), 'mil': get_col('Mileage'),
}

# 统计指标
max_speed = max(data['vx'])
avg_speed = sum(data['vx']) / n
max_speed_kmh = max(data['spd'])
max_accel = max(data['ax'])
max_decel = min(data['ax'])
max_lat_g = max(abs(v) for v in data['ay'])
max_rpm = max(data['rpm'])
total_dist = data['mil'][-1] - data['mil'][0]

data_json = json.dumps(data, separators=(',', ':'))

# ============================================================
# HTML 模板 (使用 Python f-string)
# ============================================================
# 为避免f-string中花括号冲突，所有JS中的 { 和 } 用 {{ 和 }} 转义
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>驾驶模拟器数据仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    background: #0a0e17;
    color: #e0e6ed;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    padding: 20px;
    min-height: 100vh;
}}
.header {{
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 12px;
    margin-bottom: 20px; padding: 16px 24px;
    background: linear-gradient(135deg, #141a26, #1a2235);
    border-radius: 12px; border: 1px solid #2a3444;
}}
.header-left {{
    display: flex; align-items: center; gap: 20px;
}}
.header h1 {{
    font-size: 22px; font-weight: 600;
    background: linear-gradient(90deg, #00d4ff, #00e676);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    white-space: nowrap;
}}
.file-select {{
    display: flex; align-items: center; gap: 10px;
}}
.file-select label {{
    display: inline-block;
    padding: 6px 14px;
    background: #1e2a3a;
    color: #00d4ff;
    border: 1px solid #2a4a6a;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s;
}}
.file-select label:hover {{
    background: #2a3a4a;
    border-color: #00d4ff;
}}
.file-select input[type="file"] {{ display: none; }}
.file-select .file-name {{
    font-size: 12px;
    color: #8892a4;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
.stats {{
    display: flex; gap: 20px; flex-wrap: wrap;
}}
.stat-item {{ text-align: center; }}
.stat-item .val {{ font-size: 20px; font-weight: 700; color: #00d4ff; }}
.stat-item .label {{ font-size: 11px; color: #8892a4; margin-top: 2px; white-space: nowrap; }}
.stat-item .val.green {{ color: #00e676; }}
.stat-item .val.orange {{ color: #ff6b35; }}
.stat-item .val.pink {{ color: #ff4081; }}
.stat-item .val.amber {{ color: #ffd740; }}
.grid {{
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr;
    gap: 14px;
    margin-bottom: 14px;
}}
.grid2 {{ grid-template-columns: 1fr 1fr; }}
.chart-card {{
    background: #141a26;
    border-radius: 10px;
    padding: 14px;
    border: 1px solid #2a3444;
}}
.chart-card .title {{
    font-size: 14px; font-weight: 600; color: #8892a4;
    margin-bottom: 8px;
    border-left: 3px solid #00d4ff; padding-left: 10px;
}}
.chart-card .chart {{ width: 100%; }}
#chart-trajectory {{ height: 520px; }}
.chart-3row {{ height: 340px; }}
.chart-2row {{ height: 270px; }}
.chart-normal {{ height: 230px; }}
/* 自定义滚动条 */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: #0a0e17; }}
::-webkit-scrollbar-thumb {{ background: #2a3444; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #3a4454; }}
@media (max-width: 1200px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} .grid2 {{ grid-template-columns: 1fr; }} }}
@media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} .header {{ flex-direction: column; }} }}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <h1>驾驶模拟器 数据仪表盘</h1>
        <div class="file-select">
            <label for="csvFile">选择CSV文件</label>
            <input type="file" id="csvFile" accept=".csv">
            <span class="file-name" id="currentFile">driving_sim_test_data.csv</span>
        </div>
    </div>
    <div class="stats">
        <div class="stat-item">
            <div class="val" id="stat-duration">{n//40}s</div>
            <div class="label">测试时长</div>
        </div>
        <div class="stat-item">
            <div class="val green" id="stat-maxspeed">{max_speed_kmh:.1f}</div>
            <div class="label">最高速度(km/h)</div>
        </div>
        <div class="stat-item">
            <div class="val orange" id="stat-maxaccel">{max_accel:.2f}</div>
            <div class="label">最大加速度(m/s²)</div>
        </div>
        <div class="stat-item">
            <div class="val pink" id="stat-latg">{max_lat_g:.2f}</div>
            <div class="label">最大侧向G(m/s²)</div>
        </div>
        <div class="stat-item">
            <div class="val amber" id="stat-mileage">{total_dist:.3f}</div>
            <div class="label">行驶里程(km)</div>
        </div>
        <div class="stat-item">
            <div class="val" id="stat-frames">{n}</div>
            <div class="label">数据帧数</div>
        </div>
    </div>
</div>

<!-- 第一行 -->
<div class="grid">
    <div class="chart-card" style="grid-row: span 2;">
        <div class="title">行驶轨迹</div>
        <div id="chart-trajectory" class="chart"></div>
    </div>
    <div class="chart-card">
        <div class="title">速度曲线</div>
        <div id="chart-speed" class="chart chart-2row"></div>
    </div>
    <div class="chart-card">
        <div class="title">三轴加速度</div>
        <div id="chart-accel" class="chart chart-2row"></div>
    </div>
    <div class="chart-card">
        <div class="title">车身姿态角</div>
        <div id="chart-attitude" class="chart chart-2row"></div>
    </div>
    <div class="chart-card">
        <div class="title">关键指标雷达图</div>
        <div id="chart-radar" class="chart chart-2row"></div>
    </div>
</div>

<!-- 第二行 -->
<div class="grid">
    <div class="chart-card">
        <div class="title">动力系统 <span style="font-size:11px;color:#666;font-weight:400;">引擎转速 / 挡位 / 油门</span></div>
        <div id="chart-powertrain" class="chart chart-3row"></div>
    </div>
    <div class="chart-card">
        <div class="title">控制输入 <span style="font-size:11px;color:#666;font-weight:400;">制动 / 转向 / 驻车</span></div>
        <div id="chart-controls" class="chart chart-3row"></div>
    </div>
    <div class="chart-card">
        <div class="title">角运动 <span style="font-size:11px;color:#666;font-weight:400;">偏航角速度 / 角加速度</span></div>
        <div id="chart-angular" class="chart chart-3row"></div>
    </div>
</div>

<!-- 第三行 -->
<div class="grid grid2">
    <div class="chart-card">
        <div class="title">道路信息 <span style="font-size:11px;color:#666;font-weight:400;">道路曲率 / 车辆偏移</span></div>
        <div id="chart-road" class="chart chart-normal"></div>
    </div>
    <div class="chart-card">
        <div class="title">里程累积</div>
        <div id="chart-mileage" class="chart chart-normal"></div>
    </div>
</div>

<script>
// =====================================================
// 数据层
// =====================================================
var DEFAULT_DATA = {data_json};

// 时间格式化
function timeLabel(t) {{
    var m = Math.floor(t / 60);
    var s = (t % 60).toFixed(1);
    return m + ":" + (s < 10 ? "0" : "") + s;
}}

// 地图时间格式 (用于轨迹tooltip)
function timeLabel2(t) {{
    var m = Math.floor(t / 60);
    var s = Math.floor(t % 60);
    var ms = Math.floor((t - Math.floor(t)) * 1000);
    return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s + ":" + (ms < 100 ? "0" : "") + (ms < 10 ? "0" : "") + ms;
}}

// =====================================================
// 图表选项生成函数 (接收数据对象, 返回ECharts options)
// =====================================================
var chartIds = [
    'chart-trajectory', 'chart-speed', 'chart-accel', 'chart-attitude', 'chart-radar',
    'chart-powertrain', 'chart-controls', 'chart-angular', 'chart-road', 'chart-mileage'
];

function makeTrajectoryOption(D) {{
    var n = D.t.length;
    return {{
        backgroundColor: 'transparent',
        tooltip: {{
            trigger: 'item',
            formatter: function(p) {{
                var i = p.dataIndex;
                return '<b>时间</b>: ' + timeLabel2(D.t[i]) + '<br/>'
                     + '<b>X</b>: ' + D.x[i].toFixed(2) + ' m<br/>'
                     + '<b>Y</b>: ' + D.y[i].toFixed(2) + ' m<br/>'
                     + '<b>速度</b>: ' + (D.vx[i]*3.6).toFixed(1) + ' km/h<br/>'
                     + '<b>偏航角</b>: ' + (D.yaw[i]*180/Math.PI).toFixed(1) + '°';
            }}
        }},
        grid: {{ left: 56, right: 24, top: 24, bottom: 24 }},
        xAxis: {{
            name: 'X (m)', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }},
            type: 'value', splitLine: {{ lineStyle: {{ color: '#1e2634' }} }},
            axisLabel: {{ color: '#8892a4', fontSize: 11 }}
        }},
        yAxis: {{
            name: 'Y (m)', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }},
            type: 'value', splitLine: {{ lineStyle: {{ color: '#1e2634' }} }},
            axisLabel: {{ color: '#8892a4', fontSize: 11 }}
        }},
        visualMap: {{
            show: true, dimension: 0, min: 0, max: D.t[n-1], seriesIndex: 0,
            inRange: {{ color: ['#00429d','#2c5aa0','#4771a2','#73a2c6','#a5d5d8','#ffd740','#ff8a65','#ff5252','#d32f2f'] }},
            text: ['结束', '开始'], textStyle: {{ color: '#8892a4', fontSize: 11 }},
            calculable: true, left: 10, bottom: 10, itemWidth: 12, itemHeight: 90
        }},
        series: [{{
            name: '轨迹', type: 'line',
            data: D.t.map(function(ti, i) {{ return [D.x[i], D.y[i], ti]; }}),
            smooth: true, showSymbol: false, sampling: 'lttb',
            lineStyle: {{ width: 2.5 }},
            areaStyle: {{
                color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                    colorStops: [{{offset:0,color:'rgba(0,212,255,0.15)'}},{{offset:1,color:'rgba(0,212,255,0.01)'}}] }}
            }},
            emphasis: {{ focus: 'series' }}
        }}]
    }};
}}

function makeSpeedOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + p.data[1].toFixed(1) + '<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 56, top: 12, bottom: 30 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: [
            {{ type: 'value', name: 'm/s', nameTextStyle: {{ color: '#00d4ff', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
            {{ type: 'value', name: 'km/h', nameTextStyle: {{ color: '#ffd740', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }}
        ],
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}, {{ type: 'slider', xAxisIndex: 0, height: 14, bottom: 2, borderColor: '#2a3444', fillerColor: 'rgba(0,212,255,0.15)', handleStyle: {{ color: '#00d4ff' }} }}],
        series: [
            {{ name: 'ShaftSpeed_X', type: 'line', data: D.t.map(function(t,i){{return [t, D.vx[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#00d4ff' }}, yAxisIndex: 0 }},
            {{ name: 'SpeedMeter', type: 'line', data: D.t.map(function(t,i){{return [t, D.spd[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ffd740', opacity: 0.6 }}, yAxisIndex: 1 }}
        ]
    }};
}}

function makeAccelOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + p.data[1].toFixed(2) + ' m/s²<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 20, top: 14, bottom: 30 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: {{ type: 'value', name: 'm/s²', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        legend: {{ data: ['X(纵向)', 'Y(侧向)', 'Z(垂直)'], textStyle: {{ color: '#8892a4', fontSize: 12 }}, top: 2, right: 0 }},
        series: [
            {{ name: 'X(纵向)', type: 'line', data: D.t.map(function(t,i){{return [t, D.ax[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#00d4ff' }} }},
            {{ name: 'Y(侧向)', type: 'line', data: D.t.map(function(t,i){{return [t, D.ay[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ff6b35' }} }},
            {{ name: 'Z(垂直)', type: 'line', data: D.t.map(function(t,i){{return [t, D.az[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 1.5, color: '#00e676', opacity: 0.5 }} }}
        ]
    }};
}}

function makeAttitudeOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + (p.data[1]*180/Math.PI).toFixed(1) + '°<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 20, top: 14, bottom: 30 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: {{ type: 'value', name: '角度(rad)', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        legend: {{ data: ['Pitch(俯仰)', 'Yaw(偏航)', 'Roll(侧倾)'], textStyle: {{ color: '#8892a4', fontSize: 12 }}, top: 2, right: 0 }},
        series: [
            {{ name: 'Pitch(俯仰)', type: 'line', data: D.t.map(function(t,i){{return [t, D.p[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#00e676' }} }},
            {{ name: 'Yaw(偏航)', type: 'line', data: D.t.map(function(t,i){{return [t, D.yaw[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ff6b35' }}, areaStyle: {{ color: 'rgba(255,107,53,0.08)' }} }},
            {{ name: 'Roll(侧倾)', type: 'line', data: D.t.map(function(t,i){{return [t, D.r[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ff4081' }} }}
        ]
    }};
}}

function makeRadarOption(D) {{
    var n = D.t.length;
    var maxS = Math.max.apply(null, D.vx) * 3.6;
    var sum = 0; for (var i = 0; i < n; i++) {{ sum += D.vx[i]; }} var avgS = sum / n * 3.6;
    var maxA = Math.max.apply(null, D.ax);
    var minA = Math.abs(Math.min.apply(null, D.ax));
    var maxLA = 0; for (var i = 0; i < n; i++) {{ var a = Math.abs(D.ay[i]); if (a > maxLA) maxLA = a; }}
    var maxR = Math.max.apply(null, D.rpm);
    return {{
        backgroundColor: 'transparent',
        radar: {{
            indicator: [
                {{ name: maxS.toFixed(1) + ' km/h\\n最高速度', max: Math.max(120, Math.ceil(maxS * 1.3 / 10) * 10) }},
                {{ name: avgS.toFixed(1) + ' km/h\\n平均速度', max: Math.max(80, Math.ceil(avgS * 1.3 / 10) * 10) }},
                {{ name: maxA.toFixed(2) + ' m/s²\\n最大加速', max: Math.max(3, Math.ceil(maxA * 1.3 * 2) / 2) }},
                {{ name: minA.toFixed(2) + ' m/s²\\n最大减速', max: Math.max(3, Math.ceil(minA * 1.3 * 2) / 2) }},
                {{ name: maxLA.toFixed(2) + ' m/s²\\n侧向G值', max: Math.max(2, Math.ceil(maxLA * 1.4 * 2) / 2) }},
                {{ name: maxR.toFixed(0) + ' RPM\\n最高转速', max: Math.max(6500, Math.ceil(maxR * 1.2 / 500) * 500) }},
            ],
            center: ['50%', '52%'],
            radius: '58%',
            axisName: {{
                color: '#e0e6ed',
                fontSize: 11,
                borderRadius: 4,
                padding: [0, 0, 0, 0],
            }},
            splitArea: {{
                areaStyle: {{
                    color: ['rgba(0,212,255,0.02)', 'rgba(0,212,255,0.05)',
                             'rgba(0,212,255,0.02)', 'rgba(0,212,255,0.05)']
                }}
            }},
            splitLine: {{ lineStyle: {{ color: '#2a3444' }} }},
            axisLine: {{ lineStyle: {{ color: '#2a3444' }} }}
        }},
        series: [{{
            type: 'radar',
            data: [{{
                value: [maxS, avgS, maxA, minA, maxLA, maxR],
                name: '关键指标',
                areaStyle: {{ color: 'rgba(0,212,255,0.25)' }},
                lineStyle: {{ color: '#00d4ff', width: 2 }},
                itemStyle: {{ color: '#00d4ff' }}
            }}],
            symbol: 'none'
        }}]
    }};
}}

function makePowertrainOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + (p.seriesName === '挡位' ? p.data[1] : p.data[1].toFixed(1)) + '<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 56, top: 32, bottom: 28 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: [
            {{ type: 'value', name: 'RPM', nameTextStyle: {{ color: '#ff4081', fontSize: 12 }}, min: 0, max: 7000, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
            {{ type: 'value', name: '挡位/油门', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }}, min: 0, max: 1, axisLabel: {{ color: '#8892a4', fontSize: 11, formatter: function(v){{return v.toFixed(1);}} }}, splitLine: {{ show: false }} }}
        ],
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        legend: {{ data: ['引擎转速', '挡位', '油门'], textStyle: {{ color: '#8892a4', fontSize: 12 }}, top: 4, left: 0 }},
        series: [
            {{ name: '引擎转速', type: 'line', data: D.t.map(function(t,i){{return [t, D.rpm[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ff4081' }}, yAxisIndex: 0 }},
            {{ name: '挡位', type: 'line', data: D.t.map(function(t,i){{return [t, D.gear[i] / 6];}}), smooth: false, showSymbol: false, step: 'end', lineStyle: {{ width: 2, color: '#7c4dff' }}, yAxisIndex: 1, areaStyle: {{ color: 'rgba(124,77,255,0.1)' }} }},
            {{ name: '油门', type: 'line', data: D.t.map(function(t,i){{return [t, D.thr[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#00e676' }}, yAxisIndex: 1, areaStyle: {{ color: 'rgba(0,230,118,0.08)' }} }}
        ]
    }};
}}

function makeControlsOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + (p.seriesName === '驻车制动' ? (p.data[1] > 0.5 ? 'ON' : 'OFF') : p.data[1].toFixed(3)) + '<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 20, top: 32, bottom: 28 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: {{ type: 'value', name: '值', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }}, min: -0.5, max: 1, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        legend: {{ data: ['制动行程', '转向(-1~1)', '驻车制动'], textStyle: {{ color: '#8892a4', fontSize: 12 }}, top: 4, left: 0 }},
        series: [
            {{ name: '制动行程', type: 'line', data: D.t.map(function(t,i){{return [t, D.brk[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2.5, color: '#ff1744' }}, areaStyle: {{ color: 'rgba(255,23,68,0.12)' }} }},
            {{ name: '转向(-1~1)', type: 'line', data: D.t.map(function(t,i){{return [t, D.str[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#7c4dff' }} }},
            {{ name: '驻车制动', type: 'line', data: D.t.map(function(t,i){{return [t, D.park[i]];}}), smooth: false, showSymbol: false, step: 'end', lineStyle: {{ width: 2, color: '#ffd740', opacity: 0.7 }}, areaStyle: {{ color: 'rgba(255,215,64,0.1)' }} }}
        ]
    }};
}}

function makeAngularOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + p.data[1].toFixed(4) + '<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 20, top: 32, bottom: 28 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: {{ type: 'value', name: '值', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        legend: {{ data: ['偏航角速度', '偏航角加速度'], textStyle: {{ color: '#8892a4', fontSize: 12 }}, top: 4, left: 0 }},
        series: [
            {{ name: '偏航角速度', type: 'line', data: D.t.map(function(t,i){{return [t, D.wz[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#00e676' }}, areaStyle: {{ color: 'rgba(0,230,118,0.06)' }} }},
            {{ name: '偏航角加速度', type: 'line', data: D.t.map(function(t,i){{return [t, D.waz[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ff6b35', opacity: 0.7 }} }}
        ]
    }};
}}

function makeRoadOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0]; var s = '<b>' + timeLabel(t) + '</b><br/>';
            ps.forEach(function(p) {{ s += p.marker + ' ' + p.seriesName + ': ' + p.data[1].toFixed(4) + '<br/>'; }});
            return s;
        }} }},
        grid: {{ left: 56, right: 56, top: 12, bottom: 28 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: [
            {{ type: 'value', name: '曲率(m⁻¹)', nameTextStyle: {{ color: '#00d4ff', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
            {{ type: 'value', name: '偏移(m)', nameTextStyle: {{ color: '#ffd740', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }}
        ],
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        series: [
            {{ name: '道路曲率', type: 'line', data: D.t.map(function(t,i){{return [t, D.cur[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#00d4ff' }}, yAxisIndex: 0 }},
            {{ name: '车辆偏移', type: 'line', data: D.t.map(function(t,i){{return [t, D.off[i]];}}), smooth: true, showSymbol: false, sampling: 'lttb', lineStyle: {{ width: 2, color: '#ffd740', opacity: 0.7 }}, yAxisIndex: 1 }}
        ]
    }};
}}

function makeMileageOption(D) {{
    return {{
        backgroundColor: 'transparent',
        tooltip: {{ trigger: 'axis', formatter: function(ps) {{
            var t = ps[0].data[0];
            return '<b>' + timeLabel(t) + '</b><br/>' + ps[0].marker + ' 里程: ' + ps[0].data[1].toFixed(4) + ' km';
        }} }},
        grid: {{ left: 56, right: 20, top: 12, bottom: 28 }},
        xAxis: {{ type: 'value', show: true, axisLabel: {{ formatter: timeLabel, color: '#8892a4', fontSize: 11 }}, splitLine: {{ show: false }} }},
        yAxis: {{ type: 'value', name: '里程(km)', nameTextStyle: {{ color: '#8892a4', fontSize: 12 }}, axisLabel: {{ color: '#8892a4', fontSize: 11 }}, splitLine: {{ lineStyle: {{ color: '#1e2634' }} }} }},
        dataZoom: [{{ type: 'inside', xAxisIndex: 0 }}],
        series: [{{
            name: '里程', type: 'line',
            data: D.t.map(function(t,i){{return [t, D.mil[i]];}}),
            smooth: true, showSymbol: false, sampling: 'lttb',
            lineStyle: {{ width: 2, color: '#00e676' }},
            areaStyle: {{ color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [{{offset:0,color:'rgba(0,230,118,0.2)'}},{{offset:1,color:'rgba(0,230,118,0.02)'}}] }} }}
        }}]
    }};
}}

// 选项生成函数列表 (与 chartIds 一一对应)
var optionMakers = [
    makeTrajectoryOption, makeSpeedOption, makeAccelOption, makeAttitudeOption, makeRadarOption,
    makePowertrainOption, makeControlsOption, makeAngularOption, makeRoadOption, makeMileageOption
];

// =====================================================
// 图表管理器
// =====================================================
var chartInstances = {{}};

function initCharts(data) {{
    for (var i = 0; i < chartIds.length; i++) {{
        var id = chartIds[i];
        var chart = echarts.init(document.getElementById(id));
        chart.setOption(optionMakers[i](data));
        chartInstances[id] = chart;
    }}
    // 统一 resize
    window.addEventListener('resize', function() {{
        for (var key in chartInstances) {{
            if (chartInstances.hasOwnProperty(key)) {{
                chartInstances[key].resize();
            }}
        }}
    }});
}}

function updateCharts(data) {{
    for (var i = 0; i < chartIds.length; i++) {{
        var id = chartIds[i];
        var chart = chartInstances[id];
        if (chart) {{
            chart.setOption(optionMakers[i](data), true);
        }}
    }}
}}

function updateStats(data) {{
    var n = data.t.length;
    var maxS = 0, sumV = 0;
    for (var i = 0; i < n; i++) {{ if (data.vx[i] > maxS) maxS = data.vx[i]; sumV += data.vx[i]; }}
    var maxAcc = data.ax[0], minAcc = data.ax[0];
    var maxLat = 0;
    for (var i = 0; i < n; i++) {{
        if (data.ax[i] > maxAcc) maxAcc = data.ax[i];
        if (data.ax[i] < minAcc) minAcc = data.ax[i];
        var la = Math.abs(data.ay[i]); if (la > maxLat) maxLat = la;
    }}
    var dist = data.mil[n-1] - data.mil[0];
    document.getElementById('stat-duration').textContent = (n / 40) + 's';
    document.getElementById('stat-maxspeed').textContent = (maxS * 3.6).toFixed(1);
    document.getElementById('stat-maxaccel').textContent = maxAcc.toFixed(2);
    document.getElementById('stat-latg').textContent = maxLat.toFixed(2);
    document.getElementById('stat-mileage').textContent = dist.toFixed(3);
    document.getElementById('stat-frames').textContent = n;
}}

// =====================================================
// CSV 解析
// =====================================================
function parseCSV(csvText) {{
    var lines = csvText.trim().split('\\n');
    if (lines.length < 2) return null;
    var n = lines.length - 1;
    var parseNum = function(v) {{ var x = parseFloat(v); return isNaN(x) ? 0 : x; }};
    var D = {{ t: new Array(n), x: new Array(n), y: new Array(n), z: new Array(n),
        p: new Array(n), yaw: new Array(n), r: new Array(n),
        vx: new Array(n), vy: new Array(n),
        ax: new Array(n), ay: new Array(n), az: new Array(n),
        rpm: new Array(n), spd: new Array(n), gear: new Array(n),
        thr: new Array(n), brk: new Array(n), str: new Array(n), park: new Array(n),
        wz: new Array(n), waz: new Array(n),
        cur: new Array(n), off: new Array(n), mil: new Array(n) }};
    for (var i = 0; i < n; i++) {{
        var cols = lines[i+1].split(',');
        D.t[i] = i * 0.025;
        D.x[i] = parseNum(cols[2]);   D.y[i] = parseNum(cols[3]);   D.z[i] = parseNum(cols[4]);
        D.p[i] = parseNum(cols[5]);   D.yaw[i] = parseNum(cols[6]); D.r[i] = parseNum(cols[7]);
        D.vx[i] = parseNum(cols[14]); D.vy[i] = parseNum(cols[15]);
        D.ax[i] = parseNum(cols[11]); D.ay[i] = parseNum(cols[12]); D.az[i] = parseNum(cols[13]);
        D.rpm[i] = parseNum(cols[23]); D.spd[i] = parseNum(cols[24]); D.gear[i] = Math.round(parseNum(cols[25]));
        D.thr[i] = parseNum(cols[28]); D.brk[i] = parseNum(cols[29]); D.str[i] = parseNum(cols[27]); D.park[i] = parseNum(cols[30]);
        D.wz[i] = parseNum(cols[19]);  D.waz[i] = parseNum(cols[22]);
        D.cur[i] = parseNum(cols[9]);  D.off[i] = parseNum(cols[8]); D.mil[i] = parseNum(cols[26]);
    }}
    return D;
}}

// =====================================================
// 文件选择
// =====================================================
document.getElementById('csvFile').addEventListener('change', function(e) {{
    var file = e.target.files[0];
    if (!file) return;
    document.getElementById('currentFile').textContent = file.name;
    var reader = new FileReader();
    reader.onload = function(ev) {{
        var data = parseCSV(ev.target.result);
        if (!data || data.t.length < 10) {{
            alert('无法解析CSV文件，请确保格式正确');
            return;
        }}
        updateStats(data);
        updateCharts(data);
    }};
    reader.readAsText(file, 'UTF-8');
}});

// =====================================================
// 启动
// =====================================================
initCharts(DEFAULT_DATA);
</script>
</body>
</html>'''

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

import os
size_kb = os.path.getsize(OUTPUT_PATH) / 1024
print(f'仪表盘已生成: {OUTPUT_PATH}')
print(f'文件大小: {size_kb:.0f} KB | 数据帧数: {n} | 列数: {len(headers)}')
print('新增: CSV文件选择器(点击"选择CSV文件"按钮加载其他历史数据)')
print('修复: 字号增大2号, 雷达图乱码修复, 雷达图不溢出')
