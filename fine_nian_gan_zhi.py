def get_ganzhi(input_datetime):
    year = input_datetime.year
    # 获取当前年和前一年的立春时间
    lichun_current = find_lichun(year)
    lichun_prev = find_lichun(year - 1)
    
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
