import matplotlib.pyplot as plt
import numpy as np
import csv

# File parse
ds_sizes = {'ds01': 0.1, 'ds04':10, 'ds06':100, 'ds08': 1000, 'ds10': 1000, 'ds12':100, 
            'ds14': 5000, 'ds16': 1000} # sizes given in gigabytes

ds_names = ['ds01', 'ds04', 'ds06', 'ds08', 'ds10', 'ds12', 
            'ds14', 'ds16']

src_to_oncampx = []
src_to_oncampy = []
oncampx_to_src = []
oncampy_to_src= []

src_to_offcampx = []
src_to_offcampy = []
offcampx_to_src = []
offcampy_to_src= []


def parse_dtn_data(filename, x_in, x_out, y_in, y_out):
    """
    filename: string
    x_axis: string[]
    y_in, y_out: int[]
    """
    num_rows = 0
    with open(filename,'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            try:
                if (row[0][0] == "d") and (row[0][1] == 's'):

                    if num_rows < 8: # distinguishes transfers from source to UAB.
                        x_in.append(ds_sizes.get(row[0]))
                        y_in.append(float(row[3]))

                    if num_rows >= 8: # distinguishes transfers from UAB to source.
                        x_out.append(ds_sizes.get(row[0]))
                        y_out.append(float(row[3]))

                num_rows += 1

            except IndexError:
                # blank text will have been caught here
                pass


def autolabel(rects, num):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax[num].annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


x = np.arange(len(ds_names))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots(2, 1)
fig.set_figheight(7)
fig.set_figwidth(9)


def build_graph(num, endpoint, campus, data1, data2):

    rects1 = ax[num].bar(x - width / 2, data1, width, label='{} > {}'.format(endpoint, campus))
    rects2 = ax[num].bar(x + width / 2, data2, width, label='{} > {}'.format(campus, endpoint))

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax[num].set_ylabel('Speed (MB/s)')
    ax[num].set_title('DTN Comparison to and from {} Endpoint'.format(campus))
    ax[num].set_xticks(x)
    ax[num].set_xticklabels(ds_names)
    ax[num].legend()

    autolabel(rects1, num)
    autolabel(rects2, num)


def show_graphs():

    build_graph(0, "cac_dtn_test", "OnCampus", src_to_oncampy, oncampy_to_src)
    build_graph(1, "cac_dtn_test", "OffCampus", src_to_offcampy, offcampy_to_src)

    fig.tight_layout()

    plt.show()


def main():
    parse_dtn_data("oncampus_data.csv", src_to_oncampx, oncampx_to_src, src_to_oncampy, oncampy_to_src)
    parse_dtn_data("offcampus_data.csv", src_to_offcampx, offcampx_to_src, src_to_offcampy, offcampy_to_src)
    show_graphs()


if __name__ == "__main__":
    main()
