import os
from enum import Enum

from bit_image import BitImage


class CMAP:
    def __init__(self, fp, offset, byte_order_flag="little"):
        if byte_order_flag in ["little", "big"]:
            self.byte_order_flag = byte_order_flag
        else:
            raise Exception("byte order?")
        
        fp.seek(offset, os.SEEK_SET)

        # CMAP Header
        if (fp.read(4) != b"PAMC"):
            raise Exception("CMAP chunk format error")
        
        # Chunk Size (14h+...+padding)
        self.chunk_size = self.bytes_to_int(fp.read(4))

        # 2 bytes 
        self.first_character = self.bytes_to_int(fp.read(2))
        self.last_character = self.bytes_to_int(fp.read(2))
        self.num_of_characters = self.last_character - self.first_character + 1

        # Map Type (0, 1, 2)
        self.map_type = self.bytes_to_int(fp.read(4))

        # Offset to next Character Map, plus 8 （to the start of file)
        self.offset_to_next_map_p8 = self.bytes_to_int(fp.read(4))

        # For Map Type0, Increasing TileNo's assigned to increasing CharNo's:
        #   14h      2    TileNo for First Char (and increasing for further chars)
        #   16h      2    Padding to 4-byte boundary (zerofilled)
        # For Map Type1, Custom TileNo's assigned to increasing CharNo's:
        #   14h+N*2  2    TileNo's for First..Last Char (FFFFh=None; no tile assigned)
        #   ...      0/2  Padding to 4-byte boundary (zerofilled)
        # For Map Type2, Custom TileNo's assigned to custom CharNo's:
        #   14h      2    Number of following Char=Tile groups...
        #   16h+N*4  2    Character Number
        #   18h+N*4  2    Tile Number
        #   ...      2    Padding to 4-byte boundary (zerofilled)
        if self.map_type == 0:
            self.tile_num_for_first_chara = self.bytes_to_int(fp.read(2))
            fp.read(2) # padding
        elif self.map_type == 1:
            self.tile_nums = []
            for i in range(self.num_of_characters):
                self.tile_nums.append(self.bytes_to_int(fp.read(2)))
            if len(self.tile_nums) % 4 != 0:
                fp.read(2) # padding
        elif self.map_type == 2:
            self.num_of_custom_assigned_tiles = self.bytes_to_int(fp.read(2))
            # character -> tile num
            self.custom_dict = {}
            for i in range(self.num_of_custom_assigned_tiles):
                char_no = self.bytes_to_int(fp.read(2))
                tile_no = self.bytes_to_int(fp.read(2))
                self.custom_dict[char_no] = tile_no
            fp.read(2) # padding
       

    def bytes_to_int(self, bts):
        return int.from_bytes(bts, self.byte_order_flag)

def merge_CMAP(cmaps: list[CMAP]):
    """
        return a dict {chara: (cmap_idx, tile_idx)}
    """
    ret_dict = {}
    for i in range(len(cmaps)):
        if cmaps[i].map_type == 0:
            tile_num = cmaps[i].tile_num_for_first_chara
            for chara in range(cmaps[i].first_character, cmaps[i].last_character + 1):
                ret_dict[chara] = (i, tile_num)
                tile_num += 1
        elif cmaps[i].map_type == 1:
            tile_num_idx = 0
            for chara in range(cmaps[i].first_character, cmaps[i].last_character + 1):
                ret_dict[chara] = (i, cmaps[i].tile_nums[tile_num_idx])
                tile_num_idx += 1
        elif cmaps[i].map_type == 2:
            for chara in cmaps[i].custom_dict.keys():
                ret_dict[chara] = (i, cmaps[i][chara])
        
    return ret_dict

