# 奇门遁甲排盘
from datetime import  datetime, timezone, timedelta
from skyfield.api import load, Topos
from skyfield.units import Angle
import bisect
# 初始化天文数据
load.directory = './'  # 从当前目录加载星历文件
ts = load.timescale()
eph = load('de421.bsp')
tiangan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
dizhi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
jieqi_info = [
    (315, 2, '立春'), (330, 2, '雨水'), (345, 3, '惊蛰'), (0, 3, '春分'),
    (15, 4, '清明'), (30, 4, '谷雨'), (45, 5, '立夏'), (60, 5, '小满'),
    (75, 6, '芒种'), (90, 6, '夏至'), (105, 7, '小暑'), (120, 7, '大暑'),
    (135, 8, '立秋'), (150, 8, '处暑'), (165, 9, '白露'), (180, 9, '秋分'),
    (195, 10, '寒露'), (210, 10, '霜降'), (225, 11, '立冬'), (240, 11, '小雪'),
    (255, 12, '大雪'), (270, 12, '冬至'), (285, 1, '小寒'), (300, 1, '大寒')
]


# 年干对应正月天干规则
gan_to_start = {
    '甲': '丙', '己': '丙',
    '乙': '戊', '庚': '戊',
    '丙': '庚', '辛': '庚',
    '丁': '壬', '壬': '壬',
    '戊': '甲', '癸': '甲'
}
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
# 节气名称到索引的映射
jieqi_order = {name: idx for idx, (_, _, name) in enumerate(jieqi_info)}
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
    idx = (calc_year - 4) % 60
    return tiangan[idx % 10] + dizhi[idx % 12]

# 根据输入的时间找到对应的节气
def find_jieqi(input_dt, forward: bool = True):
    """ 找到输入时间对应的节气及索引
    Args:
        input_dt: 输入时间
        forward: True表示向前找(找小于等于输入时间的最近节气)，
                False表示向后找(找大于输入时间的最近节气)
    Returns:
        (节气时间, 节气名称)
    """
    # 生成前后两年所有节气时间
    jieqi_events = []
    for y in [input_dt.year - 1, input_dt.year]:
        for degree, _, name in jieqi_info:
            jt = get_jieqi_time(y, degree)
            jieqi_events.append((jt, name))
    
    # 按时间排序
    jieqi_events.sort(key=lambda x: x[0])
    
    if forward:
        # 向前找：找到最后一个小于等于输入时间的节气
        for i in range(len(jieqi_events)-1, -1, -1):
            if jieqi_events[i][0] <= input_dt:
                return jieqi_events[i]
    else:
        # 向后找：找到第一个大于输入时间的节气
        for event in jieqi_events:
            if event[0] > input_dt:
                return event
                
    return None

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
    start_gan = gan_to_start[year_gan]
    gan_idx = (tiangan.index(start_gan) + month_num) % 10
    zhi_idx = (month_num + 2) % 12  # 正月寅=2
    
    return tiangan[gan_idx] + dizhi[zhi_idx]

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
    
    ri_gan = tiangan[ganzhi_index % 10]
    ri_zhi = dizhi[ganzhi_index % 12]
    ri_gz = f"{ri_gan}{ri_zhi}"
    
    # ------------ 时干支计算 ------------
    h = dt.hour
    # 确定时支（23点属于次日子时）
    if h == 23:
        h = 24  # 便于计算时辰索引
    zhi_index = (h + 1) // 2 % 12  # 时支索引 [[3]]
    shi_zhi = dizhi[zhi_index]
    
    # 根据日干确定时干起始（甲己日甲子，乙庚日丙子...）
    ri_gan_idx = tiangan.index(ri_gan)
    if ri_gan_idx in [0, 5]:   start = 0  # 甲/己
    elif ri_gan_idx in [1,6]:  start = 2  # 乙/庚→丙
    elif ri_gan_idx in [2,7]:  start = 4  # 丙/辛→戊
    elif ri_gan_idx in [3,8]:  start = 6  # 丁/壬→庚
    else:                      start = 8  # 戊/癸→壬
    
    shi_gan = tiangan[(start + zhi_index) % 10]
    shi_gz = f"{shi_gan}{shi_zhi}"
    
    return ri_gz, shi_gz


