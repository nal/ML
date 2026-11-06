import io
import unittest
from PIL import Image
from shape_dataset.generate import generate

class GenerationTests(unittest.TestCase):
    def test_counts_and_images(self):
        images=generate(42,43)
        self.assertEqual(len(images),45)
        for role, count in [('train',10),('held-out',5)]:
            for kind in ('circle','rectangle','triangle'):
                selected=[v for k,v in images.items() if k.startswith(f'{role}/{kind}/')]
                self.assertEqual(len(selected),count)
                for data in selected:
                    with Image.open(io.BytesIO(data)) as image:
                        self.assertEqual((image.size,image.mode,image.format),((1920,1080),'RGB','PNG'))
    def test_variation_per_class(self):
        from unittest.mock import patch
        import shape_dataset.generate as module
        original=module.sample_shape; captured=[]
        def capture(kind,rng):
            shape=original(kind,rng); captured.append((kind,shape)); return shape
        with patch.object(module,'sample_shape',side_effect=capture): images=module.generate(42,43)
        offset=0
        for role,count in [('train',10),('held-out',5)]:
            for kind in ('circle','rectangle','triangle'):
                shapes=[shape for _,shape in captured[offset:offset+count]]; offset+=count
                self.assertGreaterEqual(len({x['position'] for x in shapes}),2)
                self.assertGreaterEqual(len({x['size'] for x in shapes}),2)
                if kind!='circle': self.assertGreaterEqual(len({module.orientation(kind, x) for x in shapes}),2)
                colors=set()
                for i in range(1,count+1):
                    with Image.open(io.BytesIO(images[f'{role}/{kind}/{i:02}.png'])) as image:
                        colors.add(min(image.getcolors(1920*1080),key=lambda x:x[0])[1])
                self.assertGreaterEqual(len(colors),2)

    def test_orientation_symmetry(self):
        import math
        from shape_dataset.generate import orientation
        self.assertEqual(orientation('rectangle', {'angle': 0.2, 'square': True}), orientation('rectangle', {'angle': 0.2 + math.pi/2, 'square': True}))
        self.assertEqual(orientation('rectangle', {'angle': 0.2, 'square': False}), orientation('rectangle', {'angle': 0.2 + math.pi, 'square': False}))
        self.assertEqual(orientation('triangle', {'angle': 0.2}), orientation('triangle', {'angle': 0.2 + math.tau}))
