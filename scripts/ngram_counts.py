#!/usr/bin/env python3
import os, json, re
from collections import Counter

try:
    import nltk
    from nltk.stem import WordNetLemmatizer
except Exception:
    nltk = None
    WordNetLemmatizer = None

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

# Domain/platform noise and generic web terms that are not useful for scam semantics.
stopwords.update({
    'http', 'https', 'www', 'com', 'org', 'net', 'amp', 'html',
    'will', 'would', 'could', 'also', 'even', 'still',
    'reddit', 'subreddit', 'moderator', 'moderators', 'mod', 'mods',
    'automod', 'removed', 'deleted', 'post', 'posts', 'comment', 'comments',
    'thread', 'user', 'users', 'karma', 'upvote', 'upvotes', 'downvote', 'summoned',
    'automod', 'automoderator', 'removed', 'deleted', 'edit', 'edited',
    'bot', 'action', 'actions', 'rule', 'rules', 'filter', 'filters',
})

word_re = re.compile(r"\b[a-z][a-z']{1,}\b")
url_re = re.compile(r"https?://\S+|www\.\S+")

unigrams = Counter()
bigrams = Counter()
trigrams = Counter()

lemmatizer = WordNetLemmatizer() if WordNetLemmatizer else None


def singularize_heuristic(token):
    if len(token) <= 3:
        return token
    if token.endswith('ies') and len(token) > 4:
        return token[:-3] + 'y'
    if token.endswith('sses'):
        return token[:-2]
    if token.endswith('ses') and len(token) > 4:
        return token[:-2]
    if token.endswith('s') and not token.endswith('ss'):
        return token[:-1]
    return token


def normalize_token(token):
    token = token.strip("'")
    if not token:
        return ''
    if lemmatizer:
        try:
            return lemmatizer.lemmatize(token, pos='n')
        except LookupError:
            return singularize_heuristic(token)
    return singularize_heuristic(token)

def tokenize(text):
    text = text.lower()
    text = url_re.sub(' ', text)
    tokens = word_re.findall(text)
    return tokens


def keep_nouns(tokens):
    if not tokens:
        return []
    if nltk is None:
        return tokens
    try:
        tagged = nltk.pos_tag(tokens)
        return [tok for tok, tag in tagged if tag.startswith('NN')]
    except LookupError:
        # NLTK model data missing: proceed without POS filtering.
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
            toks = keep_nouns(toks)
            toks_nostop = [normalize_token(t) for t in toks if t not in stopwords]
            toks_nostop = [t for t in toks_nostop if t and t not in stopwords and len(t) > 1]
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
