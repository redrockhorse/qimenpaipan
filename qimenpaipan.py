# 奇门遁甲排盘

from datetime import  datetime, timezone, timedelta
from skyfield.api import load, Topos
from skyfield.units import Angle
import bisect
# 初始化天文数据
load.directory = './'  # 从当前目录加载星历文件
ts = load.timescale()
eph = load('de421.bsp')

# 定义节气与黄经对应表
solar_terms = [
    ('立春', 315), ('雨水', 330), ('惊蛰', 345), ('春分', 0),
    ('清明', 15), ('谷雨', 30), ('立夏', 45), ('小满', 60),
    ('芒种', 75), ('夏至', 90), ('小暑', 105), ('大暑', 120),
    ('立秋', 135), ('处暑', 150), ('白露', 165), ('秋分', 180),
    ('寒露', 195), ('霜降', 210), ('立冬', 225), ('小雪', 240),
    ('大雪', 255), ('冬至', 270), ('小寒', 285), ('大寒', 300)
]

# 根据输入时间获取太阳黄经度数
def get_solar_longitude(year, month, day, hour=0, minute=0, second=0):
    # 创建时间对象
    t = ts.utc(year, month, day, hour, minute, second)
    # 获取天体位置
    sun = eph['sun']
    earth = eph['earth']
    astrometric = earth.at(t).observe(sun)
    # 转换黄道坐标系
    lat, lon, _ = astrometric.ecliptic_latlon(t)
    return lon.degrees


sorted_terms = sorted(solar_terms, key=lambda x: x[1])

# 根据输入的太阳黄经度数，查找临近的节气
def find_closest_terms(angle):
    angle %= 360
    angles = [term[1] for term in sorted_terms]
    idx = bisect.bisect_right(angles, angle)
    
    # 确定相邻索引（环形处理）
    left_idx = (idx - 1) % len(sorted_terms)
    right_idx = idx % len(sorted_terms)
    
    left_name, left_angle = sorted_terms[left_idx]
    right_name, right_angle = sorted_terms[right_idx]
    
    # 直接返回黄经顺序相邻的节气对
    return [left_name, right_name]

# 获取输入年份的立春准确时间
def find_lichun(year):
    # 设置搜索范围（2月前后）
    start = ts.utc(year, 2, 1)
    end = ts.utc(year, 2, 15)
    
    # 定义黄经检测函数
    def sun_longitude(t):
        astro = eph['earth'].at(t).observe(eph['sun'])
        lat, lon, _ = astro.ecliptic_latlon()
        return lon.degrees
    # 二分法查找黄经315度的时刻
    t0, t1 = start, end
    for _ in range(20):  # 迭代20次达微秒精度
        tm = ts.tt_jd((t0.tt + t1.tt) / 2)
        if sun_longitude(tm) >= 315:
            t1 = tm
        else:
            t0 = tm
    return t1.utc_datetime()

# 获取年干支
def get_year_ganzhi(input_datetime):
    year = input_datetime.year
    # 获取当前年和前一年的立春时间
    lichun_current = find_lichun(year)
    # 判断输入日期是否在当前年立春之后
    if input_datetime >= lichun_current:
        calc_year = year
    else:
        calc_year = year - 1
    # 天干地支表
    tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    idx = (calc_year - 4) % 60
    return tiangan[idx % 10] + dizhi[idx % 12]

# 在之前的代码基础上添加以下内容

# 节气名称与黄经度数、月份的对应关系
jieqi_info = [
    (315, 2, '立春'), (330, 2, '雨水'), (345, 3, '惊蛰'), (0, 3, '春分'),
    (15, 4, '清明'), (30, 4, '谷雨'), (45, 5, '立夏'), (60, 5, '小满'),
    (75, 6, '芒种'), (90, 6, '夏至'), (105, 7, '小暑'), (120, 7, '大暑'),
    (135, 8, '立秋'), (150, 8, '处暑'), (165, 9, '白露'), (180, 9, '秋分'),
    (195, 10, '寒露'), (210, 10, '霜降'), (225, 11, '立冬'), (240, 11, '小雪'),
    (255, 12, '大雪'), (270, 12, '冬至'), (285, 1, '小寒'), (300, 1, '大寒')
]