#############################################################
class NFTR:
    """
        REF: https://problemkaputt.de/gbatek-ds-cartridge-nitro-font-resource-format.htm \n
    """
    def __init__(self, file_path: str):
        with open(file_path, "rb") as fp:
            self.get_header_chunk(fp)
            self.get_font_info_chunk(fp)
            self.get_character_glyph_chunk(fp)
            self.get_character_width_chunk(fp)
            self.get_character_map_chunks(fp)
        
    class FLAGS(Enum): 
        # chunk
        CHUNK_UNFOUND = -1,
        # byte order
        BO_BIG_ENDIAN = 0, # BO: byte order
        BO_LITTLE_ENDIAN = 1,
        # encoding
        ENC_UTF8 = 0,
        ENC_UNICODE = 1,
        ENC_SJIS = 2,
        ENC_CP1552 = 3,   

    chunk_offsets = {
        "header":                FLAGS.CHUNK_UNFOUND,
        "font_info":             FLAGS.CHUNK_UNFOUND,
        "character_glyph":       FLAGS.CHUNK_UNFOUND,
        "character_width":       FLAGS.CHUNK_UNFOUND,
        "first_character_map":   FLAGS.CHUNK_UNFOUND,
    }
    byte_order = FLAGS.BO_LITTLE_ENDIAN
    
    def bytes_to_int(self, bts):
        if self.byte_order == NFTR.FLAGS.BO_LITTLE_ENDIAN:
            byte_order_flag = "little"
        elif self.byte_order == NFTR.FLAGS.BO_LITTLE_ENDIAN:
            byte_order_flag = "big"

        return int.from_bytes(bts, byte_order_flag)

    # NFTR chunk
    def get_header_chunk(self, fp, offset=0):
        fp.seek(offset, os.SEEK_SET)

        # Header
        if (fp.read(4) != b"RTFN"):
            raise Exception("Not a Nitro Font file")

        self.chunk_offsets["header"] = 0

        # Byte Order -> FEFFh
        bo_b1 = fp.read(1) # byte order indicator byte 1
        bo_b2 = fp.read(1)
        if bo_b1 == b"\xff" and bo_b2 == b"\xfe":
            self.byte_order = NFTR.FLAGS.BO_LITTLE_ENDIAN
        elif bo_b1 == b"\xfe" and bo_b2 == b"\xff":
            self.byte_order = NFTR.FLAGS.BO_BIG_ENDIAN
        else:
            raise Exception("No byte order found")
        
        # Version
        self.version = self.bytes_to_int(fp.read(2))
        if not (self.version in [ 0x100, 0x101, 0x102]):
            print("unknow NFTR version {}".format(self.version))

        # Decompressed Resource Size
        self.decomp_res_size = self.bytes_to_int(fp.read(4))

        # Offset to "FNIF" Chunk, aka Size of "RTFN" Chunk (0010h)
        self.chunk_offsets["font_info"] = self.bytes_to_int(fp.read(2))
    
        # Total number of following Chunks (0003h+NumCharMaps) (0018h)
        self.num_of_following_chunk = self.bytes_to_int(fp.read(2))

        assert(fp.tell() == 16)

    # FINF chunk
    def get_font_info_chunk(self, fp, offset=-1):
        if (offset == -1 and self.chunk_offsets["font_info"]):
            offset = self.chunk_offsets["font_info"]
        fp.seek(offset, os.SEEK_SET)

        # FNIF Header
        if (fp.read(4) != b"FNIF"):
            raise Exception("FINF format error")
        
        # Chunk Size (1Ch or 20h)
        font_info_chunk_size = self.bytes_to_int(fp.read(4))
        if (font_info_chunk_size in [0x1c, 0x20]):
            self.font_info_chunk_size = font_info_chunk_size
        else:
            raise Exception("unknown font_info_chunk_size")

        # unknow/unused
        fp.read(1)

        # Height or Height+/-1, unsure
        self.height = self.bytes_to_int(fp.read(1))

        # Unknown (usually 00h, or sometimes 1Fh maybe for chr(3Fh)="?")
        temp = fp.read(1)

        # Unknown/unused (zero)
        temp = fp.read(2)

        # Width or Width+1, unsure
        self.width = self.bytes_to_int(fp.read(1))

        # Width_bis (?) 
        temp = fp.read(1)

        # encoding
        enc = self.bytes_to_int(fp.read(1))
        if enc == 0:
            self.encoding = NFTR.FLAGS.ENC_UTF8
        elif enc == 1:
            self.encoding = NFTR.FLAGS.ENC_UNICODE
        elif enc == 2:
            self.encoding = NFTR.FLAGS.ENC_SJIS
        elif enc == 3:
            self.encoding = NFTR.FLAGS.ENC_CP1552
        
        # Offset to Character Glyph chunk, plus 8
        self.offset_to_chara_glyph_chunk_p8 = \
            self.bytes_to_int(fp.read(4))
        
        # Offset to Character Width chunk, plus 8
        self.offset_to_chara_wdith_chunk_p8 = \
            self.bytes_to_int(fp.read(4))
    
        # Offset to first Character Map chunk, plus 8
        self.offset_to_chara_map_chunk_p8 = \
            self.bytes_to_int(fp.read(4))
    
        if self.font_info_chunk_size == 0x20:
            self.tile_height = self.bytes_to_int(fp.read(1))
            # Max Width or so +/-?   
            self.max_width = self.bytes_to_int(fp.read(1))
            # Underline location   
            self.underline_location = self.bytes_to_int(fp.read(1))
            # unknow/unused
            temp = self.bytes_to_int(fp.read(1))

        assert(fp.tell() == (offset + self.font_info_chunk_size))
        self.chunk_offsets["character_glyph"] = fp.tell()

    # CGLP (Character Glyph Chunk) (Tile Bitmaps)
    def get_character_glyph_chunk(self, fp, offset=-1):
        if (offset == -1 and self.chunk_offsets["character_glyph"]):
            offset = self.chunk_offsets["character_glyph"]
        fp.seek(offset, os.SEEK_SET)

        # FNIF Header
        if (fp.read(4) != b"PLGC"):
            raise Exception("CGLP format error")
    
        # Chunk Size (10h+NumTiles*siz+padding)
        self.chara_glyph_chunk_size = self.bytes_to_int(fp.read(4))

        # Tile Width in pixels
        self.tile_width = self.bytes_to_int(fp.read(1))
        # Tile height in pixels
        self.tile_height = self.bytes_to_int(fp.read(1))

        # Tile Size in bytes (siz=width*height*bpp+7)/8) = per character
        self.tile_bytes_size = self.bytes_to_int(fp.read(2))

        # underline location 
        self.chara_glyph_underline_location = self.bytes_to_int(fp.read(1))

        # Max proportional Width including left/right spacing
        self.max_proportional_width = self.bytes_to_int(fp.read(1))

        # Tile Depth (bits per pixel) (usually 1 or 2, sometimes 3)
        self.tile_depth = self.bytes_to_int(fp.read(1))

        # TODO
        # Tile Rotation (0=None/normal, other:
        # All tiles are starting on a byte boundary. However, the separate scanlines aren't
        # necessarily byte-aligned (for example, at 10pix width, a byte may contain rightmost
        # pixels of one line, followed by leftmost pixels of next line).
        # Bit7 of the first byte of a bitmap is the MSB of the upper-left pixel, 
        # bit6..0 are then containing the LSB(s) of the pixel (if bpp>1), followed by 
        # the next pixels of the scanline, followed by further scanlines; 
        # the data is arranged as straight Width*Height bitmap (without splitting into 8x8 sub-tiles).
        # Colors are ranging from Zero (transparent/background color) to all bit(s) set (solid/text color).
        # The meaning of the Tile Rotation entry is unclear
        # (one source claims 0=0', 1=90', 2=270', 3=180', and another source claims 0=0', 2=90', 
        # 4=180', 6=270', and for both sources, it's unclear 
        # if the rotation is meant to be clockwise or anti-clockwise).
        
        self.tile_rotation = self.bytes_to_int(fp.read(1))

        # bytes data stored 
        self.chara_glyphs = []
        
        cur_offset = 0x10
        while cur_offset < self.chara_glyph_chunk_size:
            data = fp.read(self.tile_bytes_size)
            glyph = BitImage(
                        data, 
                        self.tile_width, 
                        self.tile_height,
                        self.tile_depth
                    )
            self.chara_glyphs.append(glyph)
            cur_offset += self.tile_bytes_size

        self.chunk_offsets["character_width"] = offset + self.chara_glyph_chunk_size

    # CWDH chunk
    def get_character_width_chunk(self, fp, offset=-1):
        if offset == -1:
            offset = self.chunk_offsets["character_width"] 
        fp.seek(offset, os.SEEK_SET)
        
        # HDWC Header
        if (fp.read(4) != b"HDWC"):
            raise Exception("CWDH format error")
        
        # Character Width Chunk size
        self.chara_width_chunk_size = self.bytes_to_int(fp.read(4))

        # First Tile Number (should be 0000h)
        self.chara_width_num_first_tilex = self.bytes_to_int(fp.read(2))
        assert(self.chara_width_num_first_tilex == 0)

        # Last Tile Number  (should be NumTiles-1)
        self.chara_width_num_last_tile = self.bytes_to_int(fp.read(2))

        # unknown/unused
        temp = fp.read(4)
        
        # TODO 
        # below are tile bitmaps (Padding to 4-byte bound)
        for idx in range(self.chara_width_num_last_tile + 1):
            fp.read(1)
            fp.read(1)
            fp.read(1)

        paddings = (self.chara_width_num_last_tile + 1) * 3 // 4 * 4 + 4 \
                    -  (self.chara_width_num_last_tile + 1) * 3

        fp.read(paddings)

        if self.chara_glyph_chunk_size == 0x10 + (self.chara_width_num_last_tile + 1)*3 + paddings \
           and fp.tell() != (offset + self.chara_width_chunk_size):
            raise Exception("chunk size error in character wdith chunk")

        self.chunk_offsets["first_character_map"] = offset + self.chara_width_chunk_size
        
    # CMAP chunk
    # Character Map(s) - Translation Tables for ASCII/JIS/etc to Tile Numbers?
    def get_character_map_chunks(self, fp, offset=-1):
        if offset == -1:
            offset = self.chunk_offsets["first_character_map"] 
        fp.seek(offset, os.SEEK_SET)
       
        if self.byte_order == NFTR.FLAGS.BO_LITTLE_ENDIAN:
            bo_flag = "little"
        elif self.byte_order == NFTR.FLAGS.BO_BIG_ENDIAN:
            bo_flag = "big"
        
        self.chara_maps = []
        next_char_map_offset = offset 

        while True:
            char_map = CMAP(fp, offset=next_char_map_offset, byte_order_flag=bo_flag)
            if char_map.offset_to_next_map_p8 != 0:
                next_char_map_offset = char_map.offset_to_next_map_p8 - 8
                self.chara_maps.append(char_map)
            else:
                break
        
        self.merged_cmaps = merge_CMAP(self.chara_maps)

    def find_character_glyph(self, chara):
        if chara in self.merged_cmaps.keys():
            tp = self.merged_cmaps[chara]
            cmap_idx, tile_idx = tp[0], tp[1]
            return self.chara_glyphs[tile_idx]
        else:
            raise Exception("character not in NFTR")

#############################################################