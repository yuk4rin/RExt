import cv2
import numpy as np
from bits_utils import bit_depth_scale, byte_array_to_bit_array

class BitImage:

    GRAY_CHANNELS = 8

    def __init__(self, image, width=12, height=12, bit_depth=2):
        """
            image: bytes | numpy str (to be converted to bytes)
            width, height: in pixels
        """
        self.width = width 
        self.height = height
        self.bit_depth = bit_depth
        if isinstance(image, bytes):
            self.data_in_bytes = image
            data = byte_array_to_bit_array(image, bit_depth)
            data = self.array_truncate(data)
            # performance issue?
            data = [ bit_depth_scale(val, bit_depth, self.GRAY_CHANNELS) for val in data ]
            self.data = np.asarray(data, dtype=np.uint8).reshape(width, height)
        elif isinstance(image, np.array) or isinstance(str, np.array):
            self.data = image

    def array_truncate(self, val_array):
        supposed_array_length = self.width * self.height
        assert(len(val_array) >= supposed_array_length)
        return val_array[:supposed_array_length]
        

    def show(self, width=512, height=512):
        resized_image = cv2.resize(self.data, (width, height), interpolation=cv2.INTER_NEAREST)
        cv2.imshow("bits image", resized_image)
        cv2.waitKey(0)
