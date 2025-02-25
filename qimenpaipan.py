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
    print(jieqi_time, jieqi_name)
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

if __name__ == '__main__':
    test_time = "2025-02-25 15:30:00"
    result = calculate_qimen_info(test_time)
    for key, value in result.items():
        print(f"{key}: {value}")

    #https://metaso.cn/search/8582554478871019520?q=%E6%88%91%E6%83%B3%E7%94%A8python%E5%AE%9E%E7%8E%B0%E5%A5%87%E9%97%A8%E9%81%81%E7%94%B2%E6%8E%92%E7%9B%98%EF%BC%8C%E4%B8%BB%E8%A6%81%E5%AE%9E%E7%8E%B0%E7%BD%AE%E6%B6%A6%E6%B3%95%EF%BC%8C%E8%AF%B7%E7%BB%99%E5%87%BA%E5%AE%9E%E7%8E%B0%E7%9A%84%E6%AD%A5%E9%AA%A4%E3%80%82%E8%A6%81%E6%B1%82%E6%98%AF%E8%BE%93%E5%85%A5%E6%97%B6%E9%97%B4%EF%BC%8C%E8%BE%93%E5%87%BA%E6%8E%92%E7%9B%98%E7%BB%93%E6%9E%9C