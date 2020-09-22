import txt_mixin, rwkos
#from IPython.core.debugger import Pdb
import os, copy, txt_database
import basic_file_ops
import re
import pdb

title_p = re.compile('^ +"#+ (.*)')
heading_level_p = re.compile('^ +"(#+) .*')
hide_py_p = re.compile('^ +"# *hide')

def find_header_level(header_line,debug=False):
    pound_match = heading_level_p.search(header_line).group(1)
    pound_match = pound_match.strip()
    if debug:
        print("pound_match = %s" % pound_match)
    mylevel = len(pound_match)
    return mylevel


def clean_one_line_of_src_text(line_in):
    # notebook src text has leading spaces and has leading and trailing "'s
    lineout = line_in.strip()

    # leadning quote removal
    if lineout[0] == '"':
        lineout = lineout[1:]

    # multi-line cells end in ", while the last line or single line cells
    # just end in "
    if lineout[-2:] == '",':
        lineout = lineout[0:-2]
    elif lineout[-1] == '"':
        lineout = lineout[0:-1]

    lineout = lineout.replace('\\n','\n')
    lineout = lineout.strip()
    return lineout


class nb_cell(object):
    def find_source(self):
        start_ind = self.lines.find('   "source": [')
        if "[]" in self.lines[start_ind]:
            self.source = []
        else:
            assert self.lines[-2] == '   ]'
            self.source = self.lines[start_ind+1:-2]
        self.start_ind = start_ind


    def replace_source(self, new_src):
        start_ind = self.lines.find('   "source": [')
        assert self.lines[-2] == '   ]'
        self.lines[start_ind+1:-2] = []
        self.lines[start_ind+1:start_ind+1] = new_src



    def clean_celltype(self):
        bad_list = ['"',',']
        for s in bad_list:
            self.celltype = self.celltype.replace(s,"")
            
            
    def __init__(self, lines):
        assert lines[0] == '  {', "problem with first line of cell"
        assert lines[-1].find('  }') == 0, "problem with last line of cell"
        assert lines[1].find('"cell_type":') == 3, "problem with second line"
        temp, celltype = lines[1].split(":")
        celltype = celltype.strip()
        self.celltype = celltype
        self.clean_celltype()
        self.lines = txt_mixin.txt_list(lines)
        self.find_source()
        

