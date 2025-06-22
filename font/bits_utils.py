def bit_depth_scale(in_val, in_bits: int, out_bits: int):
    """
        int_bits: 2 or mutliple of 4
        out_bits: should be multiple of 8 

        ???: 
            no good 
            2 bit: 00   
                   01   0000 1000 -> 8
                   10   1000 0000 -> 128   
                   11   1000 1000 -> 136   
            4 bit: 0000  
                   0001  0000 0010 -> 2
                   0010  0000 1000 -> 8
                   0100  0010 0000 -> 32
                   1000  1000 0000 -> 128
    """
    if in_bits == 2:
        if in_val == 0b00:
            return 0
        elif in_val == 0b01:
            return  85
        elif in_val == 0b10:
            return  170
        elif in_val == 0b11:
            return  255

    assert(in_bits % 4 == 0)
    assert(out_bits % 8 == 0)

    slice_bits = out_bits // in_bits
    shift_bits = slice_bits - 1
    
    ret = 0
    for i in range(in_bits):
        ret |= ((in_val >> i) & 0b1) << (slice_bits * i + shift_bits)

    return ret

def byte_array_to_bit_array(in_bytes, bit_depth, byte_order_flag="big"):
    """
    in_bytes: array-like, each element is in range [0, 255) (<=0xff)
    bits_depth: 
        e.g. [ 0xFE(0b11111110) ] 
        depth = 1: [1, 1, 1, 1, 1, 1, 1, 0]  
        depth = 2: [3, 3, 3, 2]
        depth = 3: pad to 0b111,111,100 [7, 7, 4]
    """
    # assert(byte_order_flag in ["little", "big"])
    assert(byte_order_flag in ["big"])
    # little endian not implemented yet

    bits_in_array = []
    for i in range(len(in_bytes)):
        bits_in_array += [ ((in_bytes[i]>>b) & 1) for b in range(7, -1, -1) ] 

    val_in_array = []
    for i in range(0, len(bits_in_array), bit_depth):
        bits = bits_in_array[i:i+bit_depth]

        # padding 
        while(len(bits) % bit_depth != 0):
            bits.append(0)

        val = 0
        for b in range(bit_depth): 
            val += bits[b] << (bit_depth - b - 1)
        val_in_array.append(val)

    return val_in_array

def bytearray_to_bit_array(in_bytes, bit_depth, byte_order_flag="big"):
    return byte_array_to_bit_array(in_bytes, bit_depth, byte_order_flag)


def bit_array_to_byte_array(bit_array, byte_order_flag="big"):
    # assert(byte_order_flag in ["little", "big"])
    assert(byte_order_flag in ["big"])
    # little endian not implemented yet

    # make a copy
    bit_array = bit_array[:]

    # padding
    while(len(bit_array) % 8 != 0):
        bit_array.append(0)

    byte_array = byte_array
    for i in range(0, len(bit_array), 8):
        val = 0
        for j in range(8):
            val += bit_array[i+7-j] << j
        byte_array.append(val)
    
    return byte_array

def bit_array_to_bytearray(bit_array, byte_order_flag="big"):
    ba = bytearray()
    byte_array = bit_array_to_bytearray(bit_array, byte_order_flag)
    for i in byte_array:
        ba.append(i)

    return ba