import re, copy, os, sys, StringIO,traceback

import txt_mixin
#reload(txt_mixin)
from rwkmisc import rwkstr
import pylab_util as PU
from pyp_basics import line, section
from pytexutils import break_at_pipes, OptionsDictFromList

from IPython.core.debugger import Pdb
import pdb

def CountCurlies(strin):
    mystr = rwkstr(strin)
    numleft = len(mystr.findall('{'))
    numright = len(mystr.findall('}'))
    return numleft, numright


import var_to_latex as VL


#This is code from texpy that I don't completely remember the purpose
#of:
def BalanceCurlies(strin):
    outstr = ''
    rest = strin
    ind = len(rest)
    cont = True
    while ind != -1 and cont:
        ind = rest.find('}')
        if ind > -1:
            outstr += rest[0:ind]
            rest = rest[ind+1:]
            no, nc = CountCurlies(outstr)
            if no == nc:
                cont = False
                return outstr
            else:
                outstr += '}'
        else:
            outstr += rest
    return outstr


class env_popper(object):
    """This class will be used to grab environments delimited by {}
    out of lists.  These environments may span multiple lines of the
    input list."""
    def __init__(self, listin, map_in=None, preface='^'):
        self.list = txt_mixin.txt_list(listin)
        self.map = map_in
        self.keys = self.map.keys()
        self.keystr = '|'.join(self.keys)
        self.preface = preface
        self.pat = self.preface+'('+self.keystr+'){'
        self.p = re.compile(self.pat)
        self.lines = copy.copy(listin)
        self.ind = 0



    def search_vect(self, listname='lines', start=0, pstr='p'):
        p = getattr(self, pstr)
        myvect = getattr(self, listname)
        for n, line in enumerate(myvect[start:]):
            q = p.search(line)
            if q:
                return start+n
        return None



    def FindNextEnv(self, listname='lines', pstr='p'):
        """Find the next line matching self.p (the re.compile-ed
        version of self.pat), starting at line self.ind.

        The listname variable allows using this method on various
        lists within self, i.e. for texmaxima I need one list that
        doesn't get modified and one that does, so I have a
        self.rawlist and self.lines (or something like that)."""
        next_ind = self.search_vect(listname=listname, start=self.ind, \
                                    pstr=pstr)
        if next_ind is not None:
            self.matchline = next_ind
            self.ind = self.matchline+1
            return self.matchline
        else:
            return None
##         p = getattr(self, pstr)
##         myvect = getattr(self, listname)
##         for n, line in enumerate(myvect[self.ind:]):
##             q = p.search(line)
##             if q:
##                 self.matchline = self.ind+n
##                 self.ind = self.matchline+1#setup for next search, you
##                                            #may not want this +1 if
##                                            #the match gets removed and
##                                            #replaced with nothing.
##                 return self.matchline
##         return None#no match is left if we got this far


    def FindEndofEnv(self, matchline=None, listname='lines'):
        myvect = getattr(self, listname)
        if matchline is None:
            matchline = self.matchline
        n = -1
        match = False
        numleft = 0
        numright = 0
        while (not match) and (n < len(self.lines)):
            n += 1
            curline = rwkstr(myvect[matchline+n])
            numleft += len(curline.findall('{'))
            numright += len(curline.findall('}'))
            if numright >= numleft:
                match = True
        if match:
            self.endline = matchline+n
            return self.endline
        else:
            return None


    def PopEnv(self, startline=None, endline=None, clear=True, listname='lines'):
        myvect = getattr(self, listname)
        if startline is None:
            startline = self.matchline
        if endline is None:
            if self.endline is None:
                endline = self.endline
            else:
                endline = self.endline+1
        outlist = myvect[startline:endline]
