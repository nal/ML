import io
import math
import random
from PIL import Image, ImageDraw
from .colors import sample_colors
from .config import CLASSES, HEIGHT, SETS, WIDTH
from .geometry import sample_shape


def orientation(kind, geom):
    period = math.pi / 2 if kind == "rectangle" and geom.get("square") else math.pi if kind == "rectangle" else math.tau
    return round(geom["angle"] % period, 6)


def generate(train_seed, held_out_seed):
    output = {}
    for role, seed in (('train', train_seed), ('held-out', held_out_seed)):
        rng = random.Random(seed)
        for kind in CLASSES:
            values = [set(), set(), set(), set()]
            for index in range(1, SETS[role]+1):
                while True:
                    geom = sample_shape(kind, rng)
                    bg, fg = sample_colors(rng)
                    props = (geom['position'], geom['size'], fg, orientation(kind, geom))
                    # Guarantee variation by the last candidate without coupling sets.
                    required = 3 if kind == 'circle' else 4
                    if index != SETS[role] or all(len(values[i] | {props[i]}) >= 2 for i in range(required)): break
                for i, prop in enumerate(props): values[i].add(prop)
                img = Image.new('RGB', (WIDTH, HEIGHT), bg)
                draw = ImageDraw.Draw(img)
                if kind == 'circle': draw.ellipse(geom['points'], fill=fg)
                else: draw.polygon(geom['points'], fill=fg)
                buf = io.BytesIO(); img.save(buf, format='PNG', optimize=False, compress_level=6)
                output[f'{role}/{kind}/{index:02}.png'] = buf.getvalue()
    return output
