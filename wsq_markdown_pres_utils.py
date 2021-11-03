import os, glob, shutil, txt_database, txt_mixin, re, pdb, rwkos
import datetime

ts_fmt = '%m/%d/%Y %H:%M:%S'


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)


def set_to_time(d, hour, minute=0):
    d = d.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return d


def reformat_timestamp(timestamp_str):
    ts_obj = datetime.datetime.strptime(timestamp_str, ts_fmt)
    str_out = ts_obj.strftime("%a %I:%M %p")
    return str_out


class wsq_markdown_maker(txt_database.txt_database_from_file):
    def __init__(self, csv_name, video_num):
        txt_database.txt_database_from_file.__init__(self, csv_name)
        self.csv_name = csv_name
        self.video_num = video_num
        self.md_list = []
        self.out = self.md_list.append


    def add_pres_title(self):
        self.out('# WSQ for Video %i' % self.video_num)
        self.out('')


    def _build_section(self, section_title, list_in, slide_title_pat="Question %i"):
        self.md_list.append("# %s" % section_title)
        self.md_list.append("")
        for i, item in enumerate(list_in):
            j = i+1
            s_title = slide_title_pat % j
            self.out('## %s' % s_title)
            self.out('')
            self.out(item)
            self.out('')


    def build_summaries(self):
        self._build_section("Summaries", self.Summary_of_the_Video, "Summary %i")


    def build_questions(self):
        self._build_section("Questions", self.Question_from_the_Video, "Question %i")


    def build_main_doc(self):
        N = len(self.Summary_of_the_Video)

        for i in range(N):
            j = i+1
            summary = self.Summary_of_the_Video[i]
            question = self.Question_from_the_Video[i]
            self.out("## Summary %s" % j)
            self.out("")
            self.out(summary)
            self.out("")
            self.out("## Question %s" % j)            
            self.out("")
            self.out(question)
            self.out("")
            fb = None
            if hasattr(self, "Feedback"):
                fb = self.Feedback[i]
            elif hasattr(self, "feedback"):
                fb = self.feedback[i]
            if fb is not None:
                self.out("## Feedback for Response %s" % j)
                self.out("")
                self.out(fb)
                self.out("")



    def get_default_grade(self, timestamp_str):
        """I offered extra credit for early WSQ submissiom in 345 F20.
        I am using this code to determine their default starting grade
        based on whether or not they submitted before 9AM (12 points),
        noon (11 points), or later (10 points).  I have not yet used
        this code to penalize late submissions."""
        ts_obj = datetime.datetime.strptime(timestamp_str, ts_fmt)
        if ts_obj < self.cutoff1:
            default_grade = 12
        elif ts_obj < self.cutoff2:
            default_grade = 11
        else:
            default_grade = 10
        return default_grade


    def find_grading_cutoffs(self):
        """The extra credit cutoffs are 9AM and Noon on Monday and
        Wednesday.  I need to determine which cutoff is relevant when
        the code is being run.

        When should the deadline be Monday and when should it be
        Wednesday?

        - if today is a Friday, Saturday, Sunday, or Monday,
            cutoff1 is Monday at 9AM
        - if today is a Wed. the cutoff is Wed. at 9AM
        - if today is a Tuesday or Thursday, is it before or after 10:30AM? 
        """
        now = datetime.datetime.now()
        wd = now.weekday()
        if wd in [0,4,5,6]:
            due_day = next_weekday(now, 0)#0 = Monday
        elif wd == 2:
            due_day = next_weekday(now, 2)#2 = Wed.
        elif wd == 1:
            # today is Tuesday, is it before class or not?
            test = set_to_time(now,10,30)#
            if now < test:
                # before class on Tuesday
                due_day = next_weekday(now, 0)#1 = Tuesday
            else:
                # after class on Tuesday
                due_day = next_weekday(now, 2)#3 = Thursday
        elif wd == 3:
            # today is Thursday, is it before class or not?
            test = set_to_time(now,10,30)#
            if now < test:
                # before class on Thursday
                due_day = next_weekday(now, 2)#3 = Thursday
            else:
                # after class on Thursday
                due_day = next_weekday(now, 0)#1 = Tuesday


        self.cutoff1 = set_to_time(due_day,9,5)#9:05
        self.cutoff2 = set_to_time(due_day,12,5)#12:05        


    def build_grading_doc(self, start_ind=0):
        """This function assumes we have a clean csv file with no
        feedback that is ultimately being made into a juptyer notebook
        for me to enter feedback and grades.

        In order to handle appending based on new rows in the csv, I
        am adding the start_ind option."""
        print("in build_grading_doc")
        N = len(self.Summary_of_the_Video)

        def out_one_item(pat, j=None):
            if j is None:
                self.out(pat)
            else:
                self.out(pat % j)
            self.out("")

        self.find_grading_cutoffs()
        print('='*30)
        print('')
        print('EC cutoff 1: %s' % self.cutoff1)
        print('EC cutoff 2: %s' % self.cutoff2)
        print('')
        print('='*30)

        for i in range(start_ind, N):
            j = i+1
            name = self.Your_Name[i]
            summary = self.Summary_of_the_Video[i]
            try:
                question = self.Question_from_the_Video[i]
            except:
                pdb.set_trace()
            try:
                timestamp = self.Timestamp[i]
            except:
                pdb.set_trace()

            print("timestamp = %s" % timestamp)

            self.out('# Student %i: %s' % (j, name))
            self.out('')
            self.out("## Summary %s" % j)
            self.out("")
            self.out(summary)
            self.out("")
            self.out("## Question %s" % j)            
            self.out("")
            self.out(question)
            self.out("")
            out_one_item("## Summary Feedback %i", j)
            # default summary feedback
            out_one_item("good summary")
            out_one_item("## Question Feedback %i", j)
            pretty_ts = reformat_timestamp(timestamp)
            self.out('### Timestamp %i: %s - %s' % (j,timestamp, pretty_ts))
            self.out('')
            ## - determine EC cutoffs
            ## - compare time stamps to cutoffs
            ## - determing default grade
            default_grade = self.get_default_grade(timestamp)
            out_one_item("## Grade %i", j)
            # default grade
            ## get time stamp here
            out_one_item("%s" % default_grade)


    def save(self):
        outname = "WSQ_markdown_for_video_%0.2i.md" % self.video_num
        txt_mixin.dump(outname, self.md_list)
        self.md_fn = outname


    def add_slides_glob(self, glob_pat):
        """Add slides by inserting markdown from a file that matches
        the glob pattern"""
        fn = glob.glob(glob_pat)
        if len(fn) == 1:
            myfile = txt_mixin.txt_file_with_list(fn[0])
            self.md_list.extend(myfile.list)


    def add_pre_slides(self):
        self.add_slides_glob("pre_*.md")


    def add_mid_slides(self):
        self.add_slides_glob("mid_*.md")


    def add_post_slides(self):
        self.add_slides_glob("post_*.md")


    def md_to_beamer(self):
        cmd = "md_to_beamer_pres.py %s" % self.md_fn
        os.system(cmd)


    def post_process_latex(self):
        fno, ext = os.path.splitext(self.md_fn)
        self.tex_name = fno + '.tex'
        tex_file = txt_mixin.txt_file_with_list(self.tex_name)
        latex_list = ['\\input{../wsq_header.tex}','', \
                      '\\begin{document}', '']

        mytitle = 'WSQ for Video %i' % self.video_num
        title_line = '\\title[%s]{%s' % (mytitle, mytitle)
        out = latex_list.append
        out(title_line)
        out('\\\\')
        out("\\large{EGR 445/545}}")
        out("\\author[Dr. Ryan Krauss]{Dr. Ryan Krauss}")
        out("\\date{}")
        out("\\maketitle")
        out("")
        latex_list.extend(tex_file.list)
        out("")
        out("\\end{document}")
        txt_mixin.dump(self.tex_name, latex_list)


    def run_latex(self):
        cmd = "pdflatex %s" % self.tex_name
        os.system(cmd)


    def main(self):
        #self.add_pres_title()
        self.add_pre_slides()
        self.build_summaries()
        self.add_mid_slides()
        self.build_questions()
        self.add_post_slides()
        self.save()
        self.md_to_beamer()
        # md to pres
        # latex post processing
        #   - header
        #   - title slide
        #   - end doc
        self.post_process_latex()
        self.run_latex()


    def doc_main(self):
        self.add_pre_slides()
        self.build_main_doc()
        self.add_mid_slides()
        self.add_post_slides()
        self.save_doc()


    def make_doc_name(self):
        outname = "WSQ_markdown_doc_for_video_%0.2i.md" % self.video_num
        return outname


    def save_doc(self):
        outname = self.make_doc_name()
        txt_mixin.dump(outname, self.md_list)
        self.md_fn = outname


    def make_grading_name(self):
        outname = "WSQ_markdown_grading_for_video_%0.2i.md" % self.video_num
        return outname


    def save_grading(self):
        # - test if it exists
        # - increment file name somehow if it does
        outname = self.make_grading_name()
        if os.path.exists(outname):
            fno, ext = os.path.splitext(outname)
            for i in range(2,100):
                new_name = fno + '_%0.2i.md' % i
                if not os.path.exists(new_name):
                    outname = new_name
                    break

        txt_mixin.dump(outname, self.md_list)
        self.md_fn = outname


    def find_start_ind(self): 
        outname = self.make_grading_name()

        if not os.path.exists(outname):
            return 0
        else:
            # find highest student # in the file
            # - should we be searching .ipynb instead of .md?
            #     - probably
            fno, ext = os.path.splitext(outname)
            jup_name = fno + '.ipynb'
            ## Find highest student number in the existing file
            myfile = txt_mixin.txt_file_with_list(jup_name)
            inds = myfile.findallre('# Student [0-9]+:', match=0)
            assert len(inds) > 0, "Did not find any students in %s" % jup_name
            last_student = myfile.list[inds[-1]]
            p = "# Student ([0-9]+):"
            q = re.search(p,last_student)
            start_ind = int(q.group(1))
            print("start_ind = %s" % start_ind)
            return start_ind


    def grading_main(self):
        start_ind =  self.find_start_ind()
        self.build_grading_doc(start_ind=start_ind)
        self.save_grading()