##         if startline==endline:#make sure the {'s  and }'s are balanced
##             outstr = BalanceCurlies(outlist[0])
##             outlist = [outstr]
        if clear:
            myvect[startline:endline] = []
        return outlist


    def PopNext(self, clear=True, listname='lines'):
        if self.FindNextEnv(listname=listname) is not None:#sets self.matchline
            self.FindEndofEnv(listname=listname)#sets self.endline
            outlist = self.PopEnv(clear=clear, listname=listname)
            if clear:
                self.ind = self.matchline#r      return outlist
                return outlist
        else:
            return None


    def _CleanChunk(self, chunk):
        """Extract the Python code from \pyenv{  }"""
        mystr = '\n'.join(chunk)
        #find periods with only one space after them
        p = re.compile(r'\. ([A-Z])')
        mystr = p.sub(r'.  \1',mystr)

        p2 = re.compile(self.pat+'(.*)}', re.DOTALL)
        q2 = p2.search(mystr)
        code = q2.group(2)
        code = BalanceCurlies(code)
        nl, nr = CountCurlies(code)
        assert nl==nr, "Number of left and right curly braces not equal:"+code
        envkey = q2.group(1)
        #codelist = code.split('\n')
        return envkey, code


class simple_popper(env_popper):
    def __init__(self, listin, start_re):
        self.list = txt_mixin.txt_list(listin)
        self.start_re = start_re
        self.p_start = re.compile(self.start_re)
        self.ind = 0

    def PopNext(self, clear=False):
        if self.FindNextEnv() is not None:#sets self.matchline
            self.FindEndofEnv()#sets self.endline
            outlist = self.PopEnv(clear=clear)
            if clear:
                self.ind = self.matchline#r      return outlist
            return outlist
        else:
            return None

    def PopEnv(self, startline=None, endline=None, clear=False):
        if startline is None:
            startline = self.matchline
        if endline is None:
            if self.endline is not None:
                endline = self.endline+1
        outlist = self.list[startline:endline]
        if clear:
            myvect[startline:endline] = []
        return outlist

    def FindNextEnv(self):
        """Find the next line matching self.p_start (the re.compile-ed
        version of self.pat), starting at line self.ind."""
        next_ind = self.list.findnextre(self.p_start, ind=self.ind)
        if next_ind is not None:
            self.matchline = next_ind
            self.ind = self.matchline+1
            return self.matchline
        else:
            return None

    def FindEndofEnv(self, matchline=None):
        if matchline is None:
            matchline = self.matchline
        n = -1
        match = False
        numleft = 0
        numright = 0
        while (not match) and (n < len(self.list)):
            n += 1
            curline = rwkstr(self.list[matchline+n])
            numleft += len(curline.findall('{'))
            numright += len(curline.findall('}'))
            if numright >= numleft:
                match = True
        if match:
            self.endline = matchline+n
            return self.endline
        else:
            return None


    def Execute(self):
        keepgoing = True
        n = 0
        self.nested_list = []
        while keepgoing and (n < len(self.list)):
            chunk = self.PopNext()
            if chunk:
                self.nested_list.append(chunk)
            else:
                keepgoing = False
            n += 1
        return self.nested_list


class pyp_figure(object):
    def __init__(self, string_in, objlist, level=1):
        self.rawstring = string_in
        self.objlist = objlist
        self.clean_string = self.rawstring.replace('\n',' ')
        self.list = break_at_pipes(self.clean_string)
        self.path = self.list.pop()
        self.options = {'center':True}
        self.level = level
        mydict, loners = OptionsDictFromList(self.list)
        self.options.update(mydict)
        self.caption = ''
        self.height = None
        self.width = None
        self.label = None
        assert len(loners) < 2, 'self.list has more than 1 unlabeled option'
        if len(loners) == 1:
            self.options['caption'] = loners[0]
            self.caption = loners[0]
        elif self.options.has_key('caption'):
            self.caption = self.options['caption']
        if not (self.options.has_key('width') or self.options.has_key('height')):
            #self.options['height']='0.9\\textheight'
            self.options['width']='0.9\\textwidth'
        self.center = self.options['center']
        map_list = ['height','width','label','placestr']
        for key in map_list:
            if self.options.has_key(key):
                setattr(self, key, self.options[key])