# 节气名称到索引的映射
jieqi_order = {name: idx for idx, (_, _, name) in enumerate(jieqi_info)}

# 年干对应正月天干规则
gan_to_start = {
    '甲': '丙', '己': '丙',
    '乙': '戊', '庚': '戊',
    '丙': '庚', '辛': '庚',
    '丁': '壬', '壬': '壬',
    '戊': '甲', '癸': '甲'
}

# 修正后的get_jieqi_time函数（关键修改部分）
def get_jieqi_time(year, target_degree):
    """ 计算指定年份特定黄经度数对应的节气时间 """
    # 根据黄经度数确定对应的月份
    for degree, month, _ in jieqi_info:
        if degree == target_degree:
            break
    
    # 修正月份范围设置
    start_year = year
    start_month = month - 1
    if start_month < 1:
        start_month = 12
        start_year -= 1
    
    end_year = year
    end_month = month + 1
    if end_month > 12:
        end_month = 1
        end_year += 1
    
    # 创建时间范围（前后各扩展一个月）
    start = ts.utc(start_year, start_month, 1)
    end = ts.utc(end_year, end_month, 1)

    # 二分法查找
    def sun_longitude(t):
        astro = eph['earth'].at(t).observe(eph['sun'])
        return astro.ecliptic_latlon()[1].degrees % 360

    t0, t1 = start, end
    for _ in range(20):
        tm = ts.tt_jd((t0.tt + t1.tt) / 2)
        if sun_longitude(tm) >= target_degree % 360:
            t1 = tm
        else:
            t0 = tm
    return t1.utc_datetime()

# 根据输入的时间找到对应的节气
def find_jieqi(input_dt):
    """ 找到输入时间对应的节气及索引 """
    # 生成前后两年所有节气时间
    jieqi_events = []
    for y in [input_dt.year - 1, input_dt.year]:
        for degree, _, name in jieqi_info:
            jt = get_jieqi_time(y, degree)
            jieqi_events.append( (jt, name) )
    
    # 按时间排序并找到最后一个小于等于输入时间的节气
    jieqi_events.sort(key=lambda x: x[0])
    for i in range(len(jieqi_events)-1, -1, -1):
        if jieqi_events[i][0] <= input_dt:
            return jieqi_events[i]
    return None

# 获取月干支
def get_yue_ganzhi(input_dt):
    """ 计算月干支 """
    # 获取年干
    year_gan = get_year_ganzhi(input_dt)[0]
    
    # 获取对应节气及索引
    jieqi_time, jieqi_name = find_jieqi(input_dt)
    # print(jieqi_time, jieqi_name)
    idx = jieqi_order[jieqi_name]
    month_num = idx // 2  # 0-11对应正月到腊月
    
    # 计算天干地支
    tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    
    start_gan = gan_to_start[year_gan]
    gan_idx = (tiangan.index(start_gan) + month_num) % 10
    zhi_idx = (month_num + 2) % 12  # 正月寅=2
    
    return tiangan[gan_idx] + dizhi[zhi_idx]

from datetime import datetime, timedelta

