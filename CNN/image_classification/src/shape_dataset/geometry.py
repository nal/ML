import math


def sample_shape(kind, rng):
    # A triangle derived from a wide isosceles base, with a variable apex,
    # retains a large interior while allowing arbitrary sampled vertices.
    while True:
        angle = 0 if kind == 'circle' else rng.uniform(0, math.tau)
        if kind == 'circle':
            radius = rng.randint(120, 300)
            points = [(-radius, -radius), (radius, radius)]
        elif kind == 'rectangle':
            w = rng.randint(240, 550)
            h = w if rng.randrange(8) == 0 else rng.randint(240, 550)
            points = [(-w/2,-h/2), (w/2,-h/2), (w/2,h/2), (-w/2,h/2)]
        else:
            w, h = rng.randint(440, 650), rng.randint(440, 650)
            apex = rng.uniform(-0.15, 0.15) * w
            points = [(-w/2, h/2), (w/2, h/2), (apex, -h/2)]
            sides = [math.dist(points[i], points[(i+1)%3]) for i in range(3)]
            area = w*h/2
            inradius = 2*area/sum(sides)
            angles = [math.degrees(math.acos(max(-1, min(1, (sides[(i-1)%3]**2+sides[i]**2-sides[(i+1)%3]**2)/(2*sides[(i-1)%3]*sides[i]))))) for i in range(3)]
            if inradius < 120 or min(angles) < 20:
                continue
        c, s = math.cos(angle), math.sin(angle)
        rotated = [(x*c-y*s, x*s+y*c) for x,y in points]
        minx, maxx = min(x for x,y in rotated), max(x for x,y in rotated)
        miny, maxy = min(y for x,y in rotated), max(y for x,y in rotated)
        cx = rng.randint(math.ceil(-minx), math.floor(1919-maxx))
        cy = rng.randint(math.ceil(-miny), math.floor(1079-maxy))
        coords = [(round(x+cx), round(y+cy)) for x,y in rotated]
        xs, ys = zip(*coords)
        return {'points': coords, 'position': (cx,cy), 'size': (max(xs)-min(xs), max(ys)-min(ys)), 'angle': angle, 'square': kind == 'rectangle' and w == h}
