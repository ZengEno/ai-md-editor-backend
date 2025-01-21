


# 以下代码用于生成 user id
def decimal_to_26(decimal_num):
    """将十进制数转换为用大写英文字母表示的26进制数"""
    if decimal_num == 0:
        return 'A'
    result = ''
    while decimal_num > 0:
        remainder = decimal_num % 26
        result = chr(remainder + ord('A')) + result
        decimal_num //= 26
    return result


def twenty_six_to_decimal(twenty_six_num):
    """将用大写英文字母表示的26进制数转换为十进制数"""
    result = 0
    power = 0
    for char in twenty_six_num[::-1]:  # 从低位到高位处理
        digit = ord(char) - ord('A')
        result += digit * (26 ** power)
        power += 1
    return result


def generate_user_id(number):
    quotient = number // 1000  # 整数部分
    remainder = number % 1000  # 余数部分
    return decimal_to_26(quotient) + f"{remainder:03d}"


def user_id_to_number(user_id):
    first_part = user_id[:-3]
    last_part = user_id[-3:]
    return twenty_six_to_decimal(first_part) * 1000 + int(last_part)