list_map = txt_mixin.default_map

class multicols(txt_mixin.txt_file_with_list):
    def clean_start(self, pat='[two|three|four]cols{(.*)'):
        obj0 = self.objlist[0]
        p = re.compile(pat)
        q = p.search(obj0.string)
        if q:
            self.objlist.pop(0)
            rest = q.group(1)
            if rest:
                line0 = line(rest)
                self.objlist.insert(0,line0)


    def clean_end(self, pat='(.*)}'):
        end_obj = self.objlist[-1]
        p = re.compile(pat)
        q = p.match(end_obj.string)
        if q:
            self.objlist.pop()
            start = q.group(1)
            rest = q.group(1)
            if rest:
                lastline = line(rest)
                self.objlist.append(lastline)


    def clean_list(self):
        while not self.list[0]:
            self.list.pop(0)
        while not self.list[-1]:
            self.list.pop()


    def __init__(self, string_in, objlist, widths=None, \
                 level=0, *args, **kwargs):
        txt_mixin.txt_file_with_list.__init__(self, pathin=None)
        self.level = level
        self.rawstring = string_in
        self.objlist = objlist
        self.clean_start()
        self.clean_end()
        mylist = self.rawstring.split('\n')
        self.list = txt_mixin.txt_list(mylist)
        self.clean_list()
        msg = 'self.objlist and self.list do not correspond.'
        assert len(self.list) == len(self.objlist), \
               msg +'\nlength mismatch'
        bool_list = []
        for obj, string in zip(self.objlist, self.list):
            cur_bool = obj.string == string
            if not cur_bool:
                raise StandardError, msg + '\n' + 'Problem items:' + \
                      str(obj) +'!=' +string
        self.widths = widths
        for item in list_map:
            cur_func = getattr(self.list, item)
            setattr(self, item, cur_func)#map functions from self.list


    def break_up_cols(self):
        self.inds = self.findallre('^[-=]+$')
        self.col_objs = []
        prev_ind = 0
        for ind in self.inds:
            cur_slice = self.objlist[prev_ind:ind]
            self.col_objs.append(cur_slice)
            prev_ind = ind+1
        cur_slice = self.objlist[prev_ind:]
        self.col_objs.append(cur_slice)


    def parse_cols(self):
        if not hasattr(self, 'col_objs'):
            self.break_up_cols()
        self.cols = []
        for cur_slice in self.col_objs:
            cur_col = column(cur_slice)
            self.cols.append(cur_col)


class twocols(multicols):
    def __init__(self, string_in, objlist, widths=None, \
                 *args, **kwargs):
        #print('string_in='+str(string_in))
        if widths is None:
            widths = ['0.45\\textwidth']*2
        multicols.__init__(self, string_in, objlist, widths=widths)
        self.break_up_cols()
        self.parse_cols()


class column(object):
    def __init__(self, objlist):
        self.objlist_in = objlist
        #self.clean_start()
        self.env_popper = pyp_env_popper(self.objlist_in)
        self.env_popper.Execute()
        self.objlist = self.env_popper.objlist


class pyp_eqn(object):
    def __init__(self, string_in, objlist, level=0):
        self.rawline = string_in
        if string_in.find('|'):
            env, rest = string_in.split('|',1)
            self.env = env
            self.eqn = rest.lstrip()
        else:
            self.eqn = string_in
            self.env = 'equation'
        self.objlist = objlist
        self.level = level



class pyp_code(object):
    def __init__(self, string_in, objlist, level=0):
        self.code = string_in
        self.rawline = string_in
        self.objlist = objlist
        self.lines = self.code.split('\n')
        self.level = level


