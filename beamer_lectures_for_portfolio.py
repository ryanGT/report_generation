import os
import file_finder

def remove_exts_from_list(listin):
    listout = []
    for filename in listin:
        pne, ext = os.path.splitext(filename)
        listout.append(pne)
    return listout


def find_beamer_lectures(lecture_path):
    #Search for all rst's that have matching pdf's that aren't in
    #"exclude" directories
    rst_finder = file_finder.File_Finder(lecture_path, \
                                         extlist=['.rst'], \
                                         skipdirs=['exclude'])
    rst_files = rst_finder.Find_All_Files()

    pdf_finder = file_finder.File_Finder(lecture_path, \
                                         extlist=['.pdf'], \
                                         skipdirs=['exclude'])
    pdf_files = pdf_finder.Find_All_Files()
    
    rst_list = remove_exts_from_list(rst_files)
    pdf_list = remove_exts_from_list(pdf_files)
    filt_list = [item for item in rst_list if item in pdf_list]
    filt_list.sort()
    return filt_list


def make_all_handouts(pathlist):
    """This function takes a list of paths that do not have extensions
    and runs 'rst2beamer_rwk.py --handouts
    --theme=ryansiuemostlywhite' on them"""
    base_cmd = 'rst2beamer_rwk.py --handouts --theme=ryansiuemostlywhite %s'
    curdir = os.getcwd()
    try:
        for pne in pathlist:
            curpath = pne + '.rst'
            folder, rstname = os.path.split(curpath)
            os.chdir(folder)
            cmd = base_cmd % rstname
            os.system(cmd)
    finally:
        os.chdir(curdir)
        

def make_pdf_paths(pnelist):
    """add .pdf to a list of paths with not extensions"""
    outlist = [item + '.pdf' for item in pnelist]
    return outlist


def merge_handouts(pathlist, dest_path):
    path_str = ' '.join(pathlist)
    cmd = 'pdftk_merge.py %s %s' % (path_str, dest_path)
    print(cmd)
    os.system(cmd)
    

def run_one_course(lecture_path, pdf_out_path):
    filt_paths = find_beamer_lectures(lecture_path)
    make_all_handouts(filt_paths)
    pdflist = make_pdf_paths(filt_paths)
    merge_handouts(pdflist, pdf_out_path)
    return pdflist

    
if __name__ is '__main__':
    run_592 = 0
    if run_592:
        mypath_592 = '/home/ryan/siue/classes/nonlinear_controls/2011/lectures/'
        outpath_592 = '/home/ryan/siue/tenure/course_portfolios/592_nonlinear_controls/beamer_lectures.pdf'
        pdf_paths_592 = run_one_course(mypath_592, outpath_592)
    run_452 = 0
    if run_452:
        mypath_452 = '/home/ryan/siue/classes/452/2011/lectures'
        outpath_452 = '/home/ryan/siue/tenure/course_portfolios/452/beamer_lectures.pdf'
        pdf_paths_452 = run_one_course(mypath_452, outpath_452)

    run_450 = 1
    if run_450:
        mypath_450 = '/home/ryan/siue/classes/450/2010/lectures'
        outpath_450 = '/home/ryan/siue/tenure/course_portfolios/450/beamer_lectures.pdf'
        pdf_paths_450 = run_one_course(mypath_450, outpath_450)