class rbg_sketching_wsq(wsq_markdown_maker):
    def _find_matches(self, folder, name):
        name_pat = "*%s*" % name
        full_pat = os.path.join(folder, name_pat)
        matches = glob.glob(full_pat)
        return matches

    
    def find_image_in_folder_by_name(self, folder, name):
        matches = self._find_matches(folder, name)
        if len(matches) == 0:
            if "Fiore" in name:
                name = "Nicholas Fiore"
            elif "Nicholas" in name:
                fname, lname = name.split(' ',1)
                name = "Nick " + lname.strip()
                
            matches = self._find_matches(folder, name)
        assert len(matches) > 0, "Did not find a match for %s" % name
        assert len(matches) == 1, "Found more than one match for %s" % name
        return matches[0]

        
    def find_sketch(self, name):
        hand_sketch_folder = r'/Users/kraussry/Google Drive/Teaching/345_F20/wsq_forms/WSQ for EGR 345 Video 15 (File responses)/Hand Sketch of your Bode Plot (jpg, png, pdf, ...) (File responses)'
        return self.find_image_in_folder_by_name(hand_sketch_folder, name)
    

    def copy_sketch(self, sketch_in_path, name):
        fno, ext = os.path.splitext(sketch_in_path)
        outfolder = "sketches"
        outname = rwkos.clean_filename("sketch_%s.%s" % (name, ext))
        outpath = os.path.join(outfolder, outname)
        shutil.copyfile(sketch_in_path, outpath)
        if ext.lower() == '.pdf':
            cmd = 'pdf_to_jpeg_one_page.py %s' % outpath
            os.system(cmd)
            pne, ext2 = os.path.splitext(outpath)
            outpath = pne + '.jpg'
        return outpath


    def find_verify_png(self, name):
        verify_folder = r'/Users/kraussry/Google Drive/Teaching/345_F20/wsq_forms/WSQ for EGR 345 Video 15 (File responses)/Python verification Bode plot (png, jpg, or pdf) from plt.savefig. (File responses)'
        return self.find_image_in_folder_by_name(verify_folder, name)        


    def copy_verify_png(self, pathin, name):
        fno, ext = os.path.splitext(pathin)
        outfolder = "verification_bodes"
        assert ext.lower() in ['.png','.jpg','.jpeg'], "did not receive a png or jpg: %s" % pathin
        outname = rwkos.clean_filename("verification_bode_%s.%s" % (name, ext.lower()))
        outpath = os.path.join(outfolder, outname)
        shutil.copyfile(pathin, outpath)
        return outpath
        

    def build_grading_doc(self, start_ind=0):
        N = len(self.Your_Name)

        def out_one_item(pat, j=None):
            if j is None:
                self.out(pat)
            else:
                self.out(pat % j)
            self.out("")

        self.find_grading_cutoffs()
        print('='*30)
        print('')
        print('EC cutoff 1: %s' % self.cutoff1)
        print('EC cutoff 2: %s' % self.cutoff2)
        print('')
        print('='*30)


        code_attr = self.find_attr_re(re.compile("Code.*"))
        q_attr = self.find_attr_re(re.compile("Question.*"))

        code_array = getattr(self, code_attr)
        q_array = getattr(self, q_attr)
        
        for i in range(start_ind, N):
            j = i+1
            #pdb.set_trace()
            name = self.Your_Name[i]
            code = code_array[i]
            question = q_array[i]

            sketch_in_path = self.find_sketch(name)
            sketch_out_path = self.copy_sketch(sketch_in_path, name)

            verify_in_path = self.find_verify_png(name)
            verify_out_path = self.copy_verify_png(verify_in_path, name)

            
            try:
                timestamp = self.Timestamp[i]
            except:
                pdb.set_trace()

            print("timestamp = %s" % timestamp)

            self.out('# Student %i: %s' % (j, name))
            self.out('')
            self.out("## Code %s" % j)
            self.out("")
            self.out(code)
            self.out("")
            self.out("## Sketch %s" % j)
            self.out('')
            self.out('<img src="%s" width=600px>' % sketch_out_path)
            self.out('')
            self.out("## Python Verification %s" % j)
            self.out('')
            self.out('<img src="%s" width=600px>' % verify_out_path)
            self.out('')
            self.out("## Question %s" % j)            
            self.out("")
            self.out(question)
            self.out("")
            out_one_item("## Sketch Feedback %i", j)
            # default summary feedback
            self.out("")
            out_one_item("## Question Feedback %i", j)
            pretty_ts = reformat_timestamp(timestamp)
            self.out('### Timestamp %i: %s - %s' % (j,timestamp, pretty_ts))
            self.out('')
            ## - determine EC cutoffs
            ## - compare time stamps to cutoffs
            ## - determing default grade
            default_grade = self.get_default_grade(timestamp)
            out_one_item("## Grade %i", j)
            # default grade
            ## get time stamp here
            out_one_item("%s" % default_grade)
    



