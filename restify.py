from docutils import core
from docutils.writers.html4css1 import Writer,HTMLTranslator

import pdb

class NoHeaderHTMLTranslator0(HTMLTranslator):
    def __init__(self, document):
        HTMLTranslator.__init__(self,document)
        self.head_prefix = ['','','','','']
        self.body_prefix = []
        self.body_suffix = []
        self.stylesheet = []
        self.html_prolog = []
        self.head = []
        self.meta = []
        #pdb.set_trace()
        #self.__dict__


class NoHeaderHTMLTranslator(HTMLTranslator):
    def astext(self):
        print('called NoHeaderHTMLTranslator.astext')
        #pdb.set_trace()
        return ''.join(self.body)


class MyHTMLTranslator(HTMLTranslator):
    def __init__(self, document):
        HTMLTranslator.__init__(self,document)
        #pdb.set_trace()
        #print('old self.stylesheet='+self.stylesheet)
        self.stylesheet = ['<link rel="stylesheet" href="%%CSS_REL_PATH%%" type="text/css" />\n']
        navbarlist = ['<div id="sidebar">\n','<p>This is where<br>\n','the sidebar goes</p>\n','</div>\n']
        self.body_prefix.append('<div id="content">\n')
        mytail = ['</div>\n'] + navbarlist
        self.body_suffix[0:0] = mytail

##     def astext(self):
##         print('called MyHTMLTranslator.astext')
##         csslist = ['<link rel="stylesheet" href="%%CSS_REL_PATH%%" type="text/css" />\n']
##         navbarlist = ['<div id="sidebar">\n','<p>This is where<br>\n','the sidebar goes</p>\n','</div>\n']
##         mylist = self.head_prefix+self.head+csslist+self.body_prefix + \
##                  ['<div id="content">\n'] + self.body_pre_docinfo + self.body + \
##                  ['</div>\n'] + navbarlist + self.body_suffix
##         return ''.join(mylist)


class my_Writer(Writer):
    def translate(self):
        self.visitor = visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        for attr in self.visitor_attributes:
            #cur_attr = getattr(visitor, attr)
            #print(attr + '=' + str(cur_attr))
            setattr(self, attr, getattr(visitor, attr))
        #pdb.set_trace()
        self.output = self.apply_template()
        self.output = ''.join(self.body)
        #here is the template:
        #u'%(head_prefix)s\n%(head)s\n%(stylesheet)s\n%(body_prefix)s\n%(body_pre_docinfo)s\n%(docinfo)s\n%(body)s\n%(body_suffix)s\n'
        
_w = Writer()
_w.translator_class = MyHTMLTranslator#NoHeaderHTMLTranslator

_w2 = Writer()
_w2.translator_class = NoHeaderHTMLTranslator

_w0 = my_Writer()
_w0.translator_class = NoHeaderHTMLTranslator0




def reSTify(string):
    return core.publish_string(string,writer=_w)



#def reSTify_part(string):
#    return core.publish_string(string,writer=_w2)


def reSTify_part(string):
    return core.publish_string(string,writer=_w0)



def mytest():
    f = open('test_pieces.html','w')
    f.writelines(_w.head_prefix)
    f.writelines(_w.head)
    f.write('<link rel="stylesheet" href="main_blog_style.css" type="text/css" />\n')
    f.writelines(_w.body_prefix)
    f.write('<div id="content">\n')
    f.writelines(_w.body_pre_docinfo)
    f.writelines(_w.body)
    f.write('</div>\n')
    navbar = """<div id="sidebar">
<p>This is where<br>
the sidebar goes</p>
</div>
"""
    f.write(navbar)
    f.writelines(_w.body_suffix)
    f.close()
    

if __name__ == '__main__':
    test = """
Test example of reST__ document.

__ http://docutils.sf.net/rst.html

- item 1
- item 2
- item 3

"""
    test2 = """===========================
The Arrival of Joshua Ryan
===========================


Waiting
========

After waking up at 6 in the morning and getting to the hospital, we
had to wait a bit before Dr. Schaarf came and started the inducing
process.  This is a picture of us in the last few hours before Joshua
arrived and before things really got going/crazy.

.. picture path: 

.. figure:: pics/img_0277.jpg

    Ryan and Missy waiting for Missy to be induced.


Who knew that such a peaceful start would end like this:

.. figure:: pics/IMG_0293.JPG
   
    Joshua shortly after he arrived out in the world.


"""
    #print('reSTify')
    #print('=='*5)
    #print reSTify(test2)

    #print('\n'*3)
    #print('reSTify_part')
    #print('=='*5)
    #print reSTify_part(test2)
    #mytest()
    #test_out = reSTify(test2)
    #f2 = open('test_pieces2.html','w')
    #f2.write(test_out)
    #f2.close()

    navtest = """`Jan <../Jan/Jan_23_2008.html>`_

`Jul <../Jul/Jul_23_2008.html>`_

`Aug <Aug_31_2008.html>`_


- `31 <Aug_31_2008.html>`_

`Sep <../Sep/Sep_27_2008.html>`_

`Dec <../Dec/Dec_25_2008.html>`_"""

    print reSTify_part(navtest)

    #print('\n'*3)
    #print reSTify_part0(navtest)
 