def get_solar_longitude(year, month, day, hour=0, minute=0, second=0):
    """根据输入时间获取太阳黄经度数"""
    # 创建时间对象
    t = ts.utc(year, month, day, hour, minute, second)
    # 获取天体位置
    sun = eph['sun']
    earth = eph['earth']
    astrometric = earth.at(t).observe(sun)
    # 转换黄道坐标系
    lat, lon, _ = astrometric.ecliptic_latlon(t)
    return lon.degrees

def get_solstices(year: int) -> tuple[datetime, datetime]:
    """获取指定年份的夏至和冬至时间
    
    Args:
        year: 年份
    
    Returns:
        tuple[datetime, datetime]: (夏至时间, 冬至时间)
    """
    summer_solstice = None
    winter_solstice = None
    
    for degree, _, name in jieqi_info:
        if name == '夏至':
            summer_solstice = get_jieqi_time(year, degree)
        elif name == '冬至':
            winter_solstice = get_jieqi_time(year, degree)
        
        # 如果两个至点都找到了就可以退出循环
        if summer_solstice and winter_solstice:
            break
    
    return summer_solstice, winter_solstice

def get_futou_details(day_ganzhi, method='置闰'):
    """
    根据日干支和定局方法计算符头、三元及距离天数
    :param day_ganzhi: 日干支，如"甲子"
    :param method: 定局方法，"置闰" 或 "拆补"
    :return: 字典包含符头、三元、距离天数
    """
    # 生成干支表（60甲子）
    
    ganzhi = [f"{tiangan[i%10]}{dizhi[i%12]}" for i in range(60)]
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
        zhi_type = ''
        step_day = 0
        # 置闰法：仅匹配甲子、甲午、己卯、己酉 这里定位的是上元第一天
        if method == '置闰' and check_gz in {'甲子','甲午','己卯','己酉'}:
            futou = check_gz
            days_ago = steps
            step_day = days_ago % 5 +1
            if 0 <= days_ago <= 5:
                zhi_type = "上元"
            elif 6 <= days_ago <= 10:
                zhi_type = "中元"
            elif 11 <= days_ago <= 15:
                zhi_type = "下元"
            else:
                zhi_type = "上元"
            break

        # 拆补法：匹配所有甲/己日
        if method == '拆补' and check_gz[0] in {'甲','己'}:
            futou = check_gz
            days_ago = steps
            # 确定三元
            zhi_type = {
                '子':'上元', '午':'上元', '卯':'上元', '酉':'上元',
                '寅':'中元', '申':'中元', '巳':'中元', '亥':'中元',
                '辰':'下元', '戌':'下元', '丑':'下元', '未':'下元'
            }[futou[1]]
            break

    return {'符头': futou, '上中下元': zhi_type, '符头差日': days_ago, '某元第几天': step_day}