class jupyter_notebook(txt_mixin.txt_file_with_list):
    def __init__(self, filepath):
        self.pathin = filepath
        txt_mixin.txt_file_with_list.__init__(self, filepath)
        #self.raw_list = copy.copy(self.list)#<-- double RAM usage?

        
    def chop_header(self):
        assert self.list[0] == '{', 'problem with line 1'
        assert self.list[1] == ' "cells": [', 'problem with line 2'
        self.header = copy.copy(self.list[0:2])
        self.list[0:2] = []


    def chop_metadata(self):
        meta_inds = self.findall(' "metadata":',forcestart=1)
        assert len(meta_inds) == 1, "problem with finding metadata: %s" % \
                                     meta_inds
        meta_ind = meta_inds[0]
        line_before = self.list[meta_ind-1]
        assert line_before == " ],", "problem with line before metadata"
        self.tail = copy.copy(self.list[meta_ind-1:])
        self.list[meta_ind-1:] = []


    def break_into_cells(self):
        """Assuming chop_header and chop_metadata have already been called,
           self.list should just contain the lines associated with the
           cells and each cell should start with two spaces and then a
           {.  Additionally, each cell should end with two spaces and a
           } and all but the last cell should have a comma after the }.
        """
        # Assume that two spaces and an open or close curly brace
        # marks the start and end of every cell
        start_inds = self.findall('  {', forcestart=1)
        end_inds = self.findall('  }', forcestart=1)
        assert len(start_inds) == len(end_inds), \
            "problem matching starting and ending curly braces"
        cells = []
        for start, end in zip(start_inds, end_inds):
            curlines = copy.copy(self.list[start:end+1])
            curcell = nb_cell(curlines)
            cells.append(curcell)
        self.cells = cells


    def is_header(self, cell_ind, max_level=None, debug=False):
        """A header cell is a markdown cell whose source starts with spaces, a
        quotation mark, any number of # and then a space."""
        curcell = self.cells[cell_ind]
        if curcell.celltype != 'markdown':
            return False
        elif len(curcell.source) == 0:
            return False
        else:
            line0 = curcell.source[0]
            q = title_p.search(line0)
            if q is not None:
                #print("title = %s" % q.group(1))
                if max_level is not None:
                    match_level = find_header_level(line0)
                    if debug:
                        print("max_level = %s, match_level = %s" % (max_level, match_level))
                    if match_level > max_level:
                        return False
                    else:
                        return True
                else:
                    return True
            else:
                return False


    def get_title(self, cell_ind, raw=False):
        """Use regexp to get the title without the #'s unless raw=True"""
        header_cell = self.cells[cell_ind]
        if raw:
            return header_cell.source[0]
        else:
            q = title_p.search(header_cell.source[0])
            title = q.group(1).strip()
            if title[-1] == '"':
                title = title[0:-1]
            return title

    
    def find_next_header_cell(self, start_ind=0, max_level=None):
        N = len(self.cells)
        for i in range(start_ind, N):
            if self.is_header(i, max_level=max_level):
                return i


    def find_document_header(self):
        """If the first cell is a level one header, it is assumed to
        contain the document title."""
        ind = self.find_next_header_cell(start_ind=0, max_level=1)
        if ind < 3:
            return self.get_title(ind)
        else:
            return None

            
    def find_next_header_cell_matching_title(self, start_ind=0, title_list=None, \
                                             max_level=5):
        if title_list is None:
            title_list = ['Notes', 'Hide', 'Skip', 'Solution','notes']
        N = len(self.cells)
        for i in range(start_ind,N):
            h_cell = self.find_next_header_cell(start_ind,max_level=max_level)
            if h_cell is None:
                # there are no more header cells
                return None
            else:
                title = self.get_title(h_cell)
                for s in title_list:
                    if title.find(s) == 0:
                        # we found a header cell with a title in the list
                        return h_cell
                # the title for this header cell didn't match the list,
                # find the next header cell
                start_ind = h_cell+1
        # If we get to this point, we did not find a match
        return None


    def find_notes_to_remove(self, max_level=5, debug=False):
        """Find markdown cells whose source first line of source contains #
           Notes, # Hide, or # Skip and then find the index of the
           next header cell, so that we can delete the notes 'section'
        """
        N = len(self.cells)
        start_ind = 0
        ind_pairs = []
        for i in range(N):
            next_header_ind = self.find_next_header_cell_matching_title(start_ind, \
                                                                        max_level=max_level)
            if next_header_ind is None:
                break
            else:
                # we found one, go to the next section heading
                if debug:
                    print("next_header_ind = %s" % next_header_ind)
                    print("title = %s" % self.get_title(next_header_ind, raw=True))
                match_level = find_header_level(self.get_title(next_header_ind, raw=True))
                stop_ind = self.find_next_header_cell(next_header_ind+1,max_level=match_level)
                ind_pairs.append([next_header_ind, stop_ind])
                if stop_ind is None:
                    break
                start_ind = stop_ind+1
                
        return ind_pairs


    def find_top_level_notes(self, debug=False):
        """Find # Notes or # note(s) with exactly one # (top level)
        and cut everything until the next # Slide # slide(s) or
        # end note"""
        ind_pairs = self.find_notes_to_remove(max_level=1)
        if debug:
            for ind1, ind2 in ind_pairs:
                title1 = self.get_title(ind1, raw=True)
                line1 = "start: %s, %s" % (ind1, title1)
                print(line1)
                if ind2:
                    title2 = self.get_title(ind2, raw=True)
                    line2 = "start: %s, %s" % (ind2, title2)
                else:
                    line2 = "(at end)"
                    print(line2)
        return ind_pairs


    def pop_notes(self, ind_pairs=None):
        if ind_pairs is None:
            ind_pairs = self.find_notes_to_remove()
        ind_pairs.reverse()# remove them from the end first so that we
                           # don't shift the indices
        for pair in ind_pairs:
            self.cells[pair[0]:pair[1]] = []



    def pop_top_level_notes(self):
        ind_pairs = self.find_top_level_notes()
        self.pop_notes(ind_pairs)


    def pop_top_level_end_section_titles(self):
        """In order to accomidate top level notes to keep things out
        of slides, I needed to implement # End Notes and # Slides and
        stuff.  Those top level sections need to be removed before a
        notebook is ready for slides or sharing with students."""
        N = len(self.cells)
        start_ind = 0
        inds = []
        mylist = ['Slides','slides','End Notes','End Note','end notes','slide','slides']
        for i in range(N):
            next_header_ind = self.find_next_header_cell_matching_title(start_ind, \
                                                                        title_list=mylist, \
                                                                        max_level=1)
            if next_header_ind:
                inds.append(next_header_ind)
                start_ind = next_header_ind+1
            else:
                break
            
        inds.reverse()
        for ind in inds:
            self.cells.pop(ind)

            
        
    def cut_after_stop_here(self):
        """Find # Stop Here and cut everything after it."""
        ind = self.find_next_header_cell_matching_title(title_list=['Stop Here','stop here'])
        if ind:
            self.cells[ind:] = []
        

    def is_hidden_python(self, cell_ind):
        curcell = self.cells[cell_ind]
        if curcell.celltype != 'code':
            return False
        elif not curcell.source:
            # empty code cell where source = []
            return False
        else:
            line0 = curcell.source[0]
            q = hide_py_p.search(line0)
            if q is None:
                return False
            else:
                return True


    def find_python_cells_to_hide(self):
        cell_list = []
        N = len(self.cells)
        for i in range(N):
            if self.is_hidden_python(i):
                cell_list.append(i)
        return cell_list
    

    def pop_hidden_python(self):
        inds_to_remove = self.find_python_cells_to_hide()
        inds_to_remove.reverse()
        for ind in inds_to_remove:
            self.cells.pop(ind)
        

    def reassemble(self):
        linesout = self.header

        # the last cell cannot end with }, or the notebook is not JSON
        last_cell = self.cells[-1]
        assert last_cell.lines[-1].find('  }') == 0, "problem with last line of last cell"
        last_cell.lines[-1] = '  }'
        
        for curcell in self.cells:
            linesout.extend(curcell.lines)

        linesout += self.tail
        self.linesout = linesout


    def save(self, pathout):
        self.reassemble()
        txt_mixin.dump(pathout, self.linesout)
        

    def main(self):
        self.chop_header()
        self.chop_metadata()
        self.break_into_cells()
        