# 获取日时干支
def get_day_houre_ganzhi(input_str):
    # 解析输入时间 [[5]]
    dt = datetime.strptime(input_str, "%Y-%m-%d %H:%M:%S")
    
    # 调整日期：23点后算下一天 [[1]]
    if dt.hour >= 23:
        adjusted_date = dt.date() + timedelta(days=1)
    else:
        adjusted_date = dt.date()
    
    # ------------ 日干支计算 ------------
    # 基准日需按实际情况调整！示例基准：2025-02-24为甲子日
    base_date = datetime(2025, 2, 24).date()
    days_diff = (adjusted_date - base_date).days
    ganzhi_index = days_diff % 60  # 干支60一轮回
    
    gan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    zhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    ri_gan = gan[ganzhi_index % 10]
    ri_zhi = zhi[ganzhi_index % 12]
    ri_gz = f"{ri_gan}{ri_zhi}"
    
    # ------------ 时干支计算 ------------
    h = dt.hour
    # 确定时支（23点属于次日子时）
    if h == 23:
        h = 24  # 便于计算时辰索引
    zhi_index = (h + 1) // 2 % 12  # 时支索引 [[3]]
    shi_zhi = zhi[zhi_index]
    
    # 根据日干确定时干起始（甲己日甲子，乙庚日丙子...）
    ri_gan_idx = gan.index(ri_gan)
    if ri_gan_idx in [0, 5]:   start = 0  # 甲/己
    elif ri_gan_idx in [1,6]:  start = 2  # 乙/庚→丙
    elif ri_gan_idx in [2,7]:  start = 4  # 丙/辛→戊
    elif ri_gan_idx in [3,8]:  start = 6  # 丁/壬→庚
    else:                      start = 8  # 戊/癸→壬
    
    shi_gan = gan[(start + zhi_index) % 10]
    shi_gz = f"{shi_gan}{shi_zhi}"
    
    return ri_gz, shi_gz

# 获取年月日时的干支
def get_full_ganzhi(datetime_str):
    """
    输入日期时间字符串，返回完整的年月日时干支
    参数:
        datetime_str: 格式为 "YYYY-MM-DD HH:MM:SS" 的字符串
    返回:
        tuple: (年干支, 月干支, 日干支, 时干支)
    """
    # 解析输入时间字符串为datetime对象
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    # 转换为UTC时间（因为天文计算需要）
    dt_utc = dt.replace(tzinfo=timezone.utc)
    
    # 获取年干支
    year_gz = get_year_ganzhi(dt_utc)
    
    # 获取月干支
    month_gz = get_yue_ganzhi(dt_utc)
    
    # 获取日时干支
    day_gz, hour_gz = get_day_houre_ganzhi(datetime_str)
    
    return (year_gz, month_gz, day_gz, hour_gz)


def get_futou_details(day_ganzhi, method='置闰'):
    """
    根据日干支和定局方法计算符头、三元及距离天数
    :param day_ganzhi: 日干支，如"甲子"
    :param method: 定局方法，"置闰" 或 "拆补"
    :return: 字典包含符头、三元、距离天数
    """
    # 生成干支表（60甲子）
    gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    ganzhi = [f"{gan[i%10]}{zhi[i%12]}" for i in range(60)]
    ganzhi_map = {gz:i for i,gz in enumerate(ganzhi)}

    # 校验输入合法性
    if day_ganzhi not in ganzhi_map:
        raise ValueError("无效的日干支")
    current_idx = ganzhi_map[day_ganzhi]

    # 逆向查找符头
    futou, days_ago = None, 0
    for steps in range(60):
        check_idx = (current_idx - steps) % 60
        check_gz = ganzhi[check_idx]

        # 置闰法：仅匹配甲子、甲午、己卯、己酉
        if method == '置闰' and check_gz in {'甲子','甲午','己卯','己酉'}:
            futou = check_gz
            days_ago = steps
            break

        # 拆补法：匹配所有甲/己日
        if method == '拆补' and check_gz[0] in {'甲','己'}:
            futou = check_gz
            days_ago = steps
            break

    # 确定三元
    zhi_type = {
        '子':'上元', '午':'上元', '卯':'上元', '酉':'上元',
        '寅':'中元', '申':'中元', '巳':'中元', '亥':'中元',
        '辰':'下元', '戌':'下元', '丑':'下元', '未':'下元'
    }[futou[1]]

    return {'符头': futou, '上中下元': zhi_type, '距离天数': days_ago}

