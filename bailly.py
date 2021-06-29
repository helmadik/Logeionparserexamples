# -*- coding: utf-8 -*-
"""
Sample data:


"""

#import codecs
#import unicodedata
import re

name = 'Bailly2020'
type = 'greek'
caps = 'source'
convert_xml = False

def removeDumbGreekLetters(entry):
	entry = entry.replace('\u03D0', '\u03B2')
	entry = entry.replace('\u03D1', '\u03B8')
	entry = entry.replace('\u1F71', '\u03AC')
	entry = entry.replace('\u1F73', '\u03AD')
	entry = entry.replace('\u1F75', '\u03AE')
	entry = entry.replace('\u1F77', '\u03AF')
	entry = entry.replace('\u1F79', '\u03CC')
	entry = entry.replace('\u1F7B', '\u03CD')
	entry = entry.replace('\u1F7D', '\u03CE')
	entry = entry.replace('\u1FD3', '\u0390')
	entry = entry.replace('\u1FE3', '\u03B0')

	entry = entry.replace('\u1FE8', '\u1FB0\u0304')
	entry = entry.replace('\u1FE9', '\u1FD0\u0304')
	entry = entry.replace('\u200A', '\uE70A')
	entry = entry.replace('\u2039', '\uE1AA')
	entry = entry.replace('\u203A', '\uE1A9')
	entry = entry.replace('\u203B', '\uE1B3')
	entry = entry.replace('\u203C', '\uE1C3')
	entry = entry.replace('\u203D', '\u1FE0\u0304')
	entry = entry.replace('\u203E', '\u1FB3\u0304')
	entry = entry.replace('\u2200', '\u0370')
	entry = entry.replace('\u2263', '\u2E16')

	return entry

def toBold(l):
	return ' <b>%s</b> ' % l.group(1)

def toPCA(l):
	return ' <span style="font-variant: small-caps;">%s</span> ' % l.group(1)

def toSecBold(l):
#	return ' <p style="padding-left: 50px; text-indent: -15px"><b>%s</b>' % l.group(1)
	return ' <b>%s</b>' % l.group(1)

def toUP(l):
	return '<sup>%s</sup>' % l.group(1)

def toDIXPC(l):
	return '<span style="text-transform: uppercase;">%s</span>' % l.group(1)

def toOverline(l):
	return '<span style="text-decoration: overline;">%s</span>' % l.group(1)

#def toEntree(l):
#	return '<span style="display: inline-block; padding-left: 25px; text-indent: -15px;"><b>%s</b></span>' % l.group(1)

def toEntree(l):
	return '<b>%s</b>' % l.group(1)

def toEntreeStat(l):
	if l.group(2) == "17":
		return '<b>%s</b>' % (l.group(1))
	else:
		return '<b>%s <font color="green">(%s)</font></b>' % (l.group(1), l.group(2))

def toPPBold(l):
#	return ' <p style="padding-top: 10px; padding-left: 35px; text-indent: #-15px">&para; <b>%s</b>' % l.group(1)
#	return ' &para; <b>%s</b>' % l.group(1)
	return ' <b>%s</b>' % l.group(1)

def toRubBold(l):
	return '<br><p style="padding-top: 10px; display: inline-block; padding-left: 25px; text-indent: -15px;"><b>%s</b>' % l.group(1)

def toRubBold2(l):
	return '<br><p style="padding-top: 10px; display: inline-block; padding-left: 25px; text-indent: 0px;"><b>%s</b>' % l.group(1)

def toItalic_(l):
	return '<i>%s</i> ' % l.group(1)

def toItalic(l):
	return '<i>%s</i> ' % l.group(1)

def toSect(l):
	return '<br><p style="padding-top: 10px; display: inline-block; padding-left: 25px; text-indent: -15px;"><i>%s</i>' % l.group(1)

def toOrig(l):
	return '%s' % l.group(1)

def toFrenchOrth(l):
	return '%s&nbsp;%s%s' % (l.group(1), l.group(2), l.group(3))

def italNested(l):
	line = l.group(1)
	line = re.sub(r"\\ital", "", line)
	line = re.sub(r"[{}]", "", line)
#	return '%s%s%s' % ("\ital{", line, "}") 
	return '%s' % line 

def parse(dico_path, log, log_error):
#	datafile = dico_path+'/gaffiot-a-z-20160831.tex'
	datafile = dico_path+'/bailly-entier-20210110.tex'
