import csv

bottle_list = []

# Read all data from the csv file.
with open('a.csv', 'rb') as b:
    bottles = csv.reader(b)
    bottle_list.extend(bottles)

# data to override in the format {line_num_to_override:data_to_write}.
line_to_override = {1: ['e', 'c', 'd']}

# Write data to the csv file and replace the lines in the line_to_override dict.
with open('a.csv', 'wb') as b:
    writer = csv.writer(b)
    for line, row in enumerate(bottle_list):
        data = line_to_override.get(line, row)
        writer.writerow(data)









import csv, os

with open('path/to/filename') as inf, open('path/to/filename_temp', 'w') as outf:
    reader = csv.reader(inf)
    writer = csv.writer(outf)
    for line in reader:
        if line[1] == '0':
           ...
        ... # as above

os.remove('path/to/filename')
os.rename('path/to/filename_temp', 'path/to/filename')
