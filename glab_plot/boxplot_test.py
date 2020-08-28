import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoLocator, AutoMinorLocator
from termcolor import colored


def printHeadTailDataFrame(df: pd.DataFrame, name: str, index: str = True, head: int = 10, tail: int = 10):
    """
    printHeadTailDataFrame prints the head first/tail last rows of the dataframe df

    :param df: dataframe to print
    :type df: dataframe
    :param name: name for dataframe (def ``DataFrame``)
    :type name: string
    :param head: nr of lies from start of df
    :type head: int
    :param tail: nr of lies from start of df
    :type tail: int
    :param index: display the index of the dataframe or not
    :type: bool
    """
    if df.shape[0] <= (head + tail):
        print('\n   ...  %s (size %d)\n%s' % (colored(name, 'green'), df.shape[0], df.to_string(index=index)))
    else:
        print('\n   ... Head of %s (size %d)' % (colored(name, 'green'), df.shape[0]))
        print(df.head(n=head).to_string(index=index))
        print('   ... Tail of %s (size %d)\n%s' % (colored(name, 'green'), df.shape[0], df.tail(n=tail).to_string(index=index)))


# using differently scaled data for the different random series:
df = pd.DataFrame(
    np.asarray([
        np.random.rand(140),
        2 * np.random.rand(140),
        4 * np.random.rand(140),
        8 * np.random.rand(140),
    ]).T,
    columns=['A', 'B', 'C', 'D']
)

printHeadTailDataFrame(df=df, name='df', index=False)


df['models'] = pd.Series(np.repeat([
    'model1', 'model2', 'model3', 'model4', 'model5', 'model6', 'model7'
], 20))

printHeadTailDataFrame(df=df, name='df', index=False)

# creating the boxplot array:
bp_dict = df.boxplot(
    by="models",
    layout=(2, 2),
    figsize=(6, 8),
    return_type='both',
    patch_artist=True,
    rot=45,
)

colors = ['b', 'y', 'm', 'c', 'g', 'b', 'r', 'k', ]

# adjusting the Axes instances to your needs
for row_key, (ax, row) in bp_dict.items():
    print(row_key)
    print(ax)
    print(row)
    print()
    ax.set_xlabel('')
    ax.set_ylabel('AMAM')

    # removing shared axes:
    grouper = ax.get_shared_y_axes()
    shared_ys = [a for a in grouper]
    for ax_list in shared_ys:
        for ax2 in ax_list:
            grouper.remove(ax2)

    # setting limits:
    ax.axis('auto')
    ax.relim()      # <-- maybe not necessary

    # adjusting tick positions:
    ax.yaxis.set_major_locator(AutoLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    # making tick labels visible:
    plt.setp(ax.get_yticklabels(), visible=True)

    for i, box in enumerate(row['boxes']):
        box.set_facecolor(colors[i])

plt.show()
