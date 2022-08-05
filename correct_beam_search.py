from transformers import Wav2Vec2Processor
import re
import numpy as np
from pypinyin import lazy_pinyin, Style
from pypinyin.style._utils import get_initials, get_finals
import _locale
from pyctcdecode import build_ctcdecoder
from pyctcdecode.language_model import load_unigram_set_from_arpa
from special_process import smart_transfer_cn2ar, process_num1
from pyctcdecode.language_model import HotwordScorer
import json

_locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])


def load_unigram_prob_from_arpa(arpa_path: str):
    """Read unigrams from arpa file."""
    unigrams = {}
    with open(arpa_path) as f:
        start_1_gram = False
        for line in f:
            line = line.strip()
            if line == "\\1-grams:":
                start_1_gram = True
            elif line == "\\2-grams:":
                break
            if start_1_gram and len(line) > 0:
                parts = line.split("\t")
                if len(parts) == 3:
                    tt = (7 + float(parts[0])) * 3
                    if tt <= 0:
                        tt = 0.0001
                    unigrams[parts[1]] = tt

    return unigrams

processor = Wav2Vec2Processor.from_pretrained("res/zh_tokenizer", local_files_only=True)

token2id = processor.tokenizer.encoder
labels = sorted(token2id, key=token2id.__getitem__)
id2token = {value:key for key, value in token2id.items()}

hanzi = re.compile('^[\u4e00-\u9fa5]$')
no_hanzi = re.compile('[^\u4e00-\u9fa5]+')
similar_token = {}
initial_final_map = {}
tone2normal = {}
for k, v in token2id.items():
    if hanzi.match(k):
        phonene = lazy_pinyin(k)[0]
        if phonene in similar_token:
            similar_token[phonene].append(v)
        else:
            similar_token[phonene] = [v]
        initial = get_initials(phonene, strict=False)
        final = get_finals(phonene, strict=False)
        initial_final_map[phonene] = (initial, final, set(initial), set(final))
        full_phonene = lazy_pinyin(k, style=Style.TONE3, neutral_tone_with_five=True)[0]
        tone2normal[full_phonene] = phonene
        tone2normal[phonene] = phonene
        if full_phonene in similar_token:
            similar_token[full_phonene].append(v)
        else:
            similar_token[full_phonene] = [v]

unigram = load_unigram_set_from_arpa('res/bigram.arpa')
default_hot_weight = 6
kenlm_model_path = "res/lm.bin"
lm_decoder = build_ctcdecoder(labels, kenlm_model_path, unigram, alpha=1, beta=1.5)
kenlm_model = lm_decoder.model_container[lm_decoder._model_key]._kenlm_model
unigram_prob = load_unigram_prob_from_arpa('res/bigram.arpa')
similarity_cache = {}


