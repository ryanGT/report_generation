"""This module contains misc functions for programmatically generating
latex files."""

def split_table_labels_into_multiple_rows(labels, breakchar='\\', \
                                          first_column_blank=False):
    """For a latex table, I often have long column labels.  I like to
    manually determine where to break them, and then give each label
    multiple rows so they look nice.  This can be tedious to format
    correctly.  This function takes a list of labels that may or may
    not contain breakchar and converts it to latex code to make nice
    looking, multi-row labels.  It also determines how many blank rows
    are needed for labels that are shorter than the longest one."""
    big_list = []
    N = 1
    for label in labels:
        curlist = label.split(breakchar)
        if len(curlist) > N:#determine how many rows are needed to
                            #format all the labels nicely
            N = len(curlist)
        big_list.append(curlist)

    label_list = []

    for i in range(N):
        currow = []
        for ent in big_list:
            n = len(ent)
            offset = N-n
            if N-i > n:
                currow.append('')
            else:
                currow.append(ent[i-offset])
        curstr = ' & '.join(currow) + '\\\\'
        if first_column_blank:
            curstr = ' & ' + curstr
        label_list.append(curstr)
    return label_list