class pyp_link(object):
    def __init__(self, string_in, objlist, level=0):
        self.link = string_in
        self.rawline = objlist[0].rawline
        self.objlist = objlist
        self.level = level



pyp_def_map = {'fig':pyp_figure, 'twocols':twocols, \
               'eqn':pyp_eqn,'code':pyp_code, 'link':pyp_link}


class pyp_env_popper(env_popper):
    """The trick with trying to use env_popper with pyp parsing is
    that the input lists are composed of raw strings, but line
    instances.  So, pyp_env_popper will create a separate list of the
    strings of the input list of lines and try and work with those two
    separate lists, one mainly for searching, the other for one we are
    really trying to work with."""
    def __init__(self, listin, map_in=None, preface='', def_level=1):
        if map_in is None:
            map_in = pyp_def_map
        env_popper.__init__(self, listin, map_in, preface=preface)
        self.objlist = copy.copy(self.list)
        self.def_level = def_level
        self.lines = [item.string for item in self.list]


    def PopEnv(self, startline=None, endline=None, clear=True, \
               listname='objlist', clearnames=['lines']):#'objlist']):
        myvect = getattr(self, listname)
        if startline is None:
            startline = self.matchline
        if endline is None:
            endline = self.endline+1
        outlist = myvect[startline:endline]
        if clear:
            myvect[startline:endline] = []
            for curname in clearnames:
                curvect = getattr(self, curname)
                curvect[startline:endline] = []
        return outlist


    def Chunk_from_Objlist(self, objlist):
        chunk = [item.string for item in objlist]
        return chunk


    def PopNext(self, clear=True, list1name='lines', \
                list2name='objlist'):
        if self.FindNextEnv(listname=list1name) is not None:#sets self.matchline
            self.FindEndofEnv(listname=list1name)#sets self.endline
            outlist = self.PopEnv(clear=clear, listname=list2name, \
                                  clearnames=[list1name])
            if clear:
                self.ind = self.matchline#r      return outlist
                return outlist
        else:
            return None


    def Execute(self):
        keepgoing = True
        n = 0
        while keepgoing and (n < len(self.list)):
            obj_chunk = self.PopNext()
            if obj_chunk:
                chunk = self.Chunk_from_Objlist(obj_chunk)
                envkey, code = self._CleanChunk(chunk)
                #print('envkey='+str(envkey))
                curclass = self.map[envkey]
                cur_object = curclass(code, obj_chunk, \
                                      level=self.def_level)
                self.objlist[self.matchline:self.matchline] = [cur_object]
                self.lines[self.matchline:self.matchline] = ['!!!space holder!!!']
            else:
                keepgoing = False
            n += 1
        return self.objlist

class python_report_env(object):
    def __init__(self, listin):
        self.list = txt_mixin.txt_list(listin)
        self.code = '\n'.join(self.list)


    def Execute(self, namespace, **kwargs):
        self.namespace = namespace
        try:
            exec self.code in namespace
        except:
            for i,l in enumerate(self.code.split('\n')):
                print '%s: %s'%(i+1,l)
            traceback.print_exc(file=sys.stdout)
            sys.exit(0)

    def To_PYP(self, **kwargs):
        raise NotImplementedError


