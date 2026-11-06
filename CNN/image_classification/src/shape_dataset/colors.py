def luminance(color):
    def linear(value):
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
    return sum(weight * linear(channel) for weight, channel in zip((0.2126, 0.7152, 0.0722), color))


def contrast(a, b):
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)


def sample_colors(rng):
    background = tuple(rng.randrange(256) for _ in range(3))
    while True:
        foreground = tuple(rng.randrange(256) for _ in range(3))
        if contrast(background, foreground) >= 3:
            return background, foreground
