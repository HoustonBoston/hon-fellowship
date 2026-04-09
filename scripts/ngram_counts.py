#!/usr/bin/env python3
import os, json, re
from collections import Counter

root = '.'
files = [
    'CryptoCurrency/filtered_r_CryptoCurrency_2020-2025_posts.jsonl',
    'CryptoCurrency/filtered_r_CryptoCurrency_comments_2024.jsonl',
    'CryptoCurrency/filtered_r_CryptoCurrency_comments_2025.jsonl',
    'CryptoScamReport/data/filtered_r_CryptoScamReport_2020-2025_posts.jsonl',
    'CryptoScamReport/data/filtered_r_CryptoScamReport_2020-2025_comments.jsonl',
    'CryptoScams/data/filtered_r_CryptoScams_2020-2025_posts.jsonl',
    'CryptoScams/data/filtered_r_CryptoScams_2020-2025_comments.jsonl',
]

files = [f for f in files if os.path.exists(os.path.join(root,f))]
print('Found files:', files)

stopwords = set("""
 a about above after again against all am an and any are aren't as at be because been before being below between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each few for from further had hadn't has hasn't have haven't having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor not of off on once only or other ought our ours ourselves out over own same shan't she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then there there's these they they'd they'll they're they've this those through to too under until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's with won't would wouldn't you you'd you'll you're you've your yours yourself yourselves
""".split())

word_re = re.compile(r"\b[a-z0-9']{2,}\b")

unigrams = Counter()
bigrams = Counter()
trigrams = Counter()

def tokenize(text):
    text = text.lower()
    tokens = word_re.findall(text)
    tokens = [t for t in tokens if not re.fullmatch(r"\d+", t)]
    return tokens

for path in files:
    p = os.path.join(root, path)
    try:
        fh = open(p, 'r', encoding='utf-8')
    except Exception as e:
        print('Failed opening', p, e)
        continue
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            texts = []
            if 'title' in j and j.get('title'):
                texts.append(j.get('title',''))
            if 'selftext' in j and j.get('selftext'):
                texts.append(j.get('selftext',''))
            if 'body' in j and j.get('body'):
                texts.append(j.get('body',''))
            if not texts:
                continue
            combined = ' '.join(texts)
            toks = tokenize(combined)
            toks_nostop = [t for t in toks if t not in stopwords]
            unigrams.update(toks_nostop)
            for i in range(len(toks_nostop)-1):
                bigrams.update([toks_nostop[i] + ' ' + toks_nostop[i+1]])
            for i in range(len(toks_nostop)-2):
                trigrams.update([toks_nostop[i] + ' ' + toks_nostop[i+1] + ' ' + toks_nostop[i+2]])

N=30
print('\nTop unigrams:')
for w,c in unigrams.most_common(N):
    print(f"{w}\t{c}")

print('\nTop bigrams:')
for w,c in bigrams.most_common(N):
    print(f"{w}\t{c}")

print('\nTop trigrams:')
for w,c in trigrams.most_common(N):
    print(f"{w}\t{c}")
