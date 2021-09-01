"""
    A solution for the medium challenge, an encrypted user-side cache
"""

from attack_util import *
from easy_solution import EasyAttacker
from itertools import product

class MediumAttacker(EasyAttacker):
    """The attacker script for the medium challenge, extend EasyAttacker"""
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
    print(MediumAttacker.attack(verbose=True))