class rbg_id_wsq(rbg_sketching_wsq):
    def copy_starting_bode(self, in_path, name):
        fno, ext = os.path.splitext(in_path)
        outfolder = "starting_bodes"
        outname = rwkos.clean_filename("starting_bode_%s.%s" % (name, ext))
        outpath = os.path.join(outfolder, outname)
        shutil.copyfile(in_path, outpath)
        if ext.lower() == '.pdf':
            cmd = 'pdf_to_jpeg_one_page.py %s' % outpath
            os.system(cmd)
            pne, ext2 = os.path.splitext(outpath)
            outpath = pne + '.jpg'
        return outpath


    def find_bode_starting(self, name):
        bode_folder = r'/Users/kraussry/Google Drive/Teaching/345_F20/wsq_forms/Modified WSQ for Video 15: RBG Part 1 (File responses)/Bode plot starting point from Python (png, jpg, or pdf) (File responses)'
        return self.find_image_in_folder_by_name(bode_folder, name)


    def build_grading_doc(self, start_ind=0):
        N = len(self.Your_Name)

        def out_one_item(pat, j=None):
            if j is None:
                self.out(pat)
            else:
                self.out(pat % j)
            self.out("")

        self.find_grading_cutoffs()
        print('='*30)
        print('')
        print('EC cutoff 1: %s' % self.cutoff1)
        print('EC cutoff 2: %s' % self.cutoff2)
        print('')
        print('='*30)


        code_attr = self.find_attr_re(re.compile("Code_.*"))
        q_attr = self.find_attr_re(re.compile("Question_.*"))

        code_array = getattr(self, code_attr)
        q_array = getattr(self, q_attr)

        for i in range(start_ind, N):
            j = i+1
            #pdb.set_trace()
            name = self.Your_Name[i]
            code = code_array[i]
            question = q_array[i]

            bode_in_path = self.find_bode_starting(name)
            bode_out_path = self.copy_starting_bode(bode_in_path, name)

            #verify_in_path = self.find_verify_png(name)
            #verify_out_path = self.copy_verify_png(verify_in_path, name)


            try:
                timestamp = self.Timestamp[i]
            except:
                pdb.set_trace()

            print("timestamp = %s" % timestamp)

            self.out('# Student %i: %s' % (j, name))
            self.out('')
            self.out("## Bode Starting Point %s" % j)
            self.out('')
            self.out('<img src="%s" width=600px>' % bode_out_path)
            self.out('')
            self.out("## Code %s" % j)
            self.out("")
            self.out(code)
            self.out("")
            #self.out("## Python Verification %s" % j)
            #self.out('')
            #self.out('<img src="%s" width=600px>' % verify_out_path)
            #self.out('')
            self.out("## Question %s" % j)            
            self.out("")
            self.out(question)
            self.out("")
            out_one_item("## System ID Feedback %i", j)
            # default summary feedback
            self.out("")
            out_one_item("## Question Feedback %i", j)
            pretty_ts = reformat_timestamp(timestamp)
            self.out('### Timestamp %i: %s - %s' % (j,timestamp, pretty_ts))
            self.out('')
            ## - determine EC cutoffs
            ## - compare time stamps to cutoffs
            ## - determing default grade
            default_grade = self.get_default_grade(timestamp)
            out_one_item("## Grade %i", j)
            # default grade
            ## get time stamp here
            out_one_item("%s" % default_grade)

    


