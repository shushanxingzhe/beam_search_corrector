#Beam Search Corrector
Beam Search Corrector是一个开箱即用的中文拼音同音近音字纠错库，可通过res/hot.json定义热词及其权重值，可智能转换中文数字到阿拉伯数字。
使用前需要下载语言模型[lm.bin](https://pan.baidu.com/s/1NIQw6NqLm2mhzp8hZ1zRwg?pwd=563y) 和[bigram.arpa](https://pan.baidu.com/s/1uIP-0d3bwjK5Hxhu5NPUjw?pwd=sa16) 到res目录下(lm.bin是有kenlm基于大量文本语料生成的语言模型)

###示例
```
from correct_beam_search import Corrector
corrector = Corrector()
print(corrector.correct('我叫刘得华我的电话号码是一八二七六八四零八十二'))
print(corrector.correct('今天是二零二二年四月二十四号'))
print(corrector.correct('感帽了'))
print(corrector.correct('你儿字今年几岁了'))
print(corrector.correct('少先队员因该为老人让坐'))
print(corrector.correct('随然今天很热'))
print(corrector.correct('传然给我'))
print(corrector.correct('呕土不止'))
print(corrector.correct('哈蜜瓜'))
print(corrector.correct('广州黄浦'))
print(corrector.correct('我生病了,咳数了好几天'))
print(corrector.correct('对这个平台新人度大打折扣'))
print(corrector.correct('我想买哥苹果手机'))
print(corrector.correct('真麻烦你了。希望你们好好的跳无'))
print(corrector.correct('机七学习是人工智能领遇最能体现智能的一个分知'))
print(corrector.correct('一只小渔船浮在平净的河面上'))
print(corrector.correct('我的家乡是有明的渔米之乡'))
print(corrector.correct('独立含球湘江北区'))
print(corrector.correct('独立含球香江北区'))
print(corrector.correct('香港也叫香江'))
print(corrector.correct('他以二百五十八亿美元身家成为河北首富'))
```
输出为
```
我叫刘德华我的电话号码是18276840842
今天是2022年4月24号
感冒了
你儿子今年几岁了
少先队员应该为老人让座
虽然今天很热
传染给我
呕吐不止
哈密瓜
广州黄埔
我生病了,可数了好几天
对这个平台信任度大打折扣
我想买个苹果手机
真麻烦你了。希望你们好好的跳舞
机器学习是人工智能领域最能体现智能的一个分支
一只小渔船浮在平静的河面上
我的家乡是有名的鱼米之乡
独立寒秋湘江北去
独立寒秋湘江北去
香港也叫香江
他以258亿美元身家成为河北首富
```

#Acknowledgement
Many thanks to [pyctcdecode](https://github.com/kensho-technologies/pyctcdecode), I borrowed a lot of code from it.

Many thanks to [cn2an](https://github.com/Ailln/cn2an)