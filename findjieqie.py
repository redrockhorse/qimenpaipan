import bisect

solar_terms = [
    ('立春', 315), ('雨水', 330), ('惊蛰', 345), ('春分', 0), ('清明', 15), ('谷雨', 30),
    ('立夏', 45), ('小满', 60), ('芒种', 75), ('夏至', 90), ('小暑', 105), ('大暑', 120),
    ('立秋', 135), ('处暑', 150), ('白露', 165), ('秋分', 180), ('寒露', 195), ('霜降', 210),
    ('立冬', 225), ('小雪', 240), ('大雪', 255), ('冬至', 270), ('小寒', 285), ('大寒', 300)
]

sorted_terms = sorted(solar_terms, key=lambda x: x[1])

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

# 测试用例
# print(find_closest_terms(0.2))  # ['惊蛰', '春分']
# print(find_closest_terms(359))  # ['惊蛰', '春分']
# print(find_closest_terms(30))   # ['谷雨', '立夏']
# print(find_closest_terms(0))    # ['春分', '清明']
# print(find_closest_terms(345))  # ['惊蛰', '春分']
