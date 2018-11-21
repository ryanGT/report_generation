import txt_mixin
#from IPython.core.debugger import Pdb
import os, copy
import basic_file_ops
import re

title_p = re.compile('^ +"#+ (.*)')
hide_py_p = re.compile('^ +"# *hide')

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


    def is_header(self, cell_ind):
        """A header cell is a markdown cell whose source starts with spaces, a
        quotation mark, any number of # and then a space."""
        curcell = self.cells[cell_ind]
        if curcell.celltype != 'markdown':
            return False
        else:
            line0 = curcell.source[0]
            q = title_p.search(line0)
            if q is not None:
                return True
            else:
                return False


    def get_title(self, cell_ind):
        header_cell = self.cells[cell_ind]
        q = title_p.search(header_cell.source[0])
        title = q.group(1).strip()
        return title

    
    def find_next_header_cell(self, start_ind=0):
        N = len(self.cells)
        for i in range(start_ind, N):
            if self.is_header(i):
                return i

            
    def find_next_header_cell_matching_title(self, start_ind=0, title_list=None):
        if title_list is None:
            title_list = ['Notes', 'Hide', 'Skip']
        N = len(self.cells)
        for i in range(start_ind,N):
            h_cell = self.find_next_header_cell(start_ind)
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


    def find_notes_to_remove(self):
        """Find markdown cells whose source first line of source contains #
           Notes, # Hide, or # Skip and then find the index of the
           next header cell, so that we can delete the notes 'section'
        """
        N = len(self.cells)
        start_ind = 0
        ind_pairs = []
        for i in range(N):
            next_header_ind = self.find_next_header_cell_matching_title(start_ind)
            if next_header_ind is None:
                break
            else:
                # we found one, go to the next section heading
                stop_ind = self.find_next_header_cell(next_header_ind+1)
                ind_pairs.append([next_header_ind, stop_ind])
                if stop_ind is None:
                    break
                start_ind = stop_ind+1
                
        return ind_pairs


    def pop_notes(self):
        ind_pairs = self.find_notes_to_remove()
        ind_pairs.reverse()# remove them from the end first so that we
                           # don't shift the indices
        for pair in ind_pairs:
            self.cells[pair[0]:pair[1]] = []


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
        
