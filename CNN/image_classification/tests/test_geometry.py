import random
import unittest
from shape_dataset.colors import contrast, sample_colors
from shape_dataset.geometry import sample_shape

class GeometryTests(unittest.TestCase):
    def test_colors_and_bounds(self):
        rng = random.Random(42)
        for kind in ('circle', 'rectangle', 'triangle'):
            for _ in range(100):
                bg, fg = sample_colors(rng)
                self.assertGreaterEqual(contrast(bg, fg), 3)
                shape = sample_shape(kind, rng)
                for x,y in shape['points']:
                    self.assertTrue(0 <= x < 1920 and 0 <= y < 1080)
    def test_triangle_angles_and_inradius(self):
        import math
        rng = random.Random(73)
        for _ in range(300):
            points=sample_shape('triangle',rng)['points']
            sides=[math.dist(points[i],points[(i+1)%3]) for i in range(3)]
            for i in range(3):
                a,b,c=sides[i-1],sides[i],sides[(i+1)%3]
                angle=math.degrees(math.acos(max(-1,min(1,(a*a+b*b-c*c)/(2*a*b)))))
                self.assertGreaterEqual(angle,20)
            a,b,c=sides; semiperimeter=(a+b+c)/2
            area=math.sqrt(semiperimeter*(semiperimeter-a)*(semiperimeter-b)*(semiperimeter-c))
            self.assertGreaterEqual(area/semiperimeter,120)
    def test_square_can_be_sampled(self):
        from unittest.mock import patch
        rng=random.Random(8)
        # Bounding boxes of rotated squares need not be integral-equal; compare side lengths.
        with patch.object(rng, 'randrange', return_value=0):
            points=sample_shape('rectangle',rng)['points']
        import math
        self.assertLess(abs(math.dist(points[0],points[1])-math.dist(points[1],points[2])),2)
