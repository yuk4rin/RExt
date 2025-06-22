import numpy as np
from bits_utils import bit_array_to_byte_array

def padded_len(origin_len, depth):
    return ((origin_len -1) // depth + 1) * depth

def _np_bool_array_to_byte_array(image, byte_order_flag="big"):
    flatted = image.flatten()
    pad_len = padded_len(flatted.shape[0], 8)
    padded_zeros = np.zeros(pad_len - flatted.shape[0]) 
    flatted = np.append(flatted, padded_zeros)

    return bit_array_to_byte_array(flatted, byte_order_flag)

def image_to_byte_array(image, byte_order_flag="big"):
    if isinstance(image, np.array):
        image_dtype = image.dtype
        assert(image_dtype in [np.bool, np.unit8])

        if image_dtype == np.bool:
            return _np_bool_array_to_byte_array(image, byte_order_flag)
        