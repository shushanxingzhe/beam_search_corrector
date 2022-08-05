import re
import cn2an

number_map = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9
}

# 单位映射
unit_map = {
    "十": 10,
    "百": 100,
    "千": 1000,
    "万": 10000,
    "亿": 100000000
}

num_zh2ar = str.maketrans('零一二三四五六七八九', '0123456789')
num_ar2zh = str.maketrans('0123456789', '零一二三四五六七八九')


def backward_cn2an_three(text):
    output = 0
    unit = 1
    # 万、亿的单位
    ten_thousand_unit = 1
    num = 0
    for index, cn_num in enumerate(reversed(text)):
        if cn_num in number_map:
            # 数字
            num = number_map[cn_num]
            # 累加
            output = output + num * unit
        elif cn_num in unit_map:
            # 单位
            unit = unit_map[cn_num]
            # 判断出万、亿
            if unit % 10000 == 0:
                # 万、亿
                if unit > ten_thousand_unit:
                    ten_thousand_unit = unit
                # 万亿
                else:
                    ten_thousand_unit = unit * ten_thousand_unit
                    unit = ten_thousand_unit

            if unit < ten_thousand_unit:
                unit = ten_thousand_unit * unit
        else:
            raise ValueError(f"{cn_num} 不在转化范围内")

    return output


def transfer_number(text):
    num_matches = re.findall(r'[零一二三四五六七八九]{3,}', text)
    for item in num_matches:
        numstr = item.translate(num_zh2ar)
        text = text.replace(item, numstr)

    # ([一二三四五六七八九]万)?([一二三四五六七八九]千)?([一二三四五六七八九]百)([一二三四五六七八九]十)?
    quantity_matches = re.findall(r'[零一二三四五六七八九万千百十]{3,}', text)
    probnum = re.compile(r'[零一二三四五六七八九]{2,}[亿万千百十]')
    for item in quantity_matches:
        if probnum.match(item):
            continue
        numstr = backward_cn2an_three(item)
        text = text.replace(item, str(numstr))

    num_matches = re.findall(r'[一二三四五六七八九][月日]', text)
    for item in num_matches:
        numstr = item.translate(num_zh2ar)
        text = text.replace(item, numstr)

    return text


class Transform(cn2an.Transform):
    def __init__(self):
        super(Transform, self).__init__()
        #self.cn_pattern = f"负?([{self.all_num}{self.all_unit}]+点)?[{self.all_num}{self.all_unit}]+"
        self.cn_pattern = f"负?[{self.all_num}十拾百佰千仟]+(点[{self.all_num}]+)?"

    def transform(self, inputs: str, method: str = "cn2an") -> str:
        if method == "cn2an":
            # date
            inputs = re.sub(fr"((({self.smart_cn_pattern})|({self.cn_pattern}))年)?([{self.all_num}十]+月)?([{self.all_num}十]+[日|号])?",
                            lambda x: self.__sub_util(x.group(), "cn2an", "date"), inputs)
            # fraction
            inputs = re.sub(fr"{self.cn_pattern}分之{self.cn_pattern}",
                            lambda x: self.__sub_util(x.group(), "cn2an", "fraction"), inputs)
            # percent
            inputs = re.sub(fr"百分之{self.cn_pattern}",
                            lambda x: self.__sub_util(x.group(), "cn2an", "percent"), inputs)
            # celsius
            inputs = re.sub(fr"{self.cn_pattern}摄氏度",
                            lambda x: self.__sub_util(x.group(), "cn2an", "celsius"), inputs)
            # time
            inputs = re.sub(r"[零一二三四五六七八九十]{1,3}点[零一二三四五六七八九十]{1,3}分[零一二三四五六七八九十]{1,3}秒",
                 lambda x: self.__sub_util(x.group().split('点')[0], "cn2an", "number") + ':'
                            + self.__sub_util(x.group().split('点')[1].split('分')[0], "cn2an", "number") + ':'
                            + self.__sub_util(x.group().split('点')[1].split('分')[1][:-1], "cn2an", "number")
                            , inputs)
            inputs = re.sub(r"[零一二三四五六七八九十]{1,3}点[零一二三四五六七八九十]{1,3}分",
                 lambda x: self.__sub_util(x.group().split('点')[0], "cn2an", "number") + ':'
                            + self.__sub_util(x.group().split('点')[1].split('分')[0], "cn2an", "number")
                            , inputs)
            inputs = re.sub(r"[零一二三四五六七八九十]{1,3}点[一二三四五]?十[一二三四五六七八九]?",
                 lambda x: self.__sub_util(x.group().split('点')[0], "cn2an", "number") + ':'
                            + self.__sub_util(x.group().split('点')[1], "cn2an", "number")
                            , inputs)

            # number
            output = re.sub(self.cn_pattern,
                            lambda x: x.group() if len(x.group()) == 1 else self.__sub_util(x.group(), "cn2an", "number"), inputs)

        elif method == "an2cn":
            # date
            inputs = re.sub(r"(\d{2,4}年)?(\d{1,2}月)?(\d{1,2}日)?",
                            lambda x: self.__sub_util(x.group(), "an2cn", "date"), inputs)
            # fraction
            inputs = re.sub(r"\d+/\d+",
                            lambda x: self.__sub_util(x.group(), "an2cn", "fraction"), inputs)
            # percent
            inputs = re.sub(r"-?(\d+\.)?\d+%",
                            lambda x: self.__sub_util(x.group(), "an2cn", "percent"), inputs)
            # celsius
            inputs = re.sub(r"\d+℃",
                            lambda x: self.__sub_util(x.group(), "an2cn", "celsius"), inputs)
            # number
            output = re.sub(r"-?(\d+\.)?\d+",
                            lambda x: self.__sub_util(x.group(), "an2cn", "number"), inputs)
        else:
            raise ValueError(f"error method: {method}, only support 'cn2an' and 'an2cn'!")

        return output