class jupyter_notebook_title_popper(jupyter_notebook):
    def pop_title_header(self):
        """If the first cell is a level one header, it is assumed to
        contain the document title."""
        ind = self.find_next_header_cell(start_ind=0, max_level=1)
        if ind < 3:
            self.cells.pop(ind)

    
    def save(self, pathout):
        self.pop_title_header()
        self.reassemble()
        txt_mixin.dump(pathout, self.linesout)


class jupyter_notebook_slide_maker(jupyter_notebook_title_popper):
    def process_only_cells(self, searchtitle, func):
        """Find any cell whose title starts with searchtitle and call func, passing
        in the cell index as the only input to func."""
        #print("in pop_onlynotes_cells")
        start_ind = 0
        N = len(self.cells)
        for i in range(start_ind,N):
            h_cell = self.find_next_header_cell(start_ind)#,max_level=4)
            #print("h_cell = %s" % h_cell)
            if h_cell is None:
                # there are no more header cells
                return None
            else:
                title = self.get_title(h_cell)
                title = title.strip()
                if title.find(searchtitle) == 0:
                    #we found one, pop it
                    #print("found one")
                    func(h_cell)
                else:
                    #print("non-matching title: %s" % title)
                    # the title for this header cell didn't match onlynotes,
                    # find the next header cell
                    start_ind = h_cell+1
        # If we get to this point, we did not find a match
        return None


    def process_one_onlynotes_cell(self, cell_ind):
        self.cells.pop(cell_ind)


    def process_onlynotes_cells(self):
        self.process_only_cells("onlynotes", self.process_one_onlynotes_cell)


    def process_only_slide_removing_just_only_line(self, cell_ind, onlytitle):
        """For slides, a cell that starts with ### onlyslides should
        have that first line removed.  Similarly for a notes document
        and ### onlynotes"""
        # Steps:
        # - remove the onlynotes line
        # - remove any blank lines at the start after
        #   we remove the onlynotes line
        mycell = self.cells[cell_ind]
        mycell.find_source()
        #src = copy.copy(mycell.source)
        src = mycell.source
        assert src[0].find(onlytitle) > -1, "%s not in first line" % onlytitle
        src.pop(0)
        for i in range(100):
            line0 = src[0]
            line0 = line0.replace('\\n','\n')
            if line0[-2:] == '",':
                line0 = line0[0:-2]
            line0 = line0.replace('"','')
            line0 = line0.strip()
            #print("line0: %s" % line0)
            if not line0:
                src.pop(0)
            else:
                break
            
        #mycell.source = src
        #self.cells[cell_ind] = mycell
        #print("src out = %s" % mycell.source)
        #print("!"*20)
        mycell.replace_source(src)
        #print("lines = %s" % mycell.lines)        


    def process_one_onlyslides_cell(self, cell_ind):
        self.process_only_slide_removing_just_only_line(cell_ind, "onlyslides")


    def process_onlyslides_cells(self):
        self.process_only_cells("onlyslides", self.process_one_onlyslides_cell)
        
    
    def main(self):
        jupyter_notebook.main(self)
        self.process_onlynotes_cells()
        self.process_onlyslides_cells()
        

