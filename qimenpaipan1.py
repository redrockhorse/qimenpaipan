"""
奇门遁甲排盘系统 - 精简重构版（保持原逻辑口径）

功能：
1) 天文：立春/节气（太阳黄经二分）
2) 干支：年/月（立春/节气界）、日/时（基准甲子日、23点换日）
3) 置闰符头：符头/三元/符头差日/第几天
4) 置闰定局：阴阳遁、局数
5) 排盘：地盘(三奇六仪)、天盘、九星、八门、八神

注意：
- 仍使用你原代码的“置闰触发条件 futou_diff > 9 → period 冬至->大雪、夏至->芒种”的口径
- 仍使用“中宫寄坤(2宫)”的口径
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Dict, List, Tuple, Optional
from collections import deque
import logging

from skyfield.api import load

# -----------------------------------------------------------------------------
# logging
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 常量与工具
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class AstronomyConfig:
    EPHEMERIS_FILE: str = "de421.bsp"
    EPHEMERIS_DIR: str = "./"
    LICHUN_DEGREE: float = 315.0
    BINARY_SEARCH_ITERATIONS: int = 20


class Ganzhi:
    TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    DIZHI  = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

    TIANGAN_ORDER = {g:i for i,g in enumerate(TIANGAN)}
    DIZHI_ORDER   = {z:i for i,z in enumerate(DIZHI)}

    # 五虎遁月：年干 -> 正月天干
    YEAR_GAN_TO_MONTH_START = {
        "甲":"丙","己":"丙",
        "乙":"戊","庚":"戊",
        "丙":"庚","辛":"庚",
        "丁":"壬","壬":"壬",
        "戊":"甲","癸":"甲",
    }

    # 基准：2025-02-24 甲子日（你原代码口径）
    BASE_DATE = datetime(2025, 2, 24).date()
    BASE_YEAR = 4  # 公元4年甲子年（你原代码口径）

    # 60甲子与索引（只生成一次）
    # 注意：需要在类定义后生成，因为列表推导式的作用域问题
    JIAZI: List[str] = None  # type: ignore
    JIAZI_INDEX: Dict[str, int] = None  # type: ignore


# 在类定义后初始化 JIAZI 和 JIAZI_INDEX
Ganzhi.JIAZI = [f"{Ganzhi.TIANGAN[i%10]}{Ganzhi.DIZHI[i%12]}" for i in range(60)]
Ganzhi.JIAZI_INDEX = {gz:i for i,gz in enumerate(Ganzhi.JIAZI)}


class Jieqi:
    # (太阳黄经, 月份, 名称)
    INFO = [
        (315, 2, "立春"), (330, 2, "雨水"), (345, 3, "惊蛰"), (0, 3, "春分"),
        (15,  4, "清明"), (30,  4, "谷雨"), (45,  5, "立夏"), (60, 5, "小满"),
        (75,  6, "芒种"), (90,  6, "夏至"), (105, 7, "小暑"), (120, 7, "大暑"),
        (135, 8, "立秋"), (150, 8, "处暑"), (165, 9, "白露"), (180, 9, "秋分"),
        (195,10, "寒露"), (210,10, "霜降"), (225,11, "立冬"), (240,11, "小雪"),
        (255,12, "大雪"), (270,12, "冬至"), (285, 1, "小寒"), (300, 1, "大寒"),
    ]
    ORDER = {name:i for i, (_,_,name) in enumerate(INFO)}


class Qimen:
    PALACE_MAP = {
        1: ("坎","北"), 2: ("坤","西南"), 3: ("震","东"),
        4: ("巽","东南"), 5: ("中","中央"), 6: ("乾","西北"),
        7: ("兑","西"), 8: ("艮","东北"), 9: ("离","南"),
    }

    # 九宫（不含中宫）遍历序
    TRAVERSE_8 = [1,8,3,4,9,2,7,6]

    # 三奇六仪排布序（你的口径）
    QIYI_ORDER = ["戊","己","庚","辛","壬","癸","丁","丙","乙"]

    # 九星旋转用序（你的口径）
    STAR_ORIGIN_ARRAY = ["天蓬","天任","天冲","天辅","天英","天芮","天柱","天心"]

    # 旬首 -> 六仪
    XUNSHOU_LIUYI = {"甲子":"戊","甲戌":"己","甲申":"庚","甲午":"辛","甲辰":"壬","甲寅":"癸"}

    MEN_ORDER = ["休","生","伤","杜","景","死","惊","开"]
    SHEN_YANG = ["值符","腾蛇","太阴","六合","白虎","玄武","九地","九天"]
    SHEN_YIN  = ["值符","九天","九地","玄武","白虎","六合","太阴","腾蛇"]

    ZHIRUN_FUTOU = {"甲子","甲午","己卯","己酉"}

    YANG_JU = {
        "冬至":{"上元":1,"中元":7,"下元":4},
        "小寒":{"上元":2,"中元":8,"下元":5},
        "大寒":{"上元":3,"中元":9,"下元":6},
        "立春":{"上元":8,"中元":5,"下元":2},
        "雨水":{"上元":9,"中元":6,"下元":3},
        "惊蛰":{"上元":1,"中元":7,"下元":4},
        "春分":{"上元":3,"中元":9,"下元":6},
        "清明":{"上元":4,"中元":1,"下元":7},
        "谷雨":{"上元":5,"中元":2,"下元":8},
        "立夏":{"上元":4,"中元":1,"下元":7},
        "小满":{"上元":5,"中元":2,"下元":8},
        "芒种":{"上元":6,"中元":3,"下元":9},
    }
    YIN_JU = {
        "夏至":{"上元":9,"中元":3,"下元":6},
        "小暑":{"上元":8,"中元":2,"下元":5},
        "大暑":{"上元":7,"中元":1,"下元":4},
        "立秋":{"上元":2,"中元":5,"下元":8},
        "处暑":{"上元":1,"中元":4,"下元":7},
        "白露":{"上元":9,"中元":3,"下元":6},
        "秋分":{"上元":7,"中元":6,"下元":5},
        "寒露":{"上元":6,"中元":5,"下元":4},
        "霜降":{"上元":5,"中元":4,"下元":3},
        "立冬":{"上元":6,"中元":5,"下元":4},
        "小雪":{"上元":5,"中元":8,"下元":3},
        "大雪":{"上元":4,"中元":3,"下元":2},
    }


def _naive(dt: datetime) -> datetime:
    """统一成 naive datetime（去 tzinfo）用于比较，避免混用 tz 带来的坑。"""
    return dt.replace(tzinfo=None)


def _rotate(seq: List[str], steps: int) -> List[str]:
    d = deque(seq)
    d.rotate(steps)
    return list(d)


# -----------------------------------------------------------------------------
# 天文计算（带缓存）
# -----------------------------------------------------------------------------
load.directory = AstronomyConfig.EPHEMERIS_DIR
ts = load.timescale()
eph = load(AstronomyConfig.EPHEMERIS_FILE)


class Astronomy:
    @staticmethod
    def sun_longitude(t) -> float:
        astro = eph["earth"].at(t).observe(eph["sun"])
        _, lon, _ = astro.ecliptic_latlon()
        return lon.degrees % 360

    @staticmethod
    @lru_cache(maxsize=256)
    def find_lichun(year: int) -> datetime:
        start = ts.utc(year, 2, 1)
        end   = ts.utc(year, 2, 15)
        t0, t1 = start, end
        for _ in range(AstronomyConfig.BINARY_SEARCH_ITERATIONS):
            tm = ts.tt_jd((t0.tt + t1.tt) / 2)
            if Astronomy.sun_longitude(tm) >= AstronomyConfig.LICHUN_DEGREE:
                t1 = tm
            else:
                t0 = tm
        return t1.utc_datetime()

    @staticmethod
    @lru_cache(maxsize=4096)
    def jieqi_time(year: int, target_degree: int) -> datetime:
        # 找到该黄经对应的“标称月份”，然后向前后各扩一个月做二分范围
        month = next((m for deg, m, _ in Jieqi.INFO if deg == target_degree), 1)

        start_year, start_month = year, month - 1
        if start_month < 1:
            start_month = 12
            start_year -= 1

        end_year, end_month = year, month + 1
        if end_month > 12:
            end_month = 1
            end_year += 1

        start = ts.utc(start_year, start_month, 1)
        end   = ts.utc(end_year, end_month, 1)

        t0, t1 = start, end
        target = target_degree % 360
        for _ in range(AstronomyConfig.BINARY_SEARCH_ITERATIONS):
            tm = ts.tt_jd((t0.tt + t1.tt) / 2)
            if Astronomy.sun_longitude(tm) >= target:
                t1 = tm
            else:
                t0 = tm
        return t1.utc_datetime()

    @staticmethod
    @lru_cache(maxsize=128)
    def solstices(year: int) -> Tuple[datetime, datetime]:
        summer = Astronomy.jieqi_time(year, 90)   # 夏至
        winter = Astronomy.jieqi_time(year, 270)  # 冬至
        return summer, winter


# -----------------------------------------------------------------------------
# 干支
# -----------------------------------------------------------------------------
class GanzhiCalc:
    @staticmethod
    def year_gz(dt_utc: datetime) -> str:
        year = dt_utc.year
        lichun = Astronomy.find_lichun(year)
        calc_year = year if dt_utc >= lichun else year - 1
        idx = (calc_year - Ganzhi.BASE_YEAR) % 60
        return Ganzhi.TIANGAN[idx % 10] + Ganzhi.DIZHI[idx % 12]

    @staticmethod
    def jieqi_near(dt_utc: datetime, forward: bool = True) -> Optional[Tuple[datetime, str]]:
        # 只算三年*24，但由于 jieqi_time 有缓存，性能可接受
        events: List[Tuple[datetime, str]] = []
        for y in (dt_utc.year - 1, dt_utc.year, dt_utc.year + 1):
            for deg, _, name in Jieqi.INFO:
                events.append((Astronomy.jieqi_time(y, deg), name))
        events.sort(key=lambda x: x[0])

        if forward:
            for t, name in reversed(events):
                if t <= dt_utc:
                    return t, name
        else:
            for t, name in events:
                if t > dt_utc:
                    return t, name
        return None

    @staticmethod
    def month_gz(dt_utc: datetime) -> str:
        year_gan = GanzhiCalc.year_gz(dt_utc)[0]
        found = GanzhiCalc.jieqi_near(dt_utc, forward=True)
        if not found:
            raise ValueError("无法确定节气以计算月干支")
        _, jieqi_name = found

        idx = Jieqi.ORDER[jieqi_name]
        month_num = idx // 2  # 0..11（正月..腊月）

        start_gan = Ganzhi.YEAR_GAN_TO_MONTH_START[year_gan]
        gan_idx = (Ganzhi.TIANGAN.index(start_gan) + month_num) % 10
        zhi_idx = (month_num + 2) % 12  # 正月建寅
        return Ganzhi.TIANGAN[gan_idx] + Ganzhi.DIZHI[zhi_idx]

    @staticmethod
    def day_hour_gz(dt_local: datetime) -> Tuple[str, str]:
        # 日：23点后算下一天
        date_for_day = dt_local.date() + timedelta(days=1) if dt_local.hour >= 23 else dt_local.date()
        days_diff = (date_for_day - Ganzhi.BASE_DATE).days
        i = days_diff % 60
        day_gz = Ganzhi.JIAZI[i]

        # 时：23点归 24 方便算 (h+1)//2
        h = 24 if dt_local.hour == 23 else dt_local.hour
        zhi_index = ((h + 1) // 2) % 12
        shi_zhi = Ganzhi.DIZHI[zhi_index]

        # 五鼠遁日：按日干起时干
        ri_gan_idx = Ganzhi.TIANGAN.index(day_gz[0])
        start_map = {0:0, 5:0, 1:2, 6:2, 2:4, 7:4, 3:6, 8:6, 4:8, 9:8}
        start = start_map[ri_gan_idx]
        shi_gan = Ganzhi.TIANGAN[(start + zhi_index) % 10]
        hour_gz = shi_gan + shi_zhi
        return day_gz, hour_gz

    @staticmethod
    def xunshou(hour_gz: str) -> str:
        gan_idx = Ganzhi.TIANGAN_ORDER[hour_gz[0]]
        zhi_idx = Ganzhi.DIZHI_ORDER[hour_gz[1]]
        delta = (zhi_idx - gan_idx) % 12
        return {0:"甲子",10:"甲戌",8:"甲申",6:"甲午",4:"甲辰",2:"甲寅"}[delta]


# -----------------------------------------------------------------------------
# 符头（置闰 / 拆补）
# -----------------------------------------------------------------------------
class Futou:
    @staticmethod
    def details(day_gz: str, method: str = "置闰") -> Dict[str, object]:
        if day_gz not in Ganzhi.JIAZI_INDEX:
            raise ValueError(f"无效的日干支: {day_gz}")

        cur = Ganzhi.JIAZI_INDEX[day_gz]
        futou = None
        days_ago = 0
        yuan = "上元"
        step_day = 1

        for steps in range(60):
            gz = Ganzhi.JIAZI[(cur - steps) % 60]

            if method == "置闰" and gz in Qimen.ZHIRUN_FUTOU:
                futou = gz
                days_ago = steps
                step_day = days_ago % 5 + 1
                if 0 <= days_ago <= 5:
                    yuan = "上元"
                elif 6 <= days_ago <= 10:
                    yuan = "中元"
                elif 11 <= days_ago <= 15:
                    yuan = "下元"
                else:
                    yuan = "上元"
                break

            if method == "拆补" and gz[0] in {"甲","己"}:
                futou = gz
                days_ago = steps
                zhi2yuan = {
                    "子":"上元","午":"上元","卯":"上元","酉":"上元",
                    "寅":"中元","申":"中元","巳":"中元","亥":"中元",
                    "辰":"下元","戌":"下元","丑":"下元","未":"下元",
                }
                yuan = zhi2yuan[futou[1]]
                step_day = days_ago % 5 + 1
                break

        return {"符头": futou, "上中下元": yuan, "符头差日": days_ago, "某元第几天": step_day}


# -----------------------------------------------------------------------------
# 主排盘
# -----------------------------------------------------------------------------
class QiMenDunjiaPan:
    def __init__(self, input_datetime_str: str):
        self.input_dt = datetime.strptime(input_datetime_str, "%Y-%m-%d %H:%M:%S")
        # 你的原代码把 input_dt 强行当 UTC；这里保留，但建议你后续明确：输入究竟是本地还是UTC
        self.input_utc = self.input_dt.replace(tzinfo=timezone.utc)

        self.palaces: Dict[int, Dict[str, Optional[str]]] = {
            k: {"earth": None, "sky": None, "door": None, "star": None, "shen": None}
            for k in Qimen.PALACE_MAP.keys()
        }

        self.year_gz = self.month_gz = self.day_gz = self.hour_gz = None
        self.futou_date: Optional[datetime] = None

        self.period: Optional[str] = None
        self.curr_jieqi: Optional[str] = None
        self.curr_yuan: Optional[str] = None
        self.is_yang: Optional[bool] = None
        self.ju_number: Optional[int] = None

        self.xunshou_gz: Optional[str] = None
        self.xunshou_origin_pos: Optional[int] = None

        self.zhishi_pos: Optional[int] = None
        self.zhishi_men: Optional[str] = None

        self._earth_pos_by_gan: Dict[str, int] = {}   # 地盘排完后建立索引
        self._dipan_8: List[str] = []                 # 地盘8宫（按TRAVERSE_8）


    # ---- 1) 干支 ----
    def calculate_ganzhi(self):
        self.year_gz = GanzhiCalc.year_gz(self.input_utc)
        self.month_gz = GanzhiCalc.month_gz(self.input_utc)
        self.day_gz, self.hour_gz = GanzhiCalc.day_hour_gz(self.input_dt)
        logger.info(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")

    # ---- 2) 符头日 ----
    def calculate_futou_date(self):
        info = Futou.details(self.day_gz, method="置闰")
        diff = info["符头差日"]
        self.futou_date = datetime.combine(self.input_dt.date() - timedelta(days=diff), self.input_dt.time())
        logger.info(f"符头日期: {self.futou_date}")

    # ---- 3) 定局：节气/三元/阴阳遁/局数（沿用你现有口径） ----
    def determine_jieqi_yuan_ju(self):
        assert self.futou_date is not None

        summer, winter = Astronomy.solstices(self.futou_date.year)
        f = _naive(self.futou_date)
        s = _naive(summer)
        w = _naive(winter)

        if f < s:
            # 夏至前：参考上一年冬至
            _, prev_w = Astronomy.solstices(self.futou_date.year - 1)
            self.period = "冬至"
            effective_jieqi_dt = _naive(prev_w)
        elif f < w:
            self.period = "夏至"
            effective_jieqi_dt = _naive(summer)
        else:
            self.period = "冬至"
            effective_jieqi_dt = _naive(winter)

        # 参考节气的日干支 -> 再求其符头（置闰口径）
        eff_day_gz, _ = GanzhiCalc.day_hour_gz(effective_jieqi_dt)
        eff_futou = Futou.details(eff_day_gz, method="置闰")
        eff_diff = eff_futou["符头差日"]
        eff_futou_date = datetime.combine(effective_jieqi_dt.date() - timedelta(days=eff_diff), effective_jieqi_dt.time())

        # 置闰触发：>9 天
        if eff_diff > 9:
            logger.info("触发置闰")
            if self.period == "冬至":
                self.period = "大雪"
            elif self.period == "夏至":
                self.period = "芒种"

        # 输入日期与“参考符头日期”差（按日期00:00）
        input_00 = _naive(self.input_dt.replace(hour=0, minute=0, second=0, microsecond=0))
        futou_00 = _naive(eff_futou_date.replace(hour=0, minute=0, second=0, microsecond=0))
        diff_days = (input_00 - futou_00).days

        quotient, remainder = divmod(diff_days, 15)

        # 起始节气索引（在节气列表中定位 self.period）
        start_index = next((i for i, (_, _, name) in enumerate(Jieqi.INFO) if name == self.period), None)
        if start_index is None:
            raise ValueError(f"未找到起始节气：{self.period}")

        target_index = (start_index + quotient) % len(Jieqi.INFO)
        self.curr_jieqi = Jieqi.INFO[target_index][2]

        yuan_idx, _ = divmod(remainder, 5)
        self.curr_yuan = {0:"上元", 1:"中元", 2:"下元"}.get(yuan_idx, "上元")

        if self.curr_jieqi in Qimen.YANG_JU:
            self.is_yang = True
            self.ju_number = Qimen.YANG_JU[self.curr_jieqi][self.curr_yuan]
        elif self.curr_jieqi in Qimen.YIN_JU:
            self.is_yang = False
            self.ju_number = Qimen.YIN_JU[self.curr_jieqi][self.curr_yuan]
        else:
            raise ValueError(f"未找到局数映射：节气={self.curr_jieqi} 元={self.curr_yuan}")

        logger.info(f"节气/元: {self.curr_jieqi} {self.curr_yuan}，局：{'阳遁' if self.is_yang else '阴遁'}{self.ju_number}")

    # ---- 4) 地盘（三奇六仪） ----
    def arrange_earth(self):
        assert self.ju_number is not None and self.is_yang is not None

        start = self.ju_number
        positions = []
        cur = start
        for _ in range(9):
            positions.append(cur)
            cur = (cur % 9 + 1) if self.is_yang else ((cur - 2) % 9 + 1)

        for i, pos in enumerate(positions):
            if i < 6:
                self.palaces[pos]["earth"] = Qimen.QIYI_ORDER[i]
            else:
                self.palaces[pos]["earth"] = Qimen.QIYI_ORDER[6 + (i - 6) % 3]

        # 建立索引：天干 -> 宫位（中宫也可能出现）
        self._earth_pos_by_gan = {}
        for pos, data in self.palaces.items():
            if data["earth"]:
                self._earth_pos_by_gan[data["earth"]] = pos

        self._dipan_8 = [self.palaces[p]["earth"] for p in Qimen.TRAVERSE_8]
        logger.info("地盘排布完成")

    # ---- 5) 天盘 + 九星 ----
    def arrange_sky_and_stars(self):
        assert self.hour_gz is not None

        positions9 = Qimen.TRAVERSE_8 + [5]
        shigan = self.hour_gz[0]

        self.xunshou_gz = GanzhiCalc.xunshou(self.hour_gz)
        xunshou_liuyi = Qimen.XUNSHOU_LIUYI[self.xunshou_gz]
        origin_pos = self._earth_pos(xunshou_liuyi)
        origin_pos = 2 if origin_pos == 5 else origin_pos
        self.xunshou_origin_pos = origin_pos

        target_pos = self._earth_pos(shigan)
        target_pos = 2 if target_pos == 5 else target_pos

        steps = positions9.index(target_pos) - positions9.index(origin_pos)

        stars = deque(Qimen.STAR_ORIGIN_ARRAY)
        stars.rotate(steps)

        qiyi = deque(self._dipan_8)
        qiyi.rotate(steps)

        for i, pos in enumerate(Qimen.TRAVERSE_8):
            self.palaces[pos]["sky"] = qiyi[i]
            self.palaces[pos]["star"] = stars[i]

        self.palaces[5]["sky"] = self.palaces[5]["earth"]
        self.palaces[5]["star"] = "天禽"

        logger.info(f"旬首: {self.xunshou_gz}，旬首宫: {origin_pos}，时干宫: {target_pos}，旋转步数: {steps}")
        logger.info("天盘/九星排布完成")

    # ---- 6) 八门 ----
    def arrange_doors(self):
        assert self.xunshou_gz is not None and self.hour_gz is not None and self.xunshou_origin_pos is not None
        positions9 = Qimen.TRAVERSE_8 + [5]

        xun_idx = Ganzhi.JIAZI_INDEX[self.xunshou_gz]
        cur_idx = Ganzhi.JIAZI_INDEX[self.hour_gz]
        diff = cur_idx - xun_idx

        xun_earth_pos = self._earth_pos(Qimen.XUNSHOU_LIUYI[self.xunshou_gz])
        if self.is_yang:
            zhishi_pos = (xun_earth_pos + diff) % 9
        else:
            zhishi_pos = (xun_earth_pos - diff + 9) % 9
        zhishi_pos = 9 if zhishi_pos == 0 else zhishi_pos
        zhishi_pos = 2 if zhishi_pos == 5 else zhishi_pos
        self.zhishi_pos = zhishi_pos

        men_index = positions9.index(self.xunshou_origin_pos)
        self.zhishi_men = Qimen.MEN_ORDER[men_index]

        steps = positions9.index(self.zhishi_pos) - positions9.index(self.xunshou_origin_pos)
        men = deque(Qimen.MEN_ORDER)
        men.rotate(steps)

        for pos, m in zip(Qimen.TRAVERSE_8, men):
            self.palaces[pos]["door"] = m

        logger.info(f"值使门: {self.zhishi_men}，值使宫: {self.zhishi_pos}")
        logger.info("八门排布完成")

    # ---- 7) 八神 ----
    def arrange_shen(self):
        assert self.hour_gz is not None
        shen_order = Qimen.SHEN_YANG if self.is_yang else Qimen.SHEN_YIN

        shigan_pos = self._earth_pos(self.hour_gz[0])
        shigan_pos = 2 if shigan_pos == 5 else shigan_pos
        idx = Qimen.TRAVERSE_8.index(shigan_pos)

        shen = deque(shen_order)
        shen.rotate(idx)

        for pos, s in zip(Qimen.TRAVERSE_8, shen):
            self.palaces[pos]["shen"] = s

        logger.info("八神排布完成")

    # ---- helper ----
    def _earth_pos(self, gan: str) -> int:
        return self._earth_pos_by_gan.get(gan, 5)

    # ---- output ----
    def result_dict(self) -> Dict:
        return {
            "input_time": self.input_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "ganzhi": {"year": self.year_gz, "month": self.month_gz, "day": self.day_gz, "hour": self.hour_gz},
            "jieqi": self.curr_jieqi,
            "yuan": self.curr_yuan,
            "ju_type": "阳遁" if self.is_yang else "阴遁",
            "ju_number": self.ju_number,
            "xunshou": self.xunshou_gz,
            "zhishi_men": self.zhishi_men,
            "palaces": self.palaces,
        }

    def print_result(self):
        print("\n" + "=" * 60)
        print("奇门遁甲排盘结果")
        print("=" * 60)
        print(f"输入时间: {self.input_dt}")
        print(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gz}日 {self.hour_gz}时")
        print(f"节气: {self.curr_jieqi} {self.curr_yuan}")
        print(f"局数: {'阳遁' if self.is_yang else '阴遁'}{self.ju_number}局")
        print(f"旬首: {self.xunshou_gz}")
        print(f"值使门: {self.zhishi_men}")
        print("-" * 60)
        for pos in Qimen.TRAVERSE_8 + [5]:
            name, direction = Qimen.PALACE_MAP[pos]
            d = self.palaces[pos]
            print(f"{pos}宫 {name}({direction}): 地盘={d['earth']} 天盘={d['sky']} 星={d['star']} 门={d['door']} 神={d['shen']}")
        print("=" * 60)

    # ---- run ----
    def run(self) -> Dict:
        self.calculate_ganzhi()
        self.calculate_futou_date()
        self.determine_jieqi_yuan_ju()
        self.arrange_earth()
        self.arrange_sky_and_stars()
        self.arrange_doors()
        self.arrange_shen()
        logger.info("排盘完成")
        return self.result_dict()


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        "2024-11-19 20:00:00",
        "2025-02-28 18:30:00",
        "2024-06-07 16:30:00",
        "2025-03-13 04:00:00",
        "2025-10-23 03:00:00",
    ]
    dt_str = test_cases[4]
    pan = QiMenDunjiaPan(dt_str)
    pan.run()
    pan.print_result()