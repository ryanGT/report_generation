import txt_mixin, os

def list_to_table_row(listin):
    row_str = ' & '.join(listin)
    row_str += ' \\\\'
    return row_str


def csv_header(headerpath=None, \
               lhead='', rhead='', chead='', \
               lfoot='', rfoot='', cfoot=''):

    if headerpath is None:
        if os.path.exists('header.tex'):
            headerpath = 'header.tex'
        else:
            headerpath = '/Users/rkrauss/git/report_generation/class_list_header.tex'
            
    headerline = '\\input{%s}' % headerpath
    latex_out = [headerline]
    out = latex_out.append
    out('\\pagestyle{fancy}')
    ws = ' '*4
    out(ws + '\\lhead{%s}' % lhead)
    out(ws + '\\rhead{%s}' % rhead)
    out(ws + '\\chead{%s}' % chead)
    out(ws + '\\rfoot{%s}' % rfoot)
    out(ws + '\\lfoot{%s}' % lfoot)
    out(ws + '\\cfoot{%s}' % cfoot)
    out('\\renewcommand{\headrulewidth}{0pt}')
    out('\\begin{document}')
    return latex_out


def csv_to_latex_table(csvlist, labels=None, extra_col_labels=None, \
                       fmt_str=None, vrule='\\rule{0pt}{14pt}', \
                       hrule=None, headerpath=None, outpath=None, \
                       items_per_page=20, delim=',', \
                       lhead='', rhead='', chead='', \
                       lfoot='', rfoot='', cfoot='', \
                       just_tabular=False):#cfoot='\\thepage'
    if labels is None:
        labels = csvlist.pop(0)

    if type(labels) == str:
        labels = labels.split(delim)

    if extra_col_labels is not None:
        labels.extend(extra_col_labels)

    if fmt_str is None:
        N = len(labels)
        fmt_str = '|l' * N + '|'


    startline = '\\begin{tabular}{%s}' % fmt_str

    if just_tabular:
        latex_out = [startline]
    else:
        latex_out = csv_header(headerpath, \
                               lhead=lhead, rhead=rhead, chead=chead, \
                               lfoot=lfoot, rfoot=rfoot, cfoot=cfoot)
        latex_out.append(startline)

    out = latex_out.append
            
    out('\\hline')

    label_row = list_to_table_row(labels)


    out(label_row)
    out('\\hline')

    if extra_col_labels is None:
        Nec = 0
    else:
        Nec = len(extra_col_labels)


    for i, row in enumerate(csvlist):
        if type(row) == str:
            if delim is None:
                row = [row]
            else:
                row = row.split(delim)
        if (i % 2) == 0:
            out('\\rowcolor[gray]{0.9}')
        curlist = row
        if hrule is None:
            eclist = ['']*Nec
        else:
            eclist = [hrule]*Nec
        curlist += eclist
        last = curlist[-1]
        last += ' ' + vrule
        curlist[-1] = last
        currow = list_to_table_row(curlist)
        out(currow)
        out('\\hline')

        if i == items_per_page:
            out('\\end{tabular}')
            out('')
            out('\\pagebreak')
            out(startline)
            out('\\hline')
            out(label_row)
            out('\\hline')

    out('\\end{tabular}')

    if not just_tabular:
        out('\\end{document}')

    if outpath is not None:
        txt_mixin.dump(outpath, latex_out)

    return latex_out