class QiMenDunjiaPan:
    def __init__(self, input_datetime_str):
        self.input_dt = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        self.input_utc = self.input_dt.replace(tzinfo=timezone.utc)
    def calculate_ganzhi(self):
        """计算干支"""
        self.year_gz = get_year_ganzhi(self.input_utc)
        self.month_gz = get_yue_ganzhi(self.input_utc)
        self.day_gz, self.hour_gz = get_day_houre_ganzhi(self.input_dt.strftime('%Y-%m-%d %H:%M:%S'))
        print(self.year_gz,self.month_gz,self.day_gz, self.hour_gz)
    
    def calculate_futou(self):
        """计算符头日期"""
        futou_info = get_futou_details(self.day_gz)
        futou_days_diff = futou_info['符头差日']
        futou_date = datetime.combine(
            self.input_dt.date() - timedelta(days=futou_days_diff),
            self.input_dt.time(),
            tzinfo=self.input_dt.tzinfo if self.input_dt.tzinfo else None
        )
        self.futou_date = futou_date
        print(futou_date)
    
    def get_futou_jieqi(self):
        """获取符头所在的节气，夏至或者冬至"""
        print(get_solstices(self.futou_date.year))
        # 获取夏至和冬至时间
        summer_solstice, winter_solstice = get_solstices(self.futou_date.year)

        # 确保时区一致性
        futou_date_naive = self.futou_date.replace(tzinfo=None)
        summer_solstice_naive = summer_solstice.replace(tzinfo=None)
        winter_solstice_naive = winter_solstice.replace(tzinfo=None)

        # 判断符头日期在夏至和冬至的相对位置
        if futou_date_naive < summer_solstice_naive:
            # 如果在夏至前，需要获取前一年的冬至时间
            prev_summer, prev_winter = get_solstices(self.futou_date.year - 1)
            prev_winter_naive = prev_winter.replace(tzinfo=None)
            period = "夏至前"
            self.period = '冬至'
            effective_jieqi = prev_winter_naive  # 使用前一年的冬至
        elif futou_date_naive < winter_solstice_naive:
            period = "夏至后冬至前"
            self.period = '夏至'
            effective_jieqi = summer_solstice_naive  # 使用当年的夏至
        else:
            period = "冬至后"
            self.period = '冬至'
            effective_jieqi = winter_solstice_naive  # 使用当年的冬至
        

        print(f"符头日期 {self.futou_date} 在{period}")
        # 计算参考节气日期的日干支
        effective_day_ganzhi, _ = get_day_houre_ganzhi(effective_jieqi.strftime("%Y-%m-%d %H:%M:%S"))

        # 获取符头信息
        futou_info = get_futou_details(effective_day_ganzhi)

        # 计算符头日期，保持与参考节气相同的时间部分
        futou_days_diff = futou_info['符头差日']
        effective_futou_date = datetime.combine(
            effective_jieqi.date() - timedelta(days=futou_days_diff),
            effective_jieqi.time(),
            tzinfo=effective_jieqi.tzinfo
        )
        print(f"参考节气时间: {effective_jieqi}")
        print(f"参考节气日干支: {effective_day_ganzhi}")
        print(f"符头信息: {futou_info}")
        print(f"符头日期: {effective_futou_date}")
        if futou_info['符头差日'] > 9 :
            print('置闰')
            if self.period == '冬至':
               self.period = '大雪'
            if self.period == '夏至':
                self.period = '芒种'
        self.input_dt - effective_futou_date
        # 计算输入日期与符头日期的差值
        input_futou_diff = (self.input_dt.replace(tzinfo=None) - effective_futou_date.replace(tzinfo=None)).days
        print(f"输入日期与符头相差{input_futou_diff}天")
        # 计算除以15的整数部分和余数部分
        quotient, remainder = divmod(input_futou_diff, 15)
        print(f"输入日期与符头相差{input_futou_diff}天")
        print(f"除以15的结果：整数部分={quotient}，余数部分={remainder}")
        # 在节气列表中找到起始节气的索引
        start_index = None
        for i, (_, _, name) in enumerate(jieqi_info):
            if name == self.period:
                start_index = i
                break

        if start_index is not None:
            # 计算目标节气的索引（考虑循环）
            target_index = (start_index + quotient) % len(jieqi_info)
            # 获取目标节气信息
            target_degree, target_month, target_name = jieqi_info[target_index]
            
            print(f"从{self.period}开始，向后第{quotient}个节气是：{target_name}")
            self.curr_jieqi = target_name # 这里很重要，计算出了当前的真正节气
            quotient_yuan, remainder_yuan= divmod(remainder, 5)
            if quotient_yuan == 0:
                self.curr_yuan = '上元'
            if quotient_yuan == 1:
                self.curr_yuan = '中元'
            if quotient_yuan == 2:
                self.curr_yuan = '下元'
            self.remainder_yuan = remainder_yuan
            print(f"起始节气索引：{start_index}，目标节气索引：{target_index}")
            # 先检查节气是否在阳遁局数表中
            if self.curr_jieqi in yang_ju_mapping:
                self.is_yang = True
                self.ju_number = yang_ju_mapping[self.curr_jieqi][self.curr_yuan]
                print(f"阳遁{self.ju_number}局")
            # 否则检查是否在阴遁局数表中
            elif self.curr_jieqi in yin_ju_mapping:
                self.is_yang = False
                self.ju_number = yin_ju_mapping[self.curr_jieqi][self.curr_yuan]
                print(f"阴遁{self.ju_number}局")
            else:
                print(f"未找到对应的局数映射：节气={self.curr_jieqi}，元={self.curr_yuan}")
        else:
            print(f"未找到起始节气：{self.period}")


    def run(self):
        self.calculate_ganzhi()
        self.calculate_futou()
        self.get_futou_jieqi()



# 使用示例：
# year = 2024
# summer_dt, winter_dt = get_solstices(year)
# print(f"{year}年夏至：{summer_dt}")
# print(f"{year}年冬至：{winter_dt}")

if __name__ == '__main__':
    # datetime_str = "2024-11-19 01:30:00" #f8
    datetime_str = "2025-02-28 01:30:00" #t9
    qimen = QiMenDunjiaPan(datetime_str)
    qimen.run()