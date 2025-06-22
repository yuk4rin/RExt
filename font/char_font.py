from PIL import Image, ImageDraw, ImageFont
from typing import Union
import numpy as np

class CharFont:

    def __init__(self, cfont, size: int=12, 
                 top_left_pos: tuple=(0, 0)):
        self._font_meta = cfont
        self.top_left_pos = top_left_pos
        self.size = size

    def char_image(self, 
                   chara: str,
                   size: Union[int, None] = None,  # font size 
                   w: int = -1, h: int = -1,       # canvas size
                   top_left_pos:Union[tuple, None] = None,
                   mode: str = "L"):
        """
            @param: mode, 'L' (8 bits) or '1' (1 bits) 
            ref: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
        """
        assert(mode in ['L', '1'])
                       
        if w == -1 or h == -1:
            canvas_size = (size, size)
        else:
            canvas_size = (w, h)

        if not top_left_pos:
            top_left_pos = self.top_left_pos
        if not size:
            size = self.size
        
        font = ImageFont.truetype(self._font_meta, size=size)

        canvas = Image.new(mode, canvas_size, color="white")
        draw_char = ImageDraw.Draw(canvas)
        draw_char.text(top_left_pos, chara, font=font, fill="black")
        
        # canvas.show()
        return np.array(canvas)
    