custom_cn2an = Transform()
no_num = re.compile(r'[零一二三四五六七八九]')
no_single_num = re.compile(r'[零一二三四五六七八九]{2,}')
wrong_48 = re.compile(r'[零一二三四五六七八九]{4,}[十百][零一二三四五六七八九]+|[十百][零一二三四五六七八九]{3,}')


def smart_transfer_cn2ar(text):
    if not no_num.search(text):
        return text
    if no_single_num.search(text):
        wrong_num_matches = wrong_48.findall(text)
        for item in wrong_num_matches:
            numstr = re.sub(r'十', '四', item)
            numstr = re.sub(r'百', '八', numstr)
            text = text.replace(item, numstr)
        wrong_num_matches = wrong_48.findall(text)
        for item in wrong_num_matches:
            numstr = re.sub(r'十', '四', item)
            numstr = re.sub(r'百', '八', numstr)
            text = text.replace(item, numstr)
        # wrong_num_matches = re.findall(r'[零一二三四五六七八九]{4,}[十百][零一二三四五六七八九]+|[十百][零一二三四五六七八九]{2,}', text)
        # for item in wrong_num_matches:
        #     numstr = re.sub(r'十', '四', item)
        #     numstr = re.sub(r'百', '八', numstr)
        #     text = text.replace(item, numstr)
        # wrong_num_matches = re.findall(r'[零一二三四五六七八九]{3,}百[零一二三四五六七八九]+', text)
        # for item in wrong_num_matches:
        #     numstr = re.sub(r'([零一二三四五六七八九]{3,})百([零一二三四五六七八九]+)', r'\1八\2', item)
        #     text = text.replace(item, numstr)

    return custom_cn2an.transform(text)


def process_num1(text):
    wrong_num_matches = re.findall(r'[零一二三四五六七八九]+幺+', text)
    for item in wrong_num_matches:
        numstr = re.sub(r'幺', '一', item)
        text = text.replace(item, numstr)
    wrong_num_matches = re.findall(r'幺+[零一二三四五六七八九]+', text)
    for item in wrong_num_matches:
        numstr = re.sub(r'幺', '一', item)
        text = text.replace(item, numstr)
    return text


def smart_transfer_ar2cn(text):
    if not re.search(r'[0-9]', text):
        return text
    num_matches = re.findall(r'[0123456789]{6,}', text)
    for item in num_matches:
        numstr = item.translate(num_ar2zh)
        text = text.replace(item, numstr)
    text = custom_cn2an.transform(text, method='an2cn')
    return text


if __name__ == '__main__':
    print(smart_transfer_cn2ar('现在是十五点'))
    print(smart_transfer_cn2ar('现在是十五点五十九分'))
    print(smart_transfer_cn2ar('现在是十五点五十九'))
    print(smart_transfer_cn2ar('现在是十五点十九'))
    print(smart_transfer_cn2ar('现在是十五点十九分'))
    print(smart_transfer_cn2ar('现在是十五点五十九分三十四秒'))
    # print(smart_transfer_cn2ar('我叫刘佳福我的电话号码是一百八十五七五五字零八四二我是一九九零年七月二十一日出生'))
    # t = '一点二加二点三等于三点五，挖出二百两银子，我刚捡了两百块， 分你二分之一，我的电话是一八五七五五四零八四二, 我生日是一九九零年七月二十一日, 这个的价格是一十一万二千三百四十五块也可以一万零三百四十五给你, 她都七八十岁了, 这个项目也就四五十万吧'
    # print(smart_transfer_cn2ar(t))
    # print(smart_transfer_cn2ar('我叫刘佳附我的电话号码是一八五七五五四零八四二我是一九九零年七月二十一日出生'))
    # print(smart_transfer_cn2ar('一起来试一下，七七四十九天，一零零八六'))
    # print(smart_transfer_cn2ar('一起来试一下'))
    # print(smart_transfer_cn2ar('你好，明天有百分之六十二的概率降雨'))
    #
    # tt = '明天有62％的概率降雨62%, 随便来几个价格12块5，34.5元，20.1万, 现场有7/12的观众投出了赞成票, 1.2加2.3等于3.5，挖出200两银子，我刚捡了两百块，分你二分之一，我的电话是18575540842, 我生日是1990年7月21日, 这个的价格是112345块也可以10345给你, 她都七八十岁了, 这个项目也就四五十万吧'
    # print(smart_transfer_ar2cn(tt))