class psq_markdown_maker(wsq_markdown_maker):
    def find_attr_starting_with(self, search_str):
        """Find the attribute that starts with search_str"""
        found = 0
        for attr in self.attr_names:
            if attr.find(search_str) == 0:
                return attr
            
    
    def __init__(self, csv_name, class_num):
        txt_database.txt_database_from_file.__init__(self, csv_name)
        self.csv_name = csv_name
        self.class_num = class_num
        self.md_list = []
        self.out = self.md_list.append
        self.summary_attr = self.find_attr_starting_with("Summary")
        self.question_attr = self.find_attr_starting_with("Question")
        

    def add_pres_title(self):
        self.out('# PSQ for Class %i' % self.class_num)
        self.out('')
    


    def build_grading_doc(self, start_ind=0):
        """This function assumes we have a clean csv file with no
        feedback that is ultimately being made into a juptyer notebook
        for me to enter feedback and grades.
    
        In order to handle appending based on new rows in the csv, I
        am adding the start_ind option."""
        print("in build_grading_doc")
        summaries = getattr(self, self.summary_attr)
        questions = getattr(self, self.question_attr)
        
        N = len(summaries)

        def out_one_item(pat, j=None):
            if j is None:
                self.out(pat)
            else:
                self.out(pat % j)
            self.out("")

        self.find_grading_cutoffs()
        print('='*30)
        print('')
        print('EC cutoff 1: %s' % self.cutoff1)
        print('EC cutoff 2: %s' % self.cutoff2)
        print('')
        print('='*30)

        for i in range(start_ind, N):
            j = i+1
            name = self.Your_Name[i]
            summary = summaries[i]
            question = questions[i]

            try:
                timestamp = self.Timestamp[i]
            except:
                pdb.set_trace()

            print("timestamp = %s" % timestamp)

            self.out('# Student %i: %s' % (j, name))
            self.out('')
            self.out("## Summary %s" % j)
            self.out("")
            self.out(summary)
            self.out("")
            self.out("## Question %s" % j)            
            self.out("")
            self.out(question)
            self.out("")
            out_one_item("## Summary Feedback %i", j)
            # default summary feedback
            out_one_item("good summary")
            out_one_item("## Question Feedback %i", j)
            pretty_ts = reformat_timestamp(timestamp)
            self.out('### Timestamp %i: %s - %s' % (j,timestamp, pretty_ts))
            self.out('')
            ## - determine EC cutoffs
            ## - compare time stamps to cutoffs
            ## - determing default grade
            #default_grade = self.get_default_grade(timestamp)
            default_grade = 10
            out_one_item("## Grade %i", j)
            # default grade
            ## get time stamp here
            out_one_item("%s" % default_grade)


    def make_grading_name(self):
        outname = "PSQ_markdown_grading_for_class_%0.2i.md" % self.class_num
        return outname