class jupyter_notebook_student_notebook_maker(jupyter_notebook_slide_maker):
    def process_one_onlynotes_cell(self, cell_ind):
        self.process_only_slide_removing_just_only_line(cell_ind, "onlynotes")


    def process_one_onlyslides_cell(self, cell_ind):
        self.cells.pop(cell_ind)


    
class wsq_question_extracter(jupyter_notebook):
    """A class for processing WSQ feedback jupyter notebooks.  Keep
    only stuff related to questions and question feedback

    Find a heading.  If the head doesn't start with Question, pop
    until the next header.  Repeat."""
    def main(self):
        self.chop_header()
        self.chop_metadata()
        self.break_into_cells()
        self.pop_non_question_sections()


    def pop_non_question_sections(self):
        N = len(self.cells)
        start_ind = 0
        for i in range(start_ind,N):
            h_cell_ind = self.find_next_header_cell(start_ind)
            if h_cell_ind is None:
                # there are no more header cells
                return None
            h_cell_ind_2 = self.find_next_header_cell(h_cell_ind+1)
            title = self.get_title(h_cell_ind)
            if title.find("Question") != 0:
                # we found stuff to delete
                self.cells[h_cell_ind:h_cell_ind_2] = []
                # start_ind remains unchanged in this situation, I think
            else:
                # we wound a question and need to skip to the next header
                start_ind = h_cell_ind + 1

    
    def save(self):
        fno, ext = os.path.splitext(self.pathin)
        self.pathout = fno + "_questions.ipynb"
        self.reassemble()
        txt_mixin.dump(self.pathout, self.linesout)


student_name_p = re.compile("Student [0-9]+: *(.*)")

team_p = re.compile("Team [0-9]+: *(.*)")


# email list path for 445_SS20
#curdir = os.getcwd()
#if "/mnt/chromeos" in curdir:
#    grades_folder = '/mnt/chromeos/GoogleDrive/MyDrive/Teaching/445_SS20/grades'
#else:
#    grades_folder = "/Users/kraussry/Google Drive/Teaching/445_SS20/grades"
root = rwkos.get_root("345")
grades_folder = os.path.join(root, "grades")

bb_name = 'bb_email_list.csv'
bb_path = os.path.join(grades_folder, bb_name)
bb_list = txt_database.txt_database_from_file(bb_path)


def get_lname_fname_and_uid_for_student(student_name):
    #fname, lname = student_name.split(" ",1)
    name_list = student_name.split(" ")
    fname = name_list[0]
    lname = name_list[-1]
    fname = fname.strip()
    lname = lname.strip()
    myind = -1
    #case insenstive lastname search
    for i, test in enumerate(bb_list.Last_Name):
        lsearch = lname.lower()
        ltest = test.lower()
        if ltest.find(lsearch) == 0:
            myind = i
            break
    if myind == -1:
        msg = "problem with last name: %s" % lname
        raise(ValueError, msg)
    #myind = bb_list.get_ind(lname,"Last Name")
    student = bb_list[myind]
    user_id = student.Username
    return lname, fname, user_id


def get_email_and_fname_for_student(student_name):
    lname, fname, user_id = get_lname_fname_and_uid_for_student(student_name)
    email = user_id + "@mail.gvsu.edu"
    return fname, email


