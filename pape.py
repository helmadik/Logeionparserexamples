# -*- coding: utf-8 -*-
"""
Sample data:


"""

#import codecs
#import unicodedata
import re
from bs4 import BeautifulSoup

name = 'Pape'
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

	entry = entry.replace('\u0027', '\u02bc')

	return entry

def toBold(l):
	return ' <b>%s</b> ' % l.group(1)

def toPCA(l):
	return ' <span style="font-variant: small-caps;">%s</span> ' % l.group(1)

def toItalic(l):
	return '<i>%s</i> ' % l.group(1)

def parse(dico_path, log, log_error):
	datafile = dico_path+'/Pape-4.6a.txt'
	dico = []
	entry = ""
	head = ""
	orth_orig = ""
	head_orig = ""
	errors_occurred = False
	begin_reading = False

	with open(datafile) as infh:
		for line in infh:

			try:

				line = removeDumbGreekLetters(line).rstrip()

				entry = re.sub(r'<div2><head>.+?</head>(.+?)</div2>', r"\1", line)
				head_orig = re.sub(r'<div2><head>(.+?)</head>.+$', r"\1", line)

				# get rid of whitespace at the beginning of the entry
				entry = re.sub('^. *?', ', ', entry)

				# clean up the head
				head = head_orig
				head = re.sub(r' *– *', "-", head)

				#clean up situations like εἴτε – εἴτε
				head = re.sub(r'(.+?)\-\1', r"\1", head)
				head = re.sub(r'(.+?) [¹²³⁴⁵]', r"\1", head)

				entry = "<b>" + head_orig + "</b>" + entry
		
				# clean up the entry
				entry = re.sub(r'<font color="darkgreen">(.+?)</font>', toBold, entry)
				entry = re.sub(r'<font color="red">(.+?)</font>', toItalic, entry)
				entry = re.sub(r'<font color="green">(.+?)</font>', toPCA, entry)
				entry = re.sub(r'<font color="blue">(.+?)</font>', r"\1", entry)
				entry = re.sub(r'<font color="darkblue">(.+?)</font>', r"\1", entry)
				entry = re.sub(r'<font color="brown">(.+?)</font>', r"\1", entry)
				entry = re.sub(r'<font color="darkorange">(.+?)</font>', toItalic, entry)

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

			except(Exception) as e:
				log_error("%s couldn't parse line \"%s\"...: %s" \
					% (datafile.split('/')[-1],line, e))
				errors_occurred = True

	log('%s finished parsing' % datafile.split('/')[-1])
	return dico, errors_occurred
