import txt_mixin
#from IPython.core.debugger import Pdb
import os, copy
import basic_file_ops
import re

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


class nb_cell(object):
    def find_source(self):
        start_ind = self.lines.find('   "source": [')
        if "[]" in self.lines[start_ind]:
            self.source = []
        else:
            assert self.lines[-2] == '   ]'
            self.source = self.lines[start_ind+1:-2]
        self.start_ind = start_ind


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
           {.  Additionally, each cel should end with two spaces and a
           } and all but the last cel should have a comma after the }.
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
        if ind == 0:
            return self.get_title(0)
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
        
