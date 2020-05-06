# By Jake VanderPlas
# License: BSD-style

import matplotlib.pyplot as plt
import numpy as np
import sys


def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)


if __name__ == '__main__':
    N = 5

    x = np.random.randn(40)
    y = np.random.randn(40)
    c = np.random.randint(N, size=40)

    # Edit: don't use the default ('jet') because it makes @mwaskom mad...
    colormap = discrete_cmap(N, 'cubehelix')
    print(colormap)

    for i in range(0, 5):
        rgba = colormap(i / 5)
        color = (rgba[0], rgba[1], rgba[2])

        print(color)

    sys.exit(5)

    plt.scatter(x, y, c=c, s=50, cmap=discrete_cmap(N, 'cubehelix'))
    plt.colorbar(ticks=range(N))
    plt.clim(-0.5, N - 0.5)
    plt.show()
