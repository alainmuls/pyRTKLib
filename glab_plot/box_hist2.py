import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

sns.set(style="ticks")

x = np.random.randn(100)

f, (ax_box, ax_hist) = plt.subplots(nrows=2, ncols=2, sharex=True, gridspec_kw={"height_ratios": (.15, .85)})

print('ax_box = {!s}'.format(ax_box))
print('ax_hist = {!s}'.format(ax_hist))

sns.boxplot(x, ax=ax_box[0])
sns.distplot(x, ax=ax_hist[0])

ax_box[0].set(yticks=[])
sns.despine(ax=ax_hist[0])
sns.despine(ax=ax_box[0], left=True)

sns.boxplot(x, ax=ax_box[1])
sns.distplot(x, ax=ax_hist[1])

ax_box[1].set(yticks=[])
sns.despine(ax=ax_hist[1])
sns.despine(ax=ax_box[1], left=True)

plt.show()
