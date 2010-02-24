import os, time, re, copy
import rwkmisc
#reload(rwkmisc)
from rwkmisc import reverse, isfloat, rwkstr, PrintToScreen

def FixOver(strin,displaystyle=True):
#    p=re.compile(r'{{(.*?)}\\over{(.*?)}}')
#    return p.sub(ReplaceOver,strin)
    strout=strin
    prevout=''
    while strout!=prevout:
        prevout=strout
        strout=FixOneOver(prevout,displaystyle)
    return strout


def FixOneOver(strin,displaystyle=True):
    strout=strin
    oi=strout.find('\\over')
    if oi>-1:
        leftpart=rwkstr(strout[0:oi-1])#the -1 is because the syntax will always be {{num}\\over{den}} and I don't want the } before \\over
        linds=leftpart.findall('{{')
        linds=reverse(linds)
        for ti in linds:
            tempnum=leftpart[ti+2:]
            if checkonebalance(tempnum)==0:
                break
        num=tempnum
        b4=leftpart[0:ti]
        si=oi+len('\\over')+1
        rightpart=rwkstr(strout[si:])
        rinds=rightpart.findall('}}')
        for ri in rinds:
            tempden=rightpart[0:ri]
            if checkonebalance(tempden)==0:
                break
        den=tempden
        afterpart=rightpart[len(den)+2:]
        strout=b4
        if displaystyle:
            strout+=' \\displaystyle '
        strout+='\\frac{'+num+'}{'+den+'}'+afterpart
    return strout

def checkonebalance(strin, openp='{',closep='}'):
    strin=rwkstr(strin)
    no=strin.findall(openp)
    nc=strin.findall(closep)
    return len(no)-len(nc)

def ReplaceOver(match):
    num=match.group(1)
    den=match.group(2)
    outstr='\\displaystyle \\frac{'+num+'}{'+den+'}'
    return outstr


def FixPmatrix(strin):#,locstr='c'):
    p=re.compile(r'\\pmatrix{(.*)}')
    out1 = p.sub(ReplacePmatrix,strin)
    out2 = ''
    while out1 != out2:
        out2 = out1
        out1 = p.sub(ReplacePmatrix, out1)
    return out1


def FixPmatrixBody(body, locstr='c'):
    line1,rest=body.split('\\cr',1)
    mylist=line1.split('&')
    nc=len(mylist)
    p1='\\left[ \\begin{array}{'+locstr*nc+'}'
    body=body.replace('\\cr','\\\\')
    endpart='\\end{array} \\right]'
    return p1+body+endpart


def ReplacePmatrix(match, locstr='c'):
    matstr=match.group(1)
    body, extra = FindBalancedString(matstr)
    if extra:
        extra+='}'#we lost the final closing '}' if there was extra stuff after balancing
    out = FixPmatrixBody(body, locstr=locstr)
    if extra:
        out += ' '+extra
    return out

def FindBalancedString(strin, openp='{',closep='}'):
    """This function seeks to find the argument to some argument by
    checking for balanced paranthesis.  For example, given the string
    \pmatrix{{\it x_2}\cr 0\cr 1\cr }=blah blah \pmatrix{blah2},
    correctly return that the argument to the first \pmatrix is
    {\it x_2}\cr 0\cr 1\cr

    The basic algorithm is to find the next closep and then check if
    the body has matching parantheses."""
    done = False
    N = len(strin)
    i=-1
    body = ''
    rest = strin
    while not done and i < N:
        i = rest.find(closep)
        if i < 0:
            i = N
        newbody = rest[0:i+1]
        body += newbody
        if checkonebalance(body) == -1:
            body=body[0:-1]#drop last closep
            done = True
        rest = rest[i+1:]
    return body, rest