class py_figure(python_report_env):
    """A pyfig environment is a chunk of code that generates a figure.
    The figure should be ready to be saved by the end of the block,
    i.e. all formatting is done and it looks pretty.

    The caption and filename should be specified at the beginning of
    the block in a line that starts with a # and has a colon after the
    work caption of filename like so:

    #pyfig
    #caption:This is my caption.
    #filename:filename.png

    multi-line captions are o.k.: the caption is assumed to end on
    either the line with #filename: in it or the next non-commented
    line."""
    def Execute(self, namespace, figfolder='figs',\
                def_ext='.png', dpi=100, **kwargs):
        if not os.path.exists(figfolder):
            os.mkdir(figfolder)
        python_report_env.Execute(self, namespace=namespace, **kwargs)
        keys = ['caption','filename','label']
        mypat = '^#('+'|'.join(keys)+')'
        comments = [item for item in self.list if item.find('#')==0]
        if comments[0].find('#pyfig') == 0:
            comments.pop(0)
        com_list = txt_mixin.txt_list(comments)
        start_inds = com_list.findallre(mypat)
        end_inds = start_inds[1:]+[None]
        pat2 = '^#('+'|'.join(keys)+')'+':(.*)'
        p2 = re.compile(pat2)
        keysfound = []
        for si, ei in zip(start_inds, end_inds):
            chunk = ''.join(com_list[si:ei])
            q2 = p2.match(chunk)
            if q2:
                key = q2.group(1)
                body = q2.group(2)
                body = body.replace('#',' ')
                setattr(self, key, body)
                keysfound.append(key)
        assert 'filename' in keysfound, "#filename: was not found in " + \
               self.code +'\n'*2+ \
               'NOTE: it must be in the beginning comments.'
        fno, ext = os.path.splitext(self.filename)
        if not ext:
            ext = def_ext
        self.nameout = fno+ext
        self.pathout = os.path.join(figfolder, self.nameout)
        PU.mysave(self.pathout, dpi=dpi)


    def To_PYP(self, echo=False, **kwargs):
        outlist = []
        if echo:
            outlist.append('code{')
            for line in self.list:
                if line and line[0] != '#':
                    outlist.append(line)
            outlist.append('}')
        pyp_out_str = 'fig{'
        if hasattr(self, 'caption'):
            if self.caption:
                pyp_out_str += 'caption:'+self.caption+'|'
        if hasattr(self, 'label'):
            if self.label:
                pyp_out_str += 'label:'+self.label+'|'
        pyp_out_str += self.pathout+'}'
        outlist.append(pyp_out_str)
        return outlist


def find_lhs(line):
    """Find the left hand side (lhs) of an assignment statement,
    checking to make sure that the equals sign is not inside the
    arguement of a function call."""
    ind = line.find('=')
    ind2 = line.find('(')
    if ind == -1:
        return None
    elif ind2 > -1:
        #there is both an equal sign and a (
        if ind < ind2:
            #the equal sign is first and there is an lhs
            #out = myfunc(b=5)#<-- the lhs here is "out"
            return line[0:ind]
        else:
            #the ( is first as in
            #myfunc(1, b=2)#<-- note that there is no assignment here
            return None
    else:
        #there is an equal sign, but no (
        return line[0:ind]


ignore_list = ['!','-','=']

class py_body(python_report_env):
    def To_PYP(self, usetex=False, echo=False, **kwargs):
        pyp_out = []
        self.lhslist = []
        if self.list[0].find('#pybody') == 0:
            self.list.pop(0)
        for line in self.list:
            if not line:
                pyp_out.append('')
            elif line[0] == '#':
                #lines like #! or #---- or #==== are caught here and
                #dropped - they will not be echoed.
                if line[1] not in ignore_list:
                    pyp_out.append(line[1:])
            else:
                lhs = find_lhs(line)
                if echo:
                    pyp_out.append('code{'+line+'}')
                if lhs and lhs.find('print')==-1:
                    myvar = eval(lhs, self.namespace)
                    if usetex:
                        outlines, env = VL.VariableToLatex(myvar, lhs,**kwargs)
                        if len(outlines) == 1:
                            eqnlines = ['eqn{'+env+'|'+outlines[0]+'}']
                        else:
                            eqnlines = ['eqn{'+env+'|']+outlines+['}']
                        pyp_out.extend(eqnlines)
                    else:
                        pyp_out.append('%s = %s' % (lhs, myvar))
                    self.lhslist.append(lhs)
        return pyp_out



class py_no(python_report_env):
    def To_PYP(self, **kwargs):
        return []



