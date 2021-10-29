# -*- coding: utf-8 -*-
"""
Sample entry:
  <div xml:id="canon-cunliffe-lex" type="textpart" n="κανών">
    <head><foreign xml:lang="greek">κανών</foreign></head>
    <p><foreign xml:lang="greek">-όνος</foreign>, <foreign xml:lang="greek">ὁ</foreign>.</p>

    <p><term>Dat. pl.</term> <cit><quote xml:lang="greek">κανόνεσσι</quote> <bibl n="Hom. Il. 13.407">Il. 13.407</bibl></cit>.</p>
    <div xml:id="canon-cunliffe-lex-1" type="textpart">
      <head>1</head>
      <p>App., <gloss>each of two picces set inside a shield to keep it in shape, one running from top to bottom and the other placed horizontally, the middle protion of the latter forming a handle</gloss>: <cit><quote xml:lang="greek">[ἀσπίδα] δύω κανόνεσσʼ ἀραρυῖαν</quote> <bibl n="Hom. Il. 13.407">Il. 13.407</bibl></cit>. Cf. <bibl n="Hom. Od. 8.193">Od. 8.193</bibl>.</p>
    </div>

    <div xml:id="canon-cunliffe-lex-2" type="textpart">
      <head>2</head>
      <p><gloss>In weaving, app., each of two horizontal roods to which the lower ends of the threads of the warp</gloss> (<foreign xml:lang="greek">μίτος</foreign>) were attached, the even threads to one and the odd to the other <bibl n="Hom. Il. 23.761">Il. 23.761</bibl>.</p>
    </div>
  </div>
"""
import re
from glob import glob

name = 'Cunliffe'
type = 'greek'
caps = 'source'
convert_xml = True

def toSUP(l):
        return '<sup>%s</sup>' % l.group(1)

def toSUB(l):
        return '<sub>%s</sub>' % l.group(1)

# regex patterns
find_head = re.compile('<head>(\+ )?<foreign xml:lang="greek">(.*?)</foreign>[,.)]?(<hi rend="sup">.*?</hi>)? ?(<ref>.</ref>)?(, e\)cere/omai\.)?(\.-1?2?\.?)?</head>')
clean_head = re.compile('<head>|<foreign xml:lang="greek">|</foreign>|</head>|[\[\]]')
count_head = re.compile('</foreign>')
first_head = re.compile('(?<=<foreign xml:lang="greek">).*?(?=</foreign>)')
# find_def finds both main def and sub defs
find_def = re.compile('<div')
end_def = re.compile('</div>')



def parse(dico_path, log, log_error):
    dico_data = sorted(glob(dico_path+'/cunliffe*'))
# use the three lines below and the last two lines of the file if you want to run the script by itself
# def parse():
#     dico_path = ''
#     dico_data = sorted(glob('cunliffe_dico/parse.*'))
    
    dico = []
    errors_occurred = False
    
    content = ''
    headword = ''
    for xmlfile in dico_data:
        # def_level refers to how many more </def> we expect
        def_level = 0
        for i, line in enumerate(open(xmlfile)):
            if find_def.search(line):
                def_level += 1
                content += line
            elif find_head.search(line):
                headword = find_head.search(line).group(0)
                if def_level > 1:
                    content += '\n'
                content += line


            elif end_def.search(line) and def_level > 0:
                def_level -= 1
                content += line

                # Finished entry, so cleanup begins
                if def_level == 0:
                    if len(count_head.findall(headword)) > 1:
                        orth_orig = clean_head.sub('', headword)
                        headword = first_head.findall(headword)[0]
                    else:
                        headword = clean_head.sub('', headword)
                        orth_orig = headword
                
                    if 'hi rend' in headword:
                        headword = re.sub('<hi rend="sup">', '', headword)
                        headword = re.sub('</hi>', '', headword)
                        orth_orig = re.sub('<hi rend="sup">', '', orth_orig)
                        orth_orig = re.sub('</hi>', '', orth_orig)

                    if 'ref' in headword:
                        headword = re.sub('<ref>', '', headword)
                        headword = re.sub('</ref>', '', headword)
                        orth_orig = re.sub('<ref>', '', orth_orig)
                        orth_orig = re.sub('</ref>', '', orth_orig)
                    
                    headword = re.sub('(-|[0-9]|[,.\*†\+]) ?', '', headword)
                    
                    # fixes an issue with ναιετάω
                    #if headword == 'nαιετάω':
                      #  headword = re.sub('n', 'ν', headword)
                        #orth_orig = re.sub('n', 'ν', orth_orig)
                    
                    # fixes ἐξερέω issue
                    #if headword == 'ἐξερέωe)cere/omai':
                      #  headword = re.sub('e\)cere/omai', '', headword)
                        #orth_orig = re.sub('(, )?e\)cere/omai', '', orth_orig)
                    
                    # removes any final extra , and . at end of orth_orig for some lemmas
                    orth_orig = re.sub('[,.] ?$', '', orth_orig)
                    
                    # fixes καρτύνω
                    #if headword == 'καρτύνω':
                    #    orth_orig = re.sub('\+ ', '†', orth_orig)
                      #  content = re.sub('\+ καρτύνω', '†καρτύνω', content)

                    # basic formatting of entry - comment out these three lines if you don't want formatting. Small Roman numerals also occur. i can be 9 at level 3 or #1 at level 2.. so I put parentheses around the lower level ones.
                    content = re.sub('<head>([A-Z]|II|III|IV|V|VI)</head>', '<sense n="\g<1>" level="1" opt="n"></sense>', content)
                    content = re.sub('<head>([0-9]+?)</head>', '<sense n="\g<1>" level="2" opt="n"></sense>', content)
                    content = re.sub('<head>([a-z])</head>', '<sense n="\g<1>" level="3" opt="n"></sense>', content)
                    content = re.sub('<head>([α-ω]|\(i\)|\(ii\)|\(iii\)|\(iv\))</head>', '<sense n="\g<1>" level="4"  opt="n"></sense>', content)
                    
                    # this prevents apostrophes from breaking the entry
                    content = re.sub("'", "’", content)

                    content = re.sub('\n', '', content)
                    attrs = {'head': headword, 'content': content, 'orth_orig': headword}
                    content = ''
                    headword = ''
                    orth_orig = ''
                    dico.append(attrs)
            elif def_level > 0:
                content += line
            continue

    return dico, errors_occurred

# if __name__ == "__main__":
#     parse()
