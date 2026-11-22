# -*- coding: utf-8 -*-
"""解析微信群聊导出文件，提取余子豪的发言、上下文与他者视角。"""
import re, sys, json
from collections import Counter

SRC = r"C:\Users\runne\Documents\wechatExport\行行行寰球科技集团控股有限公司_20663503604@chatroom_2026-11-20_18-46-50\行行行寰球科技集团控股有限公司_c0b205e6.txt"
OUT = r"C:\Users\runne\.workbuddy\skills\yuzihao-perspective\references\sources\transcripts"

HEAD = re.compile(r'^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.+)$')
NOISE = '已按导出设置跳过图片/动画表情，保留消息与已有元数据。'

def parse():
    msgs = []
    cur = None
    with open(SRC, encoding='utf-8') as f:
        for raw in f:
            line = raw.rstrip('\n')
            m = HEAD.match(line)
            if m:
                if cur: cur['text'] = '\n'.join(cur['lines']).strip(); msgs.append(cur)
                cur = {'time': m.group(1), 'speaker': m.group(2).strip(), 'lines': []}
            else:
                if cur:
                    if line.strip() == NOISE:
                        continue
                    cur['lines'].append(line)
        if cur: cur['text'] = '\n'.join(cur['lines']).strip(); msgs.append(cur)
    return msgs

def meaningful(t):
    if not t: return False
    if t in ('[图片]', '[动画表情]', '[语音]', '[视频]', '[表情]'): return False
    if re.fullmatch(r'\[[^\]]+\]', t): return False
    return True

def main():
    msgs = parse()
    print('TOTAL_MESSAGES', len(msgs))
    target = '余子豪'
    idxs = [i for i,m in enumerate(msgs) if m['speaker']==target]
    print('YUZIHHAO_MESSAGES', len(idxs))

    # 1. 余子豪全部有效发言
    with open(OUT + r'\yuzihao_all.txt', 'w', encoding='utf-8') as f:
        f.write('# 余子豪全部发言（群聊一手语料）\n\n')
        for i in idxs:
            m = msgs[i]
            if meaningful(m['text']):
                f.write('[%s] %s\n\n' % (m['time'], m['text']))

    # 2. 上下文窗口：余子豪发言前后各4条
    with open(OUT + r'\yuzihao_context.txt', 'w', encoding='utf-8') as f:
        f.write('# 余子豪发言上下文（前4后3条，标记 >>> 为目标发言）\n\n')
        written = set()
        blocks = []
        for i in idxs:
            if not meaningful(msgs[i]['text']): continue
            s = max(0, i-4); e = min(len(msgs), i+4)
            key = (s,e)
            if key in written: continue
            written.add(key)
            b = ['='*60]
            for j in range(s, e):
                mm = msgs[j]
                if not meaningful(mm['text']): continue
                mark = '>>>' if j==i else '   '
                b.append('%s [%s] %s: %s' % (mark, mm['time'], mm['speaker'], mm['text'].replace('\n',' / ')))
            blocks.append('\n'.join(b))
        f.write('\n\n'.join(blocks))

    # 3. 他人提到余子豪（含@、被讨论）
    mentions = []
    for i,m in enumerate(msgs):
        if m['speaker']!=target and ('余子豪' in m['text'] or '@余子豪' in m['text']) and meaningful(m['text']):
            mentions.append(m)
    with open(OUT + r'\others_about_yuzihao.txt', 'w', encoding='utf-8') as f:
        f.write('# 他者视角：他人提到/评价/回应余子豪（共%d条）\n\n' % len(mentions))
        for m in mentions:
            f.write('[%s] %s: %s\n\n' % (m['time'], m['speaker'], m['text']))

    # 4. 统计：时间跨度、高频词、句长、口癖
    times = [msgs[i]['time'] for i in idxs]
    valid_texts = [msgs[i]['text'] for i in idxs if meaningful(msgs[i]['text'])]
    years = Counter(t[:4] for t in times)
    # 中文分词用简单的双字/单字统计 + 常见词
    words = Counter()
    for t in valid_texts:
        clean = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', t)
        for w in re.findall(r'[\u4e00-\u9fff]{2,4}', t):
            words[w]+=1
    stats = {
        'total_yuzihao_msgs': len(idxs),
        'meaningful_msgs': len(valid_texts),
        'time_span': [min(times), max(times)],
        'by_year': dict(sorted(years.items())),
        'avg_len': round(sum(len(t) for t in valid_texts)/max(1,len(valid_texts)),1),
        'top_words': words.most_common(120),
    }
    with open(OUT + r'\stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print('MEANINGFUL', len(valid_texts))
    print('TIME_SPAN', min(times), '->', max(times))
    print('BY_YEAR', dict(sorted(years.items())))
    print('MENTIONS', len(mentions))
    print('AVG_LEN', stats['avg_len'])
    print('TOP_WORDS', words.most_common(60))

if __name__=='__main__':
    main()
