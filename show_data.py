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

num_rows = 0
with open('oncampus_data.csv','r') as csvfile:
    plots = csv.reader(csvfile, delimiter=',')
    for row in plots:
        try:
            if (row[0][0] == "d") and (row[0][1] == 's'):
                
                if num_rows < 8: # distinguishes transfers from source to UAB.
                    src_to_oncampx.append(ds_sizes.get(row[0]))
                    src_to_oncampy.append(float(row[3]))
                    
                if num_rows >= 8: # distinguishes transfers from UAB to source.
                    oncampx_to_src.append(ds_sizes.get(row[0]))
                    oncampy_to_src.append(float(row[3]))
            
            num_rows += 1
            
        except IndexError:
            # blank text will have been caught here
            pass

num_rows = 0
with open('offcampus_data.csv','r') as csvfile:
    plots = csv.reader(csvfile, delimiter=',')
    for row in plots:
        try:
            if (row[0][0] == "d") and (row[0][1] == 's'):
                
                if num_rows < 8: # distinguishes transfers remote to local 
                    src_to_offcampx.append(ds_sizes.get(row[0]))
                    src_to_offcampy.append(float(row[3]))
                    
                if num_rows >= 8: # distinguishes transfers local to remote. 
                    offcampx_to_src.append(ds_sizes.get(row[0]))
                    offcampy_to_src.append(float(row[3]))
            
            num_rows += 1
            
        except IndexError:
            # blank text will have been caught here
            pass

x = np.arange(len(ds_names))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots(2, 1)
fig.set_figheight(7)
fig.set_figwidth(9)

rects1 = ax[0].bar(x - width/2, src_to_oncampy, width, label='Source > OnCampus')
rects2 = ax[0].bar(x + width/2, oncampy_to_src, width, label='OnCampus > Source')

rects3 = ax[1].bar(x - width/2, src_to_offcampy, width, label='Source > OffCampus')
rects4 = ax[1].bar(x + width/2, offcampy_to_src, width, label='OffCampus > Source')


# Add some text for labels, title and custom x-axis tick labels, etc.
ax[0].set_ylabel('Speed (MB/s)')
ax[0].set_title('DTN Comparison to and from OnCampus Endpoint')
ax[0].set_xticks(x)
ax[0].set_xticklabels(ds_names)
ax[0].legend()

ax[1].set_ylabel('Speed (MB/s)')
ax[1].set_title('DTN Comparison to and from OffCampus Endpoint')
ax[1].set_xticks(x)
ax[1].set_xticklabels(ds_names)
ax[1].legend()

def autolabel(rects, num):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax[num].annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

autolabel(rects1, 0)
autolabel(rects2, 0)

autolabel(rects3, 1)
autolabel(rects4, 1)

fig.tight_layout()

plt.show() 