#	datafile = dico_path+'/Gaffe.tex'	
	dico = []
	entry = ""
	head = ""
	orth_orig = ""
	head_orig = ""
	errors_occurred = False
	begin_reading = False

	with open(datafile) as infh:
		for line in infh:

#			try:
#				line = line.decode('latin1')
#			except(Exception), e:
#				line = line.decide('utf-8')
#
#			line = line.encode('utf-8')
#			line = line.replace('é', u"\u00E9".encode('utf-8'))

#			line = line.decode('utf-8', 'ignore').encode('utf-8')

			# line = "%s" % line.decode('utf-8', 'ignore')
			line = "%s" % line
#			line = line.replace("'","")

			try:
				if ("\sq" in line or "\endtriplecolumns" in line) and entry != "":

					entry = removeDumbGreekLetters(entry)

					# grab head
					#head = re.sub(r'^.*entree{[0-9 ]*[\?\*\-\( ]*(.+?)[,\) ]*}.*$', r"\1", entry.strip())
					head = re.sub(r'^.*entree{[0-9 ]*[\?\*\-\( ]*(.+?)[, ]*}.*$', r"\1", entry.strip())
					head = re.sub(r'\-.*?$', "", head) 
					head = re.sub(r'~', " ", head) 
					head = re.sub(r'[\(\)]', "", head) 
					head = head.replace('\u0387', '')
					head = removeDumbGreekLetters(head)
					head_orig = re.sub(r'^.*entree{(.+?)}.*$', r"\1", entry.strip())

					# replace ~ for nbsp
					entry = entry.replace('~', '&nbsp;')

					# fix percents
					entry = re.sub(r'\\%', "%", entry)

					# fixes for French orthography
					entry = re.sub(' ([;!:\?]+)(?![^<]*>|[^<>]*</)', r'&nbsp;\1', entry)
#					entry = entry.replace(u'\u0027', u'\u2019')
					entry = entry.replace('\u0027', '\u02bc')
					entry = entry.replace('---', '\u2014')
					entry = entry.replace('--', '\u2013')
					entry = entry.replace('\u0220', '\u23d1')

					#do some entry formatting of previous entry before saving to db

					entry = re.sub(r'\\entree{(.+?)}{([0-9]+)}', toEntreeStat, entry)
					entry = re.sub(r'\\entree{(.+?)}', toEntree, entry)
					entry = re.sub(r'\\qvoy{(.+?)}', r"[\1]", entry)
					entry = re.sub(r'\\gens{(.+?)}', toBold, entry)

##					entry = re.sub(r'\\S{}', '\u00a7', entry)
##					entry = re.sub(r'\\S([0-9].+?)', '\u00a7' + r" \1", entry)
##					entry = re.sub(r'\\\\S', '\u00a7', entry)
##					entry = re.sub(r'\\S\\', '\u00a7', entry)
##					entry = re.sub(r'\\S', '\u00a7', entry)
					entry = re.sub(r'\\thinspace ', '&nbsp;', entry)
					entry = re.sub(r'\$\\,\$\\', ' ', entry)
					entry = re.sub(r'\$\\,\$', '&nbsp;', entry)
					entry = re.sub(r'\$\\times\$', '*', entry)

					entry = re.sub(r'{\\neufrm(.*?)}', '\1', entry)
					entry = re.sub(r'\$\\overline{(.*?)}\$', toOverline, entry)
						
					entry = re.sub(r'\\lat{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\grec{(.+?)}', r"\1", entry)
##					entry = re.sub(r'\\grec{(.+?)}', r"</i>\1", entry)
					entry = re.sub(r'\\rom{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\allemand{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\anglais{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\arabe{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\armenien{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\copte{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\egypt{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\esp{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\fran{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\gotique{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\hebr{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\hittite{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\italien{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\lituan{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\myc{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\neerland{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\norrois{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\persan{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\phenicien{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\prakrit{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\protogrec{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\sscr{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\zend{(.+?)}', r"\1", entry)

					entry = re.sub(r'\\gram{(.+?)}', r"\1", entry)


					entry = re.sub(r'\\latc{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\latpl{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\latdim{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\latpf{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\latp{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\latgen{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\latv{(.+?)}', toItalic_, entry)

					entry = re.sub(r'\\hbox{(.+?)}', r"\1", entry)