py_def_map = {'fig':py_figure, 'body':py_body,'no':py_no}


class python_report_popper(env_popper):
    """This class exists to make it easier to create journal entries
    or other reports directly from commented python files.  The python
    file must include things like #pyno, #pybody and #pyfig to tell
    the popper how to chop up the file.  The chopping up will not
    include curly braces so that the end of one environment will be
    marked by the start of the next."""
    def __init__(self, listin, map_in=None, preface='^#py', show=False):
        if map_in is None:
            map_in = py_def_map
        if not show:
            listin = [item for item in listin if \
                      item.find('show(') != 0]
        env_popper.__init__(self, listin, map_in, preface)
        self.pat = '^#(?!\!)'#match any comment sign that isn't
                             #followed by a !.  If it doesn't match a
                             #known env, it will default to pybody
        self.p = re.compile(self.pat)
        self.pat2 = self.preface+'('+self.keystr+')'
        self.p2 = re.compile(self.pat2)
        self.first = True


    def FindNextEnv(self):
        """Find the next line matching self.p (the re.compile-ed
        version of self.pat), starting at line self.ind."""
        if self.first:
            self.matchline = 0
            self.ind = self.matchline+1
            self.first = 0
            return self.matchline
        else:
            next_ind = self.list.findnextre(self.p, ind=self.ind)
            if next_ind is not None:
                self.matchline = next_ind
                self.ind = self.matchline+1
                return self.matchline
            else:
                return None


    def FindEndofEnv(self, matchline=None):
        #this needs to handle pyfig env's better now that pat just
        #looks for # without a !
        if matchline is None:
            matchline = self.matchline
        line0 = self.list[matchline]
        envkey = self._Get_Env_Key(line0)
        if envkey == 'fig':
            #pdb.set_trace()
            self.ind = self.list.find_next_non_comment(start_ind=self.ind)
        end_ind = self.list.findnextre(self.p, ind=self.ind)
        if end_ind:
            end_ind = end_ind-1
        self.endline = end_ind
        return end_ind


    def PopEnv(self, startline=None, endline=None, clear=False):
        if startline is None:
            startline = self.matchline
        if endline is None:
            if self.endline is not None:
                endline = self.endline+1
        outlist = self.list[startline:endline]
        if clear:
            myvect[startline:endline] = []
        return outlist


    def PopNext(self, clear=False):
        if self.FindNextEnv() is not None:#sets self.matchline
            self.FindEndofEnv()#sets self.endline
            outlist = self.PopEnv(clear=clear)
            if clear:
                self.ind = self.matchline#r      return outlist
            return outlist
        else:
            return None


    def _Get_Env_Key(self, line0):
        """Extract the Python code from env"""
        #line0 = chunk[0]
        #code = '\n'.join(chunk)
        q2 = self.p2.match(line0)
        if q2:
            envkey = q2.group(1)
        else:
            envkey = 'body'
        #codelist = code.split('\n')
        return envkey#, code


    def Execute(self):
        keepgoing = True
        n = 0
        self.objlist = []
        while keepgoing and (n < len(self.list)):
            chunk = self.PopNext()
            if chunk:
                line0 = chunk[0]
                envkey = self._Get_Env_Key(line0)
                curclass = self.map[envkey]
                cur_object = curclass(chunk)
                self.objlist.append(cur_object)
            else:
                keepgoing = False
            n += 1
        return self.objlist


class reg_exp_popper(simple_popper, python_report_popper):
    """This class exists to make it easier to create journal entries
    or other reports directly from commented python files.  The python
    file must include things like #pyno, #pybody and #pyfig to tell
    the popper how to chop up the file.  The chopping up will not
    include curly braces so that the end of one environment will be
    marked by the start of the next."""
    def __init__(self, listin, start_re, end_re=None):
        simple_popper.__init__(self, listin, start_re)
        self.end_re = end_re
        self.p_end = re.compile(self.end_re)

    def FindEndofEnv(self, matchline=None):
        #this needs to handle pyfig env's better now that pat just
        #looks for # without a !
        if matchline is None:
            matchline = self.matchline
        end_ind = self.list.findnextre(self.p_end, ind=self.ind)
