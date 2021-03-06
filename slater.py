# -*- coding: utf-8 -*-
"""
Sample entry:

<div2 id="cross*)agaqwni/das" orig_id="n15" key="*)agaqwni/das" opt="n">
  <head extent="full" lang="greek" opt="n" orth_orig="^αγᾰθωνίδας">Ἀγαθωνίδας</head>
  a favourite of Pindar, Wil., Kl. Sch. 4. 181.
  <quote lang="greek">ὄφρα σὺν Χειμάρῳ</quote>
  <quote lang="greek">μεθύων Ἀγαθωνίδᾳ βάλω κότταβον</quote> (Wil.:
  <quote lang="greek">Ἀγάθωνι δὲ</quote> codd.: i. e.
  <sense id="n15.0" n="1" level="1" opt="n">
    <gloss>in honour of Agathonidas</gloss>) fr. 128. 2.
  </sense>
</div2>
"""
import re
from glob import glob

name = 'SlaterPindar'
type = 'greek'
caps = 'precapped'
convert_xml = True

def toSUP(l):
        return '<sup>%s</sup>' % l.group(1)

def toSUB(l):
        return '<sub>%s</sub>' % l.group(1)

# regex patterns
find_head = re.compile('<head(.)*?</head>')
clean_head = re.compile('<head(.)*?>|</head>|[\[\]]')
find_entry = re.compile('<div2')
end_entry = re.compile('</div2>')
find_orth = re.compile('orth_orig="([^"]+)"')

# Main method
def parse(dico_path, log, log_error):
    dico_data = sorted(glob(dico_path+'/pindar_dico*'))
    dico = []
    errors_occurred = False
    
    content = ''
    begin = False
    for xmlfile in dico_data:
        for line in open(xmlfile):
            if find_entry.search(line):
                begin = True
                headword = find_head.search(line).group(0)
                orth_orig = find_orth.search(headword)
                if orth_orig: orth_orig = orth_orig.group(1)
                else: orth_orig = headword
                content += line
            elif begin:
                content += line
        
            if end_entry.search(line):
                try:
                    headword = clean_head.sub('', headword)
                    headword = re.sub('<[^<]+>', '', headword)    
                    content = content.strip('\n')
                    content = re.sub('\^\{(.+?)\}', toSUP, content) 
                    content = re.sub('=\{(.+?)\}', toSUB, content) 
                    headword = headword.split(';')
                    for head in headword:
                        head = head.split(',')
                        if '' in head:
                            head.remove('')
                        for each in head: # Splits along commas, but ditches endings
                            if not '-' in each and each.strip() not in ('τό','ὁ'):
                                if not re.search('ς ', each):
                                    each = re.sub('[\']?[ ][\]]?', '', each , re.U) 
                                attrs = {'head': each.strip(), 'content': content.strip(), 'orth_orig': orth_orig}
                                dico.append(attrs)
                except(Exception) as e:
                    log_error("%s couldn't parse line \"%s\"...: %s" \
                        % (xmlfile.split('/')[-1], content[:50], e))
                    errors_occurred = True 
                
                (headword, content) = ('', '')
                begin = False
                
        log('%s finished parsing' % xmlfile.split('/')[-1])

    return dico, errors_occurred
