import csv

def load_categories():
    filename = '/app/lib/categories.csv'
    prompts = list()
    with open(filename) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            prompts.append(row)
    return prompts