class wsq_grade_emailer(wsq_question_extracter):
    def find_next_student(self, start_ind):
        """The grading jupyter notebooks have '# Student 1: Name' as
        the top level headings.  So, the section for one student will
        start with a level one header that matches the regexp
        student_name_p."""
        N = len(self.cells)
        for i in range(start_ind,N):
            h_cell = self.find_next_header_cell(start_ind,max_level=1)
            if h_cell is None:
                # there are no more header cells
                return None
            else:
                title = self.get_title(h_cell)
                title = title.strip()
                q_student = student_name_p.match(title)
                if q_student is not None:
                    # we found a level one header cell
                    # that matches the student header pattern
                    return h_cell
                # the title for this header cell didn't match the list,
                # find the next header cell
                start_ind = h_cell+1
        # If we get to this point, we did not find a match
        return None
        

    def get_level_one_or_two_header_that_starts_with(self, start_ind, \
                                                     starts_with="Summary Feedback"):
        """## Summary Feedback"""
        for i in range(10):
            h_cell = self.find_next_header_cell(start_ind,max_level=2)
            title = self.get_title(h_cell)
            if title.find(starts_with) == 0:
                # we found it
                return h_cell
            else:
                # move on to the next one
                start_ind = h_cell+1


    def get_source_text_from_cell(self, cell_ind):
        mycell = self.cells[cell_ind]
        mycell.find_source()
        clean_src_lines = [clean_one_line_of_src_text(item) for item in mycell.source]
        src_text = "\n".join(clean_src_lines) 
        return src_text


    def get_summary_feedback(self, start_ind):
        sum_ind = self.get_level_one_or_two_header_that_starts_with(start_ind, \
                                                                    "Summary Feedback")
        src = self.get_source_text_from_cell(sum_ind+1)
        return src


    def get_question_feedback(self, start_ind):
        sum_ind = self.get_level_one_or_two_header_that_starts_with(start_ind, \
                                                                    "Question Feedback")
        src = self.get_source_text_from_cell(sum_ind+1)
        return src


    def get_grade(self, start_ind):
        sum_ind = self.get_level_one_or_two_header_that_starts_with(start_ind, \
                                                                    "Grade")
        src = self.get_source_text_from_cell(sum_ind+1)
        return src

        
    def main_loop(self, video_num, subject_pat="WSQ feedback for video %i"):
        import gmail_smtp
    
        self.chop_header()
        self.chop_metadata()
        self.break_into_cells()

        start_ind = 0
        N = len(self.cells)

        #Pdb().set_trace()
        subject = subject_pat % video_num
        for i in range(start_ind, N):
            student_start = self.find_next_student(start_ind)
            if student_start is None:
                return
            else:
                start_ind = student_start + 1
                student_header = self.get_title(student_start)
                print("%i:, %s" % (student_start, student_header))
                #Pdb().set_trace()
                #if student_start > 140:
                #    pdb.set_trace()
                sum_fb = self.get_summary_feedback(start_ind)
                q_fb = self.get_question_feedback(start_ind)
                grade = self.get_grade(start_ind)
                body_pat = "## %s\n\n%s\n\n" * 3
                body = body_pat % ("Summary Feedback", sum_fb, \
                                   "Question Feedback", q_fb, \
                                   "Grade", grade)

                q_student = student_name_p.search(student_header)
                full_name = q_student.group(1)
                fname, email = get_email_and_fname_for_student(full_name)

                intro = "%s,\n\nHere is your feedback for the WSQ for video %i:\n\n" % \
                        (fname, video_num)

                if video_num == 0:
                    intro += "Note that the WSQ for video 0 is practice and the grade does not actually count.  This feedback is to help you understand my expectations and get a better grade on future WSQs.\n\n"
                print("email: %s" % email)
                body = intro+body
                print("body:\n")
                print(body)
                print("="*20)
                gmail_smtp.send_mail_gvsu([email],subject, body)

                # at this point, I need a first name, an email, and the video #
                # to send the feedback
                # - ideally, I would also save the grades into a csv file to upload to BB
                


class wsq_grades_to_csv_converter(wsq_grade_emailer):
    def main_loop(self, video_num, csv_pat="wsq_grades_for_video_%0.3i.csv"):
        self.chop_header()
        self.chop_metadata()
        self.break_into_cells()

        start_ind = 0
        N = len(self.cells)
        rows = []
        
        #Pdb().set_trace()
        for i in range(start_ind, N):
            student_start = self.find_next_student(start_ind)
            if student_start is None:
                break
            else:
                start_ind = student_start + 1
                student_header = self.get_title(student_start)
                print("%i:, %s" % (student_start, student_header))
                #Pdb().set_trace()
                sum_fb = self.get_summary_feedback(start_ind)
                q_fb = self.get_question_feedback(start_ind)
                grade = self.get_grade(start_ind)
                q_student = student_name_p.search(student_header)
                full_name = q_student.group(1)
                lname, fname, uid = get_lname_fname_and_uid_for_student(full_name)
                if len(grade) > 2:
                    msg = "likely problem with grade: vid num: %i, %s, %s" % (video_num, full_name, grade)
                    print(msg)
                    raise ValueError(msg)
                currow = [lname, fname, uid, grade]#, sum_fb, q_fb]
                rows.append(currow)
                  # at this point, I need a first name, an email, and the video #
                # to send the feedback
                # - ideally, I would also save the grades into a csv file to upload to BB

        outname = csv_pat % video_num
        print("outname = %s" % outname)
        mylabels = ['last name','first name','user id','grade']#,'summary feedback','question feedback']
        txt_mixin.dump_delimited(outname, rows, delim=',', fmt='%s', labels=mylabels)