#					entry = re.sub(r'\\hbox{(.+?)}', r"", entry)
					entry = re.sub(r'\\smash{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\sens{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\cfr{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\refp{(.+?)}{(.+?)}', r"<i>\1</i> \2", entry)
					entry = re.sub(r'\\bref{(.+?)}', r"</i>\1<i>", entry)

					entry = re.sub(r'\\desv{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\gen{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\oeuv{(.+?)}', toItalic, entry)
					entry = re.sub(r'oeuv{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\oeuva{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\refch{(.+?)}', toItalic_, entry)
					entry = re.sub(r'refch{(.+?)}', toItalic_, entry)
#					entry = re.sub(r'\\bref{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\des{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\el{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\refchp{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\freq{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\sect{(.+?)}', toSect, entry)
					entry = re.sub(r'\\Sect{(.+?)}', toSect, entry)

					entry = re.sub(r'\\kkz{(.+?)}', toSecBold, entry)
					entry = re.sub(r'\\qq{(.+?)}', toSecBold, entry)
					entry = re.sub(r'\\pp{(.+?)}', toPPBold, entry)
					entry = re.sub(r'\\qqng{(.+?)}', toSecBold, entry)
					entry = re.sub(r'\\rub{(.+?)}', toRubBold2, entry)
					entry = re.sub(r'\\Rub{(.+?)}', toRubBold, entry)
					entry = re.sub(r'\\es{(.+?)}', toBold, entry)
					entry = re.sub(r'\\grecgras{(.+?)}', toBold, entry)
					entry = re.sub(r'\\gras{(.+?)}', toBold, entry)

					entry = re.sub(r'\\pca{(.+?)}', toPCA, entry)
					entry = re.sub(r'\\pc{(.+?)}', toPCA, entry)
					entry = re.sub(r'\\up{(.+?)}', toUP, entry)
					entry = re.sub(r'\\upg{(.+?)}', toUP, entry)
					entry = re.sub(r'\\upr{(.+?)}', toUP, entry)
					entry = re.sub(r'{\\dixpc (.+?)}', toDIXPC, entry)
					entry = re.sub(r'{\\arabe (.+?)}', toDIXPC, entry)

					entry = re.sub(r'{\\dixrmchif (.+?)}', r"\1", entry)
					entry = re.sub(r'{\\douzerm (.+?)}', r"\1", entry)
					
					entry = re.sub(r'\\debutetymrev', r"", entry)
					entry = re.sub(r'\\finetymrev', r"", entry)
					entry = re.sub(r'\\smasc{}', r"(ὁ)", entry)
					entry = re.sub(r'\\smasc{}', r"(ὁ)", entry)
					entry = re.sub(r'\\smascpl{}', r"(οἱ)", entry)
					entry = re.sub(r'\\sfem{}', r"(ἡ)", entry)
					entry = re.sub(r'\\sfempl{}', r"(αἱ)", entry)
					entry = re.sub(r'\\sneutr{}', r"(τό)", entry)
					entry = re.sub(r'\\sneutrpl{}', r"(τά)", entry)
					entry = re.sub(r'\\smascfem{}', r"(ὁ, ἡ)", entry)

					entry = re.sub(r'\\par', r"<p>", entry)
					entry = re.sub(r'\\kern.*?em', r"", entry)
					entry = re.sub(r'\\%*raise.*?ex', r"", entry)
					entry = re.sub(r'\\%*raise.*?em', r"", entry)
					entry = re.sub(r'\\string', r"", entry)
					entry = re.sub(r'\\break', r"", entry)
					entry = re.sub(r'\\nobreak', r"", entry)
					entry = re.sub(r'\\unskip', r"", entry)
					entry = re.sub(r'\\unskipLampr', r"", entry)
					entry = re.sub(r'%*?\\endtriplecolumns', r"", entry)
					entry = re.sub(r'%*?\\begintriplecolumns', r"", entry)
					entry = re.sub(r'%*?\\vfill', r"", entry)
					entry = re.sub(r'%*?\\eject', r"", entry)
					entry = re.sub(r'%*?\\iffalse', r"", entry)
					entry = re.sub(r'\\penalty-10000', r"", entry)
					entry = re.sub(r'\\penalty-1000', r"", entry)
					entry = re.sub(r'\\penalty -10000', r"", entry)
					entry = re.sub(r'\\penalty -1000', r"", entry)
					entry = re.sub(r'\\penalty5000', r"", entry)
					entry = re.sub(r'\\hfil', r"", entry)
					entry = re.sub(r'\\goodbreak', r"", entry)
					entry = re.sub(r'\\hskip.*?em\\', r"", entry)