##         if end_ind:
##             end_ind = end_ind-1
        self.endline = end_ind
        return end_ind


def line_starts_with_non_white_space(linein):
    if linein is None:
        return False
    if linein == '':
        return False
    first_char = linein[0]
    ws_list = [' ','\t']#list of whitespace characters
    if first_char in ws_list:
        return False
    else:
        return True


class rst_popper(env_popper):
    """This is my quick and dirty attemp to convert a sage rst
    document to a file sage can load.  I will make some attempt to
    generalize it so that it could work with other rst documents."""
    def __init__(self, listin, preface='^'):#map_in=None
        self.list = txt_mixin.txt_list(listin)
        #self.map = map_in
        #self.keys = self.map.keys()
        #self.keystr = '|'.join(self.keys)
        self.preface = preface
        self.pat = self.preface + '\.\. (py|pyno)::'
        self.p = re.compile(self.pat)
        self.lines = copy.copy(listin)
        self.ind = 0
        self.pat2 = "^[ \t]+:label:"
        self.p2 = re.compile(self.pat2)
        self.pat_code = '^([ \t]+)'#for finding white_space
        self.pcode = re.compile(self.pat_code)



    def FindEndofEnv(self, matchline=None, listname='lines'):
        myvect = getattr(self, listname)
        if matchline is None:
            matchline = self.matchline
        n = -1

        N = len(myvect)
        i = matchline + 1

        while i < N-1:
            curline = myvect[i]
            if line_starts_with_non_white_space(curline):
                #print('curline[0]=' + curline[0] + '.')
                self.endline = i-1
                return self.endline
            else:
                i += 1
        #if the code makes it to here, the file ends on a .. py:: or
        #.. pyno:: environment
        self.endline = None
        return self.endline


    def _CleanChunk(self, chunk):
        first_line = chunk.pop(0)
        q = self.p.search(first_line)
        assert q is not None, "First line of chunk did not match pattern."
        line_two = chunk[0]#first line is already popped off
        q2 = self.p2.search(line_two)
        if q2 is not None:
            line_two = chunk.pop(0)#remove the label line

        while not chunk[0]:
            chunk.pop(0)#remove empty lines at the beginning

        while not chunk[-1]:
            chunk.pop()#remove empty lines at the end

        first_code_line = chunk[0]
        qcode = self.pcode.search(first_code_line)
        ws = qcode.group(0)
        self.pat_code2 = '^' + ws
        self.pcode2 = re.compile(self.pat_code2)

        lines_out = []

        for line in chunk:
            clean_line = self.pcode2.sub('',line)
            lines_out.append(clean_line)

        lines_out.append('')#one empty line per chunk
        return lines_out


    def Execute(self):
        keepgoing = True
        n = 0
        self.list_out = []
        #Pdb().set_trace()
        while keepgoing and (n < len(self.list)):
            chunk = self.PopNext()
            if chunk:
                clean_chunk = self._CleanChunk(chunk)
                self.list_out.extend(clean_chunk)
            else:
                keepgoing = False
            n += 1
        return self.list_out


    def save(self, outpath):
        txt_mixin.dump(outpath, self.list_out)


if __name__ == '__main__':
    filepath = '/home/ryan/siue/Research/DT_TMM/cantilever_beam/two_masses_analysis.rst'
    import txt_mixin
    myfile = txt_mixin.txt_file_with_list(filepath)
    mylist = myfile.list
    mypopper = rst_popper(mylist)
    mypopper.Execute()
    pne, ext = os.path.splitext(filepath)
    outpath = pne + '.sage'
    mypopper.save(outpath)