def get_team_num(header_line):
    part1, part2 = header_line.split(':',1)
    part1 = part1.replace("Team ","")
    part1 = part1.strip()
    return int(part1)


class lab_notebook_grade_extractor(wsq_grade_emailer):
    def find_next_team(self, start_ind):
        """The grading jupyter notebooks have '# Team 1: Madison and Ciana' as
        the top level headings.  So, the section for one team will
        start with a level one header that matches the regexp
        team_p."""
        N = len(self.cells)
        for i in range(start_ind,N):
            h_cell = self.find_next_header_cell(start_ind,max_level=1)
            if h_cell is None:
                # there are no more header cells
                return None
            else:
                title = self.get_title(h_cell)
                title = title.strip()
                q_team = team_p.match(title)
                if q_team is not None:
                    # we found a level one header cell
                    # that matches the student header pattern
                    return h_cell
                # the title for this header cell didn't match the list,
                # find the next header cell
                start_ind = h_cell+1
        # If we get to this point, we did not find a match
        return None


    def main_loop(self, lab_num):
        csv_pat="lab_%0.2i_grades_out.csv"
        self.chop_header()
        self.chop_metadata()
        self.break_into_cells()

        start_ind = 0
        N = len(self.cells)
        rows = []

        #Pdb().set_trace()
        for i in range(start_ind, N):
            team_start = self.find_next_team(start_ind)
            if team_start is None:
                break
            else:
                start_ind = team_start + 1
                team_header = self.get_title(team_start)
                print("%i:, %s" % (team_start, team_header))
                #Pdb().set_trace()
                #sum_fb = self.get_summary_feedback(start_ind)
                #q_fb = self.get_question_feedback(start_ind)
                #grade = self.get_grade(start_ind)
                q_team = team_p.search(team_header)
                team_names = q_team.group(1)
                team_num = get_team_num(team_header)
                ###########################################
                #
                # Start here: #<---------------------
                #
                ###########################################
                # To do:
                # - get team #
                # - extract feedback
                # - extract memo and comp Q grades
                currow = [team_num,team_names]#, sum_fb, q_fb]
                rows.append(currow)
                    # at this point, I need a first name, an email, and the lab #
                # to send the feedback
                # - ideally, I would also save the grades into a csv file to upload to BB

        outname = csv_pat % lab_num
        print("outname = %s" % outname)
        #mylabels = ['last name','first name','user id','grade']#,'summary feedback','question feedback']
        txt_mixin.dump_delimited(outname, rows, delim=',', fmt='%s')#, labels=mylabels)
    
    

class rsq_email_feedback(wsq_grade_emailer):
    def main_loop(self, subject, intro_line_1):
        import gmail_smtp

        self.chop_header()
        self.chop_metadata()
        self.break_into_cells()

        start_ind = 0
        N = len(self.cells)

        for i in range(start_ind, N):
            student_start = self.find_next_student(start_ind)
            if student_start is None:
                return
            else:
                start_ind = student_start + 1
                student_header = self.get_title(student_start)
                print("%i:, %s" % (student_start, student_header))
                #Pdb().set_trace()
                sum_fb = self.get_summary_feedback(start_ind)
                q_fb = self.get_question_feedback(start_ind)
                grade = self.get_grade(start_ind)
                body_pat = "## %s\n\n%s\n\n" * 3
                body = body_pat % ("Summary Feedback", sum_fb, \
                                   "Question Feedback", q_fb, \
                                   "Grade", grade)

                q_student = student_name_p.search(student_header)
                full_name = q_student.group(1)
                fname, email = get_email_and_fname_for_student(full_name)

                intro = "%s,\n\n%s:\n\n" % \
                        (fname, intro_line_1)
                print("email: %s" % email)
                body = intro+body
                print("body:\n")
                print(body)
                print("="*20)
                gmail_smtp.send_mail_gvsu([email],subject, body)

                ### at this point, I need a first name, an email, and the video #
                ### to send the feedback
                ### - ideally, I would also save the grades into a csv file to upload to BB

    