#					entry = re.sub(r'\\gras{(.+?)}', r"\1", entry)
#					entry = re.sub(r'\\gras{}', r"", entry)
#					entry = re.sub(r'\\gras', r"", entry)
					entry = re.sub("%http.*$", r"", entry)
					entry = re.sub(r'~\\%', '%', entry)
#					entry = re.sub(r'\\F', '<p style="padding-top: 10px; padding-left: 20px; text-indent: -15px">' + u'\u21a0', entry)
					entry = re.sub(r'\\F', '<p style="padding-top: 10px; padding-left: 20px; text-indent: -15px">' + '\u27b3', entry)

					entry = re.sub(r'\\autz{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\autp{(.+?)}', toPCA, entry)
					entry = re.sub(r'\\aut{(.+?)}', toPCA, entry)
					entry = re.sub(r'aut{(.+?)}', toPCA, entry)

					entry = re.sub(r'\\cl{(.+?)}', toItalic_, entry)
#					entry = re.sub(r'\\comm{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\comm{(.+?)}', r"", entry)
					entry = re.sub(r'\\etyml {(.+?)}', toItalic, entry)
					entry = re.sub(r'\\etyml{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\etymgr{(.+?)}', r"\1", entry)
					entry = re.sub(r'{\(', '(', entry)
					entry = re.sub(r'\)}', ')', entry)

					# is this the right way to clean up vowel length?
					entry = re.sub(r'e�]+?', r"", entry)

#					entry = re.sub(r'\\ital{(.+?\\ital{.+?}.+?)}', italNested, entry)
#					log(entry)
					entry = re.sub(r'\\ital{([^}]+?)}', toItalic, entry)
##					entry = re.sub(r'\\ital{(.+?)}', toItalic, entry)
					entry = re.sub(r'\\italp{(.+?)}', toItalic_, entry)
					entry = re.sub(r'\\ital\((.+?)}', toItalic_, entry)
					entry = re.sub(r'\\indoeurop{(.+?)}', r"\1", entry)
					entry = re.sub(r'\\etym{(.+?)}', r"\1", entry)

					entry = re.sub(r'%*\\imagepng.*?{.+?}{.+?}{.+?}', r'', entry)
					entry = re.sub(r'\\imagepng{.+?}{.+?}', r'', entry)
					entry = re.sub(r'\\anchor{.+?}', r'', entry)
					entry = re.sub(r'\\kkzx{.+?}', r'', entry)
					entry = re.sub(r'\\jumplink{.+?}{.+?}', r'', entry)
					entry = re.sub (r':([^ ])', r": \1", entry)
#					entry = re.sub(r'\\sq{.+?}{.+?}', r'', entry)

					entry = entry.replace(" .", ".")
					entry = entry.replace(",  ", ", ")
#					entry = entry.replace(" :", ": ")
#					entry = entry.replace(" ;", "; ")
					entry = entry.replace(":%", "")
#					entry = entry.replace("% ", "")
#					entry = entry.replace(" +", " ")
					entry = entry.replace("\\-", "")

					# entry = entry.encode('utf-8')

					if not orth_orig: orth_orig = head_orig
					attrs = {'head': head, 'content': entry, 'orth_orig': head_orig}
					dico.append(attrs)
					entry = ""
					
	
					# fix capitalization
					if len(head) > 1:
						if head[0].isupper() and head[1].isupper():
							log("Cap problem: %s" % head)
							head = head.lower().capitalize()
							head_orig = head_orig.lower().capitalize()
							log("fixed as: %s" % head)

				else:
					if not re.search('^%', line):

						#remove comments
						entry = re.sub(r'[^\\]%.*$', "", entry)
						entry = re.sub(r'^%.*$', "", entry)
						entry = re.sub(r'\\null\\vskip.*$', r"", entry)
						entry = re.sub(r'\\lettre.*$', r"", entry)
						entry = re.sub(r'\\vskip.*$', r"", entry)

						entry = entry + " " + line.strip()

			except(Exception) as e:
				log_error("%s couldn't parse line \"%s\"...: %s" \
					% (datafile.split('/')[-1],line, e))
				errors_occurred = True

	log('%s finished parsing' % datafile.split('/')[-1])
	return dico, errors_occurred
