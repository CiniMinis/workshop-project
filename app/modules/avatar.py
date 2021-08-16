from enum import Enum
from math import log2, ceil
from abc import abstractmethod, ABC
from functools import reduce
from random import randint, choice
from utils.colors import COLOR_NAMES

""" Enum for encoding the base units of DNA """
DNANucleotide = Enum('DNANucleotide', 'C G A T', start=0)

# number of bits a number in [0, x) takes to represent
def _bit_length(x): return int(ceil(log2(x)))


class BodyPart(ABC):
    """
        Abstract base class for body parts
    """
    COLOR_BIT_LEN = 6    # length in bits a color selection

    @property
    @abstractmethod
    def VARIATIONS():
        pass

    @property
    @abstractmethod
    def IS_COLORABLE():
        pass

    @classmethod
    def bit_len(cls):
        cls_len = _bit_length(cls.VARIATIONS)
        if cls.IS_COLORABLE:
            cls_len += cls.COLOR_BIT_LEN
        return cls_len

    def __init__(self, variation=None, color=None):
        if variation is None:
            assert self.VARIATIONS == 1, \
                "variation must be specified if and only if the body part has more than 1 variations"
            variation = 0
        assert (0 <= variation < self.VARIATIONS), \
            f"variation must be between 0 (inclusive) and {self.VARIATIONS} (exclusive)"
        assert (color is None) == (not self.IS_COLORABLE), \
            "color must be specified if and only if the body part is colorable"
        self.variation = variation
        self.color = color
    
    def __repr__(self):
        part_name = self.__class__.__name__
        return f"{part_name}(variation={self.variation!r}, color={self.color!r})"

    def _encode_variation(self):
        if self.VARIATIONS == 1:
            return ""
        return f"{self.variation:0b}".zfill(_bit_length(self.VARIATIONS))

    @classmethod
    def _decode_variation(cls, decode_string):
        if len(decode_string) == 0:
            return None
        return int(decode_string, 2)

    def _encode_color(self):
        if not self.IS_COLORABLE:
            return ""
        color_index = COLOR_NAMES.index(self.color)
        return f"{color_index:0b}".zfill(self.COLOR_BIT_LEN)

    @staticmethod
    def _decode_color(decode_string):
        if len(decode_string) == 0:
            return None

        decoded_int = int(decode_string, 2)
        return COLOR_NAMES[decoded_int]

    def to_bitstring(self):
        return self._encode_variation() + self._encode_color()

    @classmethod
    def from_bitstring(cls, decode_string):
        assert cls.bit_len() == len(decode_string), "String decode length mismatch"

        # if required decode color
        if cls.IS_COLORABLE:
            color = cls._decode_color(decode_string[-cls.COLOR_BIT_LEN:])
            decode_string = decode_string[:-cls.COLOR_BIT_LEN]
        else:
            color = None

        # decode variation
        variation = cls._decode_variation(decode_string)

        return cls(variation, color)

    @classmethod
    def randomize(cls):
        # if required generate color
        if cls.IS_COLORABLE:
            color = choice(COLOR_NAMES)
        else:
            color = None

        # if required generate variation
        if cls.VARIATIONS > 1:
            variation = randint(0, cls.VARIATIONS - 1)
        else:
            variation = None

        return cls(variation=variation, color=color)


class AvatarBase(ABC):
    """
        Base class for user avatars
    """
    _BODY_PART_TYPES = []
    __PART_NAME_TO_INDEX = {}
    BITS_IN_NUCLEOTIDE = 2

    def __new__(cls, *args, **kwargs):
        """
            Overriding __new__ to disallow instanciating AvatarBase, 
            despite not having abstract methods.
        """
        if cls is AvatarBase:
            raise TypeError("Can't instantiate abstract class Avatar base")
        return super(AvatarBase, cls).__new__(cls)

    def __init__(self, *body_parts):
        self.body_parts = []
        for part, cls in zip(body_parts, self._BODY_PART_TYPES):
            assert isinstance(
                part, cls), f"Given body parts mismatch the required types"
            self.body_parts.append(part)

    @classmethod
    def bit_len(cls):
        return sum([p.bit_len() for p in cls._BODY_PART_TYPES])

    def __getitem__(self, part):
        if not isinstance(part, str):
            raise KeyError("Get expects a string part name")
        
        key = part.lower()
        if key not in self.__PART_NAME_TO_INDEX:
            raise KeyError(f"{self.__class__.__qualname__} has not body part {key}")
        
        index = self.__PART_NAME_TO_INDEX[key]
        if index >= len(self.body_parts):
            raise KeyError(f"Missing body part of type \'{key}\'. " +
                "This instance was probably created before the part was registered.")
        
        return self.body_parts[index]

    def to_bitstring(self):
        return ''.join([part.to_bitstring() for part in self.body_parts])

    @classmethod
    def from_bitstring(cls, decode_string):
        assert len(decode_string) == cls.bit_len(), "Bad decode string length"

        lengths = [p.bit_len() for p in cls._BODY_PART_TYPES]
        indecies = reduce(lambda lst, length: lst +
                          [lst[-1] + length], lengths[:-1], [0])
        part_strings = [decode_string[i:i + length]
                        for i, length in zip(indecies, lengths)]
        parts = [p_type.from_bitstring(s) for s, p_type in zip(
            part_strings, cls._BODY_PART_TYPES)]
        return cls(*parts)

    def to_dna(self):
        chunk_size = self.BITS_IN_NUCLEOTIDE
        bitstring = self.to_bitstring()
        pad = (-len(bitstring) % chunk_size) * '0'
        bitstring = pad + bitstring
        chunks = [bitstring[i: i + chunk_size] for i in range(0, len(bitstring), chunk_size)]
        dna_list = [DNANucleotide(int(chunk, 2)) for chunk in chunks]
        return ''.join([nucleotide.name for nucleotide in dna_list])
    
    @classmethod
    def from_dna(cls, dna_string):
        chunk_size = cls.BITS_IN_NUCLEOTIDE

        allowed_chars = [e.name for e in DNANucleotide]

        if any([(c not in allowed_chars) for c in dna_string]):
            raise ValueError("Invalid DNA string.")
        
        dna_numbers = [DNANucleotide[ch].value for ch in dna_string]
        bitstring = ''.join([f"{num:0b}".zfill(chunk_size) for num in dna_numbers])
        needed_len = cls.bit_len()
        if not (0 <= len(bitstring) - needed_len < chunk_size):
            raise ValueError("Bad DNA string length")
        pad, bitstring = bitstring[:-needed_len], bitstring[-needed_len:]
        if '1' in pad:
            raise ValueError("Bad DNA string length")
        return cls.from_bitstring(bitstring)

    @classmethod
    def randomize(cls):
        return cls(*(p.randomize() for p in cls._BODY_PART_TYPES))
    
    @staticmethod
    def _part_to_name(part):
        return part.__name__.lower()
    
    @classmethod
    def register_part(cls, part):
        if cls is AvatarBase:
            raise TypeError("Can't register body parts to AvatarBase")

        part_name = cls._part_to_name(part)
        if part_name in cls.__PART_NAME_TO_INDEX:
            raise KeyError(f"Body part name {part_name} is already taken in {cls.__qualname__}")
        
        index = len(cls._BODY_PART_TYPES)
        cls._BODY_PART_TYPES.append(part)
        cls.__PART_NAME_TO_INDEX[part_name] = index

        return part