def calculate_qimen_info(datetime_str):
    """
    输入日期时间，计算奇门遁甲所需的基本信息
    参数:
        datetime_str: 格式为 "YYYY-MM-DD HH:MM:SS" 的字符串
    返回:
        dict: 包含年月日时干支、节气、符头等信息的字典
    """
    # 解析输入时间
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    dt_utc = dt.replace(tzinfo=timezone.utc)
    
    # 获取年月日时干支
    year_gz, month_gz, day_gz, hour_gz = get_full_ganzhi(datetime_str)
    
    # 获取节气信息
    jieqi_time, jieqi_name = find_jieqi(dt_utc)
    
    # 获取符头详情
    futou_info = get_futou_details(day_gz, method='置闰')
    
    # 计算符头对应的日期
    futou_date = dt.date() - timedelta(days=futou_info['距离天数'])
    
    return {
        '输入时间': datetime_str,
        '年干支': year_gz,
        '月干支': month_gz,
        '日干支': day_gz,
        '时干支': hour_gz,
        '当前节气': jieqi_name,
        '节气时间': jieqi_time.strftime("%Y-%m-%d %H:%M:%S"),
        '符头': futou_info['符头'],
        '三元': futou_info['上中下元'],
        '符头距今': f"{futou_info['距离天数']}天",
        '符头日期': futou_date.strftime("%Y-%m-%d")
    }


"""
奇门遁甲定局数算法伪代码实现
核心步骤：
1. 判断节气与阴阳遁
2. 定位符头与确定三元
3. 处理符头与节气关系
4. 置闰调整规则
"""

from datetime import datetime
from typing import Tuple

# ================== 基础工具函数 ==================
def get_solar_term(date: datetime) -> Tuple[str, bool]:
    """获取日期所属节气及阴阳遁状态（伪实现）
    Args:
        date: 输入日期
    Returns:
        (节气名称, 是否阳遁)
    [[[1]][[3]][[6]]] 阳遁：冬至到夏至，阴遁：夏至到冬至
    """
    # 实际应接入节气计算库，此处示例返回立春与阳遁
    return ("立春", True) if date.month >= 2 else ("冬至", True)

def ganzhi_to_dizhi(ganzhi: str) -> str:
    """提取干支中的地支（伪实现）"""
    return ganzhi[1]  # 假设干支格式如"甲子"

def get_previous_jia_ji(date: datetime) -> datetime:
    """向前追溯最近的甲/己日（符头定位核心算法）
    [[[37]]] 符头为最近的甲或己日
    """
    current = date
    while True:
        # 实际需要计算日干支，此处简化逻辑
        if current.day % 10 in [0, 5]:  # 假设甲日为0，己日为5
            return current
        current -= timedelta(days=1)