class Corrector:
    def __init__(self):
        hotword_map = {}
        ret = json.load(open('res/hot.json', 'r', encoding='utf-8'))
        hotword_map.update(ret)
        self.hotword_map = hotword_map
        self.hot_scorer = HotwordScorer.build_scorer(hotword_map)

    def update_hotword(self, data):
        json.dump(data, open('res/hot.json', 'w', encoding='utf-8'), ensure_ascii=False)
        self.hotword_map = data
        self.hot_scorer = HotwordScorer.build_scorer(self.hotword_map)

    def get_hotword(self):
        return self.hotword_map

    def correct(self, source):
        no_hanzi_pos = []
        before_strip = source
        source = no_hanzi.sub('', before_strip)
        if before_strip != source:
            for item in no_hanzi.finditer(before_strip):
                no_hanzi_pos.append((item.start(), item.group()))

        # source = smart_transfer_cn2ar(source)
        source = process_num1(source)
        encoded_input = processor.tokenizer.encode_plus(source)
        logits = np.full((len(encoded_input['input_ids']), processor.tokenizer.vocab_size), 0.001)

        source_py = lazy_pinyin(source)
        source_full_py = lazy_pinyin(source, style=Style.TONE3, neutral_tone_with_five=True)

        for i, id in enumerate(encoded_input['input_ids']):
            py = source_py[i]
            full_py = source_full_py[i]
            initial, final, initial_set, final_set = initial_final_map[py]

            for phonene in similar_token:
                if py == phonene:
                    similarity = 0.9
                elif full_py == phonene:
                    similarity = 0.94
                elif py == tone2normal[phonene]:
                    continue
                else:
                    if phonene != tone2normal[phonene]:
                        continue
                    similarity_key = (phonene, py) if phonene < py else (py, phonene)
                    if similarity_key in similarity_cache:
                        similarity = similarity_cache[similarity_key]
                    else:
                        p_initial, p_final, p_initial_set, p_final_set = initial_final_map[phonene]
                        similarity = (len(initial_set.intersection(p_initial_set)) + len(final_set.intersection(p_final_set))) / max(len(py), len(phonene))

                        if similarity <= 0.25:
                            continue
                        if p_initial != initial:
                            if initial in ['zh', 'z'] and p_initial in ['zh', 'z']:
                                similarity *= 1.15
                            elif initial in ['ch', 'c'] and p_initial in ['ch', 'c']:
                                similarity *= 1.15
                            elif initial in ['sh', 's'] and p_initial in ['sh', 's']:
                                similarity *= 1.15
                            elif initial in ['zh', 'z', 'ch', 'c'] and p_initial in ['zh', 'z', 'ch', 'c']:
                                similarity *= 1.1
                            elif initial in ['zh', 'z', 'ch', 'c', 'sh', 's'] and p_initial in ['zh', 'z', 'ch', 'c', 'sh', 's']:
                                similarity *= 1.05
                            elif initial in ['s', 'x'] and p_initial in ['s', 'x']:
                                similarity *= 1.1
                            elif initial in ['l', 'n'] and p_initial in ['l', 'n']:
                                similarity *= 1.1
                            elif initial in ['l', 'n', 'r'] and p_initial in ['l', 'n', 'r']:
                                similarity *= 1.05
                            elif initial in ['b', 'p'] and p_initial in ['b', 'p']:
                                similarity *= 1.05
                            elif initial in ['g', 'k'] and p_initial in ['g', 'k']:
                                similarity *= 1.05
                            elif initial in ['f', 'h'] and p_initial in ['f', 'h']:
                                similarity *= 1.1
                            elif initial in ['d', 't'] and p_initial in ['d', 't']:
                                similarity *= 1.05

                        if p_final != final:
                            if final in ['ang', 'an'] and p_final in ['ang', 'an']:
                                similarity *= 1.1
                            elif final in ['eng', 'en'] and p_final in ['eng', 'en']:
                                similarity *= 1.1
                            elif final in ['ang', 'an', 'eng', 'en'] and p_final in ['ang', 'an', 'eng', 'en']:
                                similarity *= 1.05
                            elif final in ['ing', 'in'] and p_final in ['ing', 'in']:
                                similarity *= 1.1
                            elif final in ['ei', 'ui'] and p_final in ['ei', 'ui']:
                                similarity *= 1.1

                        if similarity >= 0.8:
                            similarity = 0.8
                        similarity_cache[similarity_key] = similarity
                similarity = 4 + similarity * 20
                for j in similar_token[phonene]:
                    token_similarity = similarity + unigram_prob[id2token[j]]
                    if id == j:
                        logits[i][j] = 24 + unigram_prob[id2token[id]]
                    elif logits[i][j] < token_similarity:
                        logits[i][j] = token_similarity
            logits[i][id] = max(logits[i])

        text = lm_decoder.decode(logits, beam_width=30, hotword_scorer=self.hot_scorer, beam_prune_logp=-25, token_min_logp=-5.5)
        text = text.strip().strip('|')

        if len(no_hanzi_pos) > 0:
            for s, t in no_hanzi_pos:
                text = text[:s] + t + text[s:]

        if kenlm_model.score(' '.join(text), bos=True, eos=True) - kenlm_model.score(' '.join(source), bos=True, eos=True) < 0.5:
            text = source
        text = smart_transfer_cn2ar(text)

        return text


if __name__ == '__main__':
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
