import os

def find_gs_files(pdfname, fmt='_%0.4i', ext='.jpg'):
    fno, inext = os.path.splitext(pdfname)
    fullpat = fno + fmt + ext
    filenames = []
    for i in range(1,1000):
        cur_name =  fullpat % i
        if os.path.exists(cur_name):
            filenames.append(cur_name)
        else:
            break

    return filenames


def jpeg_list_to_pdf(filelist, outname, indir='.'):
    epsdir = os.path.join(indir,'temp')

    if not os.path.exists(epsdir):
        os.mkdir(epsdir)

    pdftklist = []
    for filename in filelist:
        folder, name = os.path.split(filename)
        name_only, ext = os.path.splitext(name)
        epsname = name_only+'.eps'
        outpath = os.path.join(epsdir, epsname)
        cmd = 'jpeg2ps '+filename +' > '+outpath
        print cmd
        os.system(cmd)
        cmd2 = 'epstopdf '+outpath
        print cmd2
        os.system(cmd2)
        pdfname = name_only+'.pdf'
        pdfpath = os.path.join(epsdir, pdfname)
        pdftklist.append(pdfpath)

    pdftkcmd = 'pdftk '+' '.join(pdftklist)+ ' output ' + outname
    print pdftkcmd
    os.system(pdftkcmd)

    return pdftklist