# ================== 核心算法步骤 ==================
def determine_ju_number(datetime_str: str) -> dict:
    """
    根据输入日期时间确定奇门遁甲的局数
    Args:
        datetime_str: 格式为 "YYYY-MM-DD HH:MM:SS" 的字符串
    Returns:
        dict: 包含节气、遁局、三元、局数等信息的字典
    """
    # 解析输入时间
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    
    # 获取基本信息（包含节气信息）
    basic_info = calculate_qimen_info(datetime_str)
    solar_term = basic_info['当前节气']
    
    # === 步骤1：确定节气与阴阳遁 ===
    # 判断阴阳遁：冬至到夏至为阳遁，夏至到冬至为阴遁
    winter_solstice_deg = 270  # 冬至黄经
    summer_solstice_deg = 90   # 夏至黄经
    
    # 获取当前太阳黄经
    current_lon = get_solar_longitude(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    
    # 判断阴阳遁
    if winter_solstice_deg <= current_lon < summer_solstice_deg or current_lon >= winter_solstice_deg:
        is_yang = True  # 阳遁
    else:
        is_yang = False  # 阴遁
    
    # === 步骤2：定位符头与三元 ===
    # 直接使用basic_info中的符头信息
    fu_tou = basic_info['符头']
    current_yuan = basic_info['三元']
    fu_tou_date = datetime.strptime(basic_info['符头日期'], "%Y-%m-%d").date()
    
    # === 步骤3：处理符头与节气关系 ===
    # 获取当前节气的开始时间
    current_term_start = datetime.strptime(basic_info['节气时间'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=None)
    
    # 计算符头与节气开始日期的天数差
    days_diff = (fu_tou_date - current_term_start.date()).days
    
    # 确定节气关系和生效节气
    effective_term = solar_term  # 直接使用当前节气作为生效节气
    
    # 仅记录关系，但不影响生效节气
    if days_diff == 0:
        relation = "正授"
    elif days_diff < 0:
        relation = "超神"
    else:
        relation = "接气"
    
    # === 步骤4：置闰调整 ===
    # 超过9天触发置闰条件
    if abs(days_diff) > 9:
        if solar_term in ["芒种", "大雪"]:
            # 重复前一节气的中/下元
            if current_yuan == "下元":
                current_yuan = "中元"
            elif current_yuan == "中元":
                current_yuan = "下元"
    
    # === 局数映射表 ===
    # 阳遁局数表
    yang_ju_mapping = {
        "冬至": {"上元": 1, "中元": 7, "下元": 4},
        "小寒": {"上元": 2, "中元": 8, "下元": 5},
        "大寒": {"上元": 3, "中元": 9, "下元": 6},
        "立春": {"上元": 8, "中元": 5, "下元": 2},
        "雨水": {"上元": 9, "中元": 6, "下元": 3},
        "惊蛰": {"上元": 1, "中元": 7, "下元": 4},
        "春分": {"上元": 3, "中元": 9, "下元": 6},
        "清明": {"上元": 4, "中元": 1, "下元": 7},
        "谷雨": {"上元": 5, "中元": 2, "下元": 8},
        "立夏": {"上元": 4, "中元": 1, "下元": 7},
        "小满": {"上元": 5, "中元": 2, "下元": 8},
        "芒种": {"上元": 6, "中元": 3, "下元": 9}
    }
    
    # 阴遁局数表
    yin_ju_mapping = {
        "夏至": {"上元": 9, "中元": 3, "下元": 6},
        "小暑": {"上元": 8, "中元": 2, "下元": 5},
        "大暑": {"上元": 7, "中元": 1, "下元": 4},
        "立秋": {"上元": 2, "中元": 5, "下元": 8},
        "处暑": {"上元": 1, "中元": 4, "下元": 7},
        "白露": {"上元": 9, "中元": 3, "下元": 6},
        "秋分": {"上元": 7, "中元": 6, "下元": 5},
        "寒露": {"上元": 6, "中元": 5, "下元": 4},
        "霜降": {"上元": 5, "中元": 4, "下元": 3},
        "立冬": {"上元": 6, "中元": 5, "下元": 4},
        "小雪": {"上元": 5, "中元": 8, "下元": 3},
        "大雪": {"上元": 4, "中元": 3, "下元": 2}
    }
    
    # 根据阴阳遁选择对应的局数表
    ju_mapping = yang_ju_mapping if is_yang else yin_ju_mapping
    
    # 获取局数
    ju_number = ju_mapping.get(effective_term, {}).get(current_yuan, 0)
    
    # 添加调试信息
    print(f"当前节气: {solar_term}, 生效节气: {effective_term}, 三元: {current_yuan}, 局数: {ju_number}")
    
    return {
        "节气": effective_term,
        "遁局": "阳遁" if is_yang else "阴遁",
        "元": current_yuan,
        "局数": ju_number,
        "关系": relation,
        "符头": fu_tou,
        "符头日期": basic_info['符头日期'],
        "节气开始日期": basic_info['节气时间'],
        "天数差": days_diff
    }

# 扩展calculate_qimen_info函数，加入局数信息
def calculate_qimen_info_with_ju(datetime_str):
    """
    输入日期时间，计算奇门遁甲所需的基本信息，包括局数
    参数:
        datetime_str: 格式为 "YYYY-MM-DD HH:MM:SS" 的字符串
    返回:
        dict: 包含年月日时干支、节气、符头、局数等信息的字典
    """
    # 获取基本信息
    basic_info = calculate_qimen_info(datetime_str)
    
    # 获取局数信息
    ju_info = determine_ju_number(datetime_str)
    
    # 合并信息
    result = {**basic_info, **ju_info}
    
    return result

"""
奇门遁甲排盘核心算法
包含：
1. 三奇六仪排列
2. 地盘/天盘布局
3. 八门九星布列
4. 八神飞布
"""

from collections import deque

# ================== 基础数据定义 ==================
# 九宫方位映射（洛书数序）
PALACE_MAP = {
    1: ("坎", "北"), 8: ("艮", "东北"), 3: ("震", "东"),
    4: ("巽", "东南"), 9: ("离", "南"), 2: ("坤", "西南"),
    7: ("兑", "西"), 6: ("乾", "西北"), 5: ("中", "中央")
}

# 三奇六仪顺序（阳遁顺排，阴遁逆排）
QIYI_ORDER = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]

# 八门顺序（休生伤杜景死惊开）
MEN_ORDER = ["休","生","伤","杜","景","死","惊","开"]

# 九星顺序（天蓬到天英）
STAR_ORDER = ["天蓬","天任","天冲","天辅","天英","天芮","天柱","天心"]

# 八神顺序（值符到太阴）
SHEN_ORDER = ["值符","腾蛇","太阴","六合","白虎","玄武","九地","九天"]

# ================== 核心排盘类 ==================
class QimenPan:
    def __init__(self, ju_number: int, is_yang: bool, current_time: datetime):
        self.ju_number = ju_number  # 当前局数（1-18）
        self.is_yang = is_yang      # 阴阳遁
        self.time = current_time    # 排盘时间
        
        # 初始化九宫数据结构
        self.palaces = {num: {
            'earth': None,  # 地盘仪
            'sky': None,    # 天盘仪
            'door': None,    # 八门
            'star': None,    # 九星
            'shen': None     # 八神
        } for num in PALACE_MAP}
        
    # ------------------ 核心排布方法 ------------------
    def arrange_earth_plate(self):
        """排列地盘（固定三奇六仪）"""
        start_idx = (self.ju_number - 1) % 9
        order = QIYI_ORDER if self.is_yang else QIYI_ORDER[::-1]
        
        # 按洛书数序排布
        positions = [1,8,3,4,9,2,7,6,5]  # 阳遁顺行路线
        if not self.is_yang:
            positions = positions[::-1]  # 阴遁逆行路线
            
        for i, pos in enumerate(positions):
            self.palaces[pos]['earth'] = order[(start_idx + i) % 9]

    def arrange_sky_plate(self, shigan: str):
        """排列天盘（时干对应）"""
        # 获取值符
        zhifu = "戊"  # 值符固定为戊
        
        # 找到值符初始位置（戊在地盘的位置）
        # 先检查地盘是否已排好
        if all(self.palaces[pos]['earth'] is None for pos in PALACE_MAP):
            self.arrange_earth_plate()  # 如果地盘未排，先排地盘
            
        # 查找戊在地盘的位置
        start_pos = None
        for pos, data in self.palaces.items():
            if data['earth'] == zhifu:
                start_pos = pos
                break
                
        # 如果找不到，使用默认位置
        if start_pos is None:
            start_pos = 5  # 默认中宫
            print("警告：地盘中未找到值符'戊'，使用中宫作为默认位置")
        
        # 旋转天盘到时干位置
        target_pos = self.get_shigan_position(shigan)
        rotation = (target_pos - start_pos) % 9
        
        # 旋转三奇六仪
        qiyi = []
        for pos in [1,8,3,4,9,2,7,6,5]:  # 按洛书数序
            qiyi.append(self.palaces[pos]['earth'])
            
        # 使用deque进行旋转
        qiyi_deque = deque(qiyi)
        qiyi_deque.rotate(rotation)
        
        # 更新天盘
        for i, pos in enumerate([1,8,3,4,9,2,7,6,5]):
            self.palaces[pos]['sky'] = qiyi_deque[i]

    def arrange_doors(self, zhishi: str):
        """排列八门核心算法"""
        # 确定直使起始宫
        start_pos = self.ju_number % 8 or 8
        
        # 按时辰推移（示例：每个时辰移动一宫）
        time_diff = (self.time.hour // 2)  # 时辰数
        offset = (start_pos + time_diff - 1) % 8
        
        # 八门布列
        men_order = deque(MEN_ORDER)
        men_order.rotate(-offset)
        
        # 跳过中宫（第五宫）
        positions = [pos for pos in PALACE_MAP if pos != 5]
        for pos, men in zip(positions, men_order):
            self.palaces[pos]['door'] = men

    def arrange_stars_and_shens(self):
        """排列九星八神"""
        # 值符星固定为天蓬星
        zhifu_star = "天蓬"
        
        # 找到值符（戊）在天盘的位置
        zhifu_pos = None
        for pos, data in self.palaces.items():
            if data['sky'] == "戊":
                zhifu_pos = pos
                break
                
        # 如果找不到，使用默认位置
        if zhifu_pos is None:
            zhifu_pos = 5  # 默认中宫
            print("警告：天盘中未找到值符'戊'，使用中宫作为默认位置")
        
        # 九星布列（按洛书数序）
        positions = [1,8,3,4,9,2,7,6,5]  # 洛书数序
        if not self.is_yang:
            positions = positions[::-1]  # 阴遁逆行
            
        # 计算天蓬星在洛书中的位置索引
        zhifu_idx = positions.index(zhifu_pos)
        
        # 九星顺布
        for i, pos in enumerate(positions):
            if pos == 5:  # 中宫不布九星
                continue
                
            # 计算当前宫位应放哪个星
            star_idx = (i - zhifu_idx) % 8
            if star_idx < 0:
                star_idx += 8
            self.palaces[pos]['star'] = STAR_ORDER[star_idx]
        
        # 八神布列
        # 值符神固定在值符星所在宫
        self.palaces[zhifu_pos]['shen'] = "值符"
        
        # 其余八神按阴阳遁顺逆布列
        shen_order = SHEN_ORDER[1:]  # 除值符外的七神
        shen_positions = [p for p in positions if p != zhifu_pos and p != 5]  # 除值符宫和中宫外的宫位
        
        # 根据阴阳遁确定顺序
        if not self.is_yang:
            shen_order = shen_order[::-1]
            
        # 布列八神
        for i, pos in enumerate(shen_positions):
            if i < len(shen_order):
                self.palaces[pos]['shen'] = shen_order[i]

    # ------------------ 辅助方法 ------------------
    def get_xunshou(self):
        """获取旬首（六甲旬首）"""
        # 在实际应用中，应该根据日干支计算旬首
        # 此处简化为固定返回"戊"作为值符
        return "戊"

    def get_shigan_position(self, shigan: str) -> int:
        """获取时干对应的宫位"""
        # 简化示例：甲乙属木对应震3宫
        gan_positions = {
            '甲':3, '乙':3, '丙':9, '丁':9, 
            '戊':5, '己':5, '庚':7, '辛':7, 
            '壬':1, '癸':1
        }
        return gan_positions.get(shigan[0], 5)

    def print_pan(self):
        """可视化输出盘面"""
        print("【奇门遁甲排盘】")
        print(f"时间：{self.time} 局数：{self.ju_number} 遁：{'阳' if self.is_yang else '阴'}")
        for pos in [1,8,3,4,9,2,7,6,5]:
            palace = self.palaces[pos]
            print(f"{PALACE_MAP[pos][0]}宫({pos}): "
                  f"地:{palace['earth']} 天:{palace['sky']} "
                  f"门:{palace['door']} 星:{palace['star']} 神:{palace['shen']}")

if __name__ == '__main__':
    test_time = "2025-02-28 15:30:00"
    result = calculate_qimen_info_with_ju(test_time)
    for key, value in result.items():
        print(f"{key}: {value}")
    
    # 初始化排盘对象
    pan = QimenPan(
        ju_number=result['局数'],
        is_yang=result['遁局'] == '阳遁',
        current_time=datetime.strptime(test_time, "%Y-%m-%d %H:%M:%S")
    )
    
    # 逐步排布
    pan.arrange_earth_plate()   # 布地盘
    pan.arrange_sky_plate(result['时干支'])  # 传入时干支
    pan.arrange_doors(result['日干支'])    # 传入日干支作为直使
    pan.arrange_stars_and_shens()
    
    # 输出结果
    pan.print_pan()

    