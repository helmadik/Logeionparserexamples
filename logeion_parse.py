#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#############################################################
# logeion_parse.py
# Parses text or xml files and inserts them into sqlite
# table for use by Logeion; see "Logeion_upload_instructions" 
# for details on parsers and dir structure.
#############################################################
import xml.parsers.expat
import sqlite3
import sys
import re
import logging
import unicodedata
import html.entities
import os.path
import inspect
import itertools
import collections

try:
    from parsers import *
except(Exception) as e:
    print('%s: error: import failed: %s' % (sys.argv[0], str(e)))
    sys.exit(-1)

class DicoInfo:
    all_dicos = {}
    latin = []
    greek = []
    sidebar = []
    uncapped = []
    cap_source = []
    convert_xml = []
    disabled = []
    max_dico_name_len = 0

    @classmethod
    def initialize(self):
        self.all_dicos = {}
        for module in sys.modules:
            if 'parsers.' in module:
                parser = sys.modules[module]
                try:
                    self.all_dicos[parser.name] = parser
                except(AttributeError):
                    pass
        self.latin = [d.name for d in list(self.all_dicos.values()) if d.type == 'latin']
        self.greek = [d.name for d in list(self.all_dicos.values()) if d.type == 'greek']
        self.sidebar = [d.name for d in list(self.all_dicos.values()) if d.type == 'sidebar']
        self.uncapped = [d.name for d in list(self.all_dicos.values()) if d.caps == 'uncapped']
        self.cap_source = [d.name for d in list(self.all_dicos.values()) if d.caps == 'source']
        self.convert_xml = [d.name for d in list(self.all_dicos.values()) \
                                   if hasattr(d, 'convert_xml') and d.convert_xml]
        self.disabled = [d.name for d in list(self.all_dicos.values()) \
                                if hasattr(d, 'enabled') and not d.enabled]
        max_len = 0
        for dico in itertools.chain(*[self.latin, self.greek, self.sidebar]):
            if len(dico) > max_len:
                max_len = len(dico)
        self.max_dico_name_len = max_len

DicoInfo.initialize()

# Some basic globals: usage string, Greek-to-Roman map, and entity-to-Unicode map

prog = sys.argv[0].split('/')[-1]
usage = """\
Usage: %s [options] [dico ...]
    --all           Parse all dictionaries.
    --latin         Parse Latin dictionaries and references (cumulative).
    --greek         Parse Greek dictionaries (cumulative).
    --sidebar       Parse textbooks (cumulative).
    --not <dicos>[,<dico>]*
                    Ignore given dicos when parsing (i.e. remove from set to be parsed).
    --db <db>       Use <db> as output database instead of './new_dvlg-wheel.sqlite'.
    --dico-root <root>
                    Folder containing the dictionary source folders; defaults to
                    ./dictionaries
    --help          Display this message and exit
    --modify        Do not delete entries if the target db already exists
                    (entries are deleted by default).
    --level <level> Log at level <level>; default is INFO. Case-insensitive.
                    Options: %s""" \
                    % (prog, str([f for f in dir(logging) 
                                    if f.isupper() and \
                                    type(logging.getLevelName(f)) is int and \
                                    logging.getLevelName(f) > 0]))

alpha_trans = {'α': 'a', 'β': 'b', 'γ': 'c', 'δ': 'd', 'ε': 'e', 
               'ϝ': 'f', 'ζ': 'g', 'η': 'h', 'θ': 'i', 'ι': 'j',
               'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'o',
               'ο': 'p', 'π': 'q', 'ϟ': 'r', 'ρ': 's', 'σ': 't',
               'τ': 'u', 'υ': 'v', 'φ': 'w', 'χ': 'x', 'ψ': 'y',
               'ω': 'z'}

other_entities = {
'&Amacron;': '\u0100'.encode('utf-8'), '&Emacron;': '\u0112'.encode('utf-8'),
'&Imacron;': '\u012a'.encode('utf-8'), '&Omacron;': '\u014c'.encode('utf-8'),
'&Scedil;': '\u015e'.encode('utf-8'),  '&T-vorm;': 'T',#unichr(0x1d413).encode('utf-8'),
'&Turkse-I;': '\u0130'.encode('utf-8'),'&Turkse-i;': '\u0131'.encode('utf-8'),
'&Umacron;': '\u016a'.encode('utf-8'), '&abreve;': '\u0103'.encode('utf-8'),
'&amacron;': '\u0101'.encode('utf-8'), '&breuk1-10;': '1/10',
'&breuk1-12;': '1/12',                  '&breuk1-2;': '\u00bd'.encode('utf-8'),
'&breuk1-200;': '1/200',                '&breuk1-24;': '1/24',
'&breuk1-3;': '\u2153'.encode('utf-8'),'&breuk1-4;': '\u00bc'.encode('utf-8'),
'&breuk1-6;': '\u2159'.encode('utf-8'),'&breuk1-72;': '1/72',
'&breuk1-8;': '\u215b'.encode('utf-8'),'&breuk1-96;': '1/96',
'&breuk3-4;': '\u00be'.encode('utf-8'),'&breuk5-12;': '5/12',
'&breuk7-12;': '7/12',                  '&breve;': '\u02d8'.encode('utf-8'),
'&c-mirror;': '\u0186'.encode('utf-8'),'&dice-5;': '\u2684'.encode('utf-8'),
'&eacute;': '\u00E9'.encode('utf-8'),
'&ebreve;': '\u0115'.encode('utf-8'),  '&ei;': 'ei',
'&emacron;': '\u0113'.encode('utf-8'), '&eu;': 'eu',
'&ghacek;': '\u01e7'.encode('utf-8'),  '&hk;': '\u2014'.encode('utf-8'),
'&imacron;': '\u012b'.encode('utf-8'), '&lquote;': '\u2018'.encode('utf-8'),
'&obreve;': '\u014f'.encode('utf-8'),  '&oe;': 'oe',
'&oi;': 'oi',                           '&omacron;': '\u014d'.encode('utf-8'),
'&perc;': '\u0025'.encode('utf-8'),    '&pijl;': '\u27a4'.encode('utf-8'),
'&poolse-l;': '\u0142'.encode('utf-8'),'&rquote;': '\u2019'.encode('utf-8'),
'&scedil;': '\u015f'.encode('utf-8'),  '&slash;': '\u002f'.encode('utf-8'),
'&ss;': '\u00df'.encode('utf-8'),      '&super1;': '\u00b9'.encode('utf-8'),
'&super2;': '\u00b2'.encode('utf-8'),  '&super3;': '\u00b3'.encode('utf-8'),
'&super4;': '\u2074'.encode('utf-8'),  '&super5;': '\u2075'.encode('utf-8'),
'&tcedil;': '\u0163'.encode('utf-8'),  '&umacron;': '\u016b'.encode('utf-8'),
'&wit;': ' ',                           '&yi;': 'yi',
'&ymacron;': '\u0233'.encode('utf-8')
}

#########################
#       FUNCTIONS       #
#########################

# StateManager and Functions for XML parsers

class StateManager:
    def __init__(self):
        self.closeSpan = False
        self.needsFirstUL = True
        self.content = ""
        self.currentLevel = 0

def did_start_element(name, attrs):
    if name == "sense":
        if sm.closeSpan:
             sm.content += "</span></li>" 
        sm.sl = int(attrs.setdefault("level", 0))
        if not sm.sl:
            sm.sl = 1
        sm.sense_n = attrs.setdefault("n", '0')
        if sm.sense_n == "0":
            sm.sense_n = "" 
        logging.debug('In: sm.currentLevel=%d, sm.sl=%d' % (sm.currentLevel, sm.sl))
        while sm.currentLevel < sm.sl:
            sm.needsFirstUL = False 
            if sm.currentLevel > 0:
                sm.content += "<li>"
            sm.content +="<ul>"
            sm.currentLevel+=1 
        logging.debug('Out: sm.currentLevel=%d, sm.sl=%d' % (sm.currentLevel, sm.sl))
        while sm.currentLevel > sm.sl:
            sm.content +="</ul>"
            if sm.currentLevel > 0:
                sm.content += "</li>"
            sm.currentLevel-=1
        if not sm.currentLevel == sm.sl:
            assert()
        sm.content +="<li><span class=\"bullet\">%s</span><span class=\"content\">" % sm.sense_n
        sm.closeSpan = True          
    elif name == "i":
        sm.content +="<i><b>"
    elif name == "gloss":
        sm.content +="<i><b>"
    elif name == "orth":
        sm.content +="<b>"
    elif name == "title":
        sm.content +="<i>"
    elif name == "author":
        sm.content +="<span style=\"font-variant: small-caps;\">"
    elif name == "sup":
        sm.content +="<sup>"
    elif name == "sub":
        sm.content +="<sub>"
    else:
         return

def did_end_element(name):
    if name == "i":
        sm.content +="</i></b>" 
    elif name == "gloss":
        sm.content +="</i></b>"
    elif name == "orth":
        sm.content +="</b>"
    elif name == "title":
        sm.content +="</i>"
    elif name == "head":
        sm.content += " "
    elif name == "author":
        sm.content += "</span>"
    elif name == "sup":
        sm.content +="</sup>"
    elif name == "sub":
        sm.content +="</sub>"

def did_find_char_data(data):
    sm.content += data

# Set up XML parser
#xml_parser = xml.parsers.expat.ParserCreate()
#xml_parser.StartElementHandler = did_start_element
#xml_parser.EndElementHandler = did_end_element
#xml_parser.CharacterDataHandler = did_find_char_data

def clean_one_entry(data):
    #assert isinstance(data, unicode)
    data = data.encode('utf-8')
    global sm
    sm = StateManager()
    try:
        xml_parser = xml.parsers.expat.ParserCreate()
        xml_parser.StartElementHandler = did_start_element
        xml_parser.EndElementHandler = did_end_element
        xml_parser.CharacterDataHandler = did_find_char_data
        xml_parser.Parse(data)
    except xml.parsers.expat.ExpatError as e:
        print('\n' + str(e), file=sys.stderr)
        print(data, file=sys.stderr)
        m = re.search('column ([0-9]+)', str(e))
        if m:
            print('...'+data[int(m.group(1)):], file=sys.stderr)
        sys.exit(1)
    if sm.closeSpan:
        sm.content += "</span></li>"
    while (sm.currentLevel):
        sm.content += "</ul>"
        if sm.currentLevel > 1:
            sm.content += "</li>"
        sm.currentLevel -= 1
    return sm.content

# Hammer XML so that it fits basic specifications, then clean
# and convert into rational HTML; does it for every dictionary
# except for DGE and DuCange
def clean_xml_and_convert(dico_parsed):
    for i in range(len(dico_parsed)):
        content = dico_parsed[i]['content']
        content = unescape(content)
        # logging.debug('Cleaning/converting entry ' + dico_parsed[i]['head'].decode('utf-8'))
        # logging.debug('Entry ' + dico_parsed[i]['head'].decode('utf-8') + ' has data:\n' + content)
        logging.debug('Cleaning/converting entry ' + dico_parsed[i]['head'])
        logging.debug('Entry ' + dico_parsed[i]['head'] + ' has data:\n' + content)
        if content is None:
            # logging.warning('content is None for entry ' + dico_parsed[i]['head'].decode('utf-8'))
            logging.warning('content is None for entry ' + dico_parsed[i]['head'])
        else:
            dico_parsed[i]['content'] = clean_one_entry(content).strip()
        logging.debug('Content coming out:\n' + dico_parsed[i]['content'])
    return dico_parsed

# Substitute out all entities for Unicode equivalents (except for those maintained
# by the HTML standard)
def unescape(read_in):
    if read_in is None: return None
    if type(read_in) is not str: read_in = read_in.decode('utf-8')
    all_entities = list(set(re.findall('&#?[\w\-0-9]+;', read_in)))
    hed_ent_names = list(html.entities.name2codepoint.keys())
    for e in all_entities:
        # First of these based on unescape() by Fredrik Lundh 
        # (http://effbot.org/zone/re-sub.html#unescape-html)
        if e in ('&lt;','&gt;','&amp;','&apos;','&quot;'):
            continue
        elif e[:2] == "&#":
            try:
                if e[:3] == "&#x":
                    replace_chr = chr(int(e[3:-1],16))
                else:
                    replace_chr = chr(int(e[2:-1]))
            except(ValueError):
                continue
        elif e[1:-1] in hed_ent_names:
            replace_chr = chr(html.entities.name2codepoint[e[1:-1]])
        else:
            # replace_chr = other_entities[e].decode('utf-8')
            replace_chr = other_entities[e]
        #read_in = re.sub(e.decode('utf-8'), replace_chr, read_in)
        read_in = re.sub(e, replace_chr, read_in)
    return read_in

# "Transliterates" the Greek headwords.  Roman letters are chosen by alphabetical order,
# purely for sorting
def translit(greek):
    roman = ''
    for char in removediacr(greek):
        if char not in list(alpha_trans.keys()):
            roman += char
        else:
            roman += alpha_trans[letter]
    print(roman, file=sys.stderr)
    return roman

def tolower(greek):
    # s = removediacr(greek).decode('utf-8')
    # return s.lower().encode('utf-8').replace('ϝ', '')
    s = removediacr(greek)
    return s.lower().replace('ϝ', '')

# Removes all diacritics and breathings for a transliterated column to serve as a
# base for Roman-letter Greek word entry
def removediacr(greek):
    # ugreek = greek.decode('utf-8')
    # newugreek = ''.join(c for c in unicodedata.normalize('NFD', ugreek) if unicodedata.category(c) != 'Mn')
    # return newugreek.encode('utf-8')
    ugreek = greek
    newugreek = ''.join(c for c in unicodedata.normalize('NFD', ugreek) if unicodedata.category(c) != 'Mn')
    return newugreek
# False if character is a combining breve/macron mark,
# true otherwise; used to flatten headwords to lookupforms
def not_length_marker(c):
    return unicodedata.category(c) != 'Mn' or \
           not ('BREVE' in unicodedata.name(c) or \
                'MACRON' in unicodedata.name(c))

# Changes a headword to a lookupform-acceptable entry; remove
# all non-essential diacritics (e.g. macrons and breves), as
# well as extra digits and slashes
def change_to_lookup(head):
    # if type(head) is not str:
    #     try:
    #         head = head.decode('utf-8')
    #     except UnicodeDecodeError:
    #     	# unsure if this is need - Ethan
    #         head = head.decode('latin1')
    tmp = unicodedata.normalize('NFD', head)
    head = ''.join([c for c in tmp if not_length_marker(c)])
    head = unicodedata.normalize('NFC', head) # recombine characters
    return re.sub('[0-9\[\]]', '', head)

# Stores each dico
def dico_loader(dico, entries, modify=False):
    global c
    if not entries: # Usually due to parser error
        sys.stdout.flush()
        return False
    elif dico not in DicoInfo.sidebar:
        c.execute('delete from Entries where dico=(?)', (dico,))
        for entry in entries:
            #print >> sys.stderr, entry['content'] 
            # Take entities out of all values
            #entry = dict([(x, unescape(y)) for (x, y) in entry.items()])
            if 'orth_orig' not in list(entry.keys()) or entry['orth_orig'] is None:
                entry['orth_orig'] = entry['head']
            c.execute('insert into Entries values (?,?,?,?,?)', \
                (entry['head'], entry['orth_orig'], entry['content'], dico, change_to_lookup(entry['head'])))
    else:
        c.execute('delete from Sidebar where dico=(?)', (dico,))
        for entry in entries: 
            c.execute('insert into Sidebar values (?,?,?,?,?)', \
                (entry['head'], entry['content'], entry['chapter'], dico, change_to_lookup(entry['head'])))
    return True

def main():
    #######################
    #        SETUP        #
    #######################

    global c
    args = sys.argv[1:]
    if not args:
        print(usage, file=sys.stderr)
        sys.exit(1)

    # Parse command-line arguments
    dicos_to_parse = {}
    flag2dicos = {'--greek': DicoInfo.greek,     '--latin': DicoInfo.latin,
                  '--sidebar': DicoInfo.sidebar, '--all': list(DicoInfo.all_dicos.keys())}
    dbname = 'new_dvlg-wheel.sqlite'
    # CHANGE BACK TO DICTIONARIES WHEN DONE TESTING
    dico_root = './dictionaries'
    notdbs = None
    loglevel = logging.INFO
    modify = False
    i = 0
    while i < len(args):
        if args[i] == '--help':
            print(usage, file=sys.stderr)
            sys.exit(0)
        elif args[i] == '--modify':
            modify = True
        elif args[i] == '--level': # set log level
            levelname = logging.getLevelName(args[i+1].upper())
            loglevel = levelname if type(levelname) is int else loglevel
            i += 1
        elif args[i] == '--db': # use provided db name
            dbname = args[i+1]
            i += 1
        elif args[i] == '--dico-root':
            dico_root = args[i+1]
            i += 1
        elif args[i] == '--all': # parse all dicos
            dicos_to_parse.update([(k,DicoInfo.all_dicos[k]) for k in DicoInfo.latin])
            dicos_to_parse.update([(k,DicoInfo.all_dicos[k]) for k in DicoInfo.greek])
            dicos_to_parse.update([(k,DicoInfo.all_dicos[k]) for k in DicoInfo.sidebar])
        elif args[i] == '--latin': # parse Latin/English dicos
            dicos_to_parse.update([(k,DicoInfo.all_dicos[k]) for k in DicoInfo.latin])
        elif args[i] == '--greek': # parse Greek dicos
            dicos_to_parse.update([(k,DicoInfo.all_dicos[k]) for k in DicoInfo.greek])
        elif args[i] == '--sidebar': # parse textbooks
            dicos_to_parse.update([(k,DicoInfo.all_dicos[k]) for k in DicoInfo.sidebar])
        elif args[i] == '--not': # ignore the following dico
            notdbs = args[i+1].split(',')
            i += 1
        else: # all other args
            if args[i] in DicoInfo.all_dicos:
                dicos_to_parse[args[i]] = DicoInfo.all_dicos[args[i]]
            else:
                print('%s: error: dico/option %s not recognized' \
                    % (prog, args[i]), file=sys.stderr)
                print(usage, file=sys.stderr)
                sys.exit(1)
        i += 1

    if notdbs:
        for ndb in notdbs:
            if ndb in dicos_to_parse:
                del dicos_to_parse[ndb]
                print('Not processing %s' % ndb)
    for dd in DicoInfo.disabled:
        if dd in dicos_to_parse:
            del dicos_to_parse[dd]

    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()

    # Log config
    logging.basicConfig(filename='parser.log',
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        filemode='w', level=loglevel, datefmt='%m/%d/%Y %I:%M:%S %p')

    if not dicos_to_parse:
        print('%s: error: no dictionaries specified' % prog, file=sys.stderr)
        print(usage, file=sys.stderr)
        sys.exit(-1)
    logging.info('Dicos to be parsed: '+str(list(dicos_to_parse.keys())))

    # Will skip creating Latin/GreekHeadwords if nothing has changed
    # in either (same with capitalization)
    parsing_latin = any([k in DicoInfo.latin for k in dicos_to_parse])
    parsing_greek = any([k in DicoInfo.greek for k in dicos_to_parse])
    performing_capitalization = any([k in DicoInfo.uncapped    for k in dicos_to_parse])


    #######################
    #       PARSERS       #
    #######################

    # Create dico tables in wheel from those in final
    try: # See if Entries already exists; if not, create it and index
        c.execute('select lookupform from Entries')
    except(sqlite3.OperationalError):
        c.executescript('create table Entries(head text, orth_orig text, content text, dico text, lookupform text); \
                         create index lookupform_index_e on Entries (lookupform);')
    else: # If Entries does exist, delete all rows in it
        if not modify:
            print('Clearing current Entries table...')
            c.execute('delete from Entries')

    try: # See if Sidebar already exists; if not, create it
        c.execute('select lookupform from Sidebar')
    except(sqlite3.OperationalError):
        c.executescript('create table Sidebar(head text, content text, chapter text, dico text, lookupform text); \
                         create index lookupform_index_s on Sidebar (lookupform);')
    else: # If Sidebar does exist, delete all rows in it
        if not modify:
            print('Clearing current Sidebar table...')
            c.execute('delete from Sidebar')

    # Parse each dico and send the resulting list to dico_loader
    print('Parsing dictionary files...')
    for dico in dicos_to_parse:
        spcs = ' '*(25-len(dico))
        logging.info('Parsing %s:', dico)
        sys.stdout.write('\t%s:%sparsing\r' % (dico, spcs)) 
        sys.stdout.flush()
        try:
            parse_func = getattr(dicos_to_parse[dico], 'parse')
        except(AttributeError):
            logging.error('Could not find parse function in parser for dico %s' % dico)
            sys.exit(-1)
        if dico == 'JACT':
            argspec = inspect.getfullargspec(parse_func)
            errors_occurred = False
            dico_path = os.path.join(dico_root, dico)
            if len(argspec.args) == 3: # New style: pass in logging functions directly
                dico_parsed, errors_occurred = parse_func(dico_path, logging.info, logging.warning)
            elif len(argspec.args) == 1: # Old style: return log statements instead of logging in parse function
                dico_parsed, tobelogged = parse_func(dico_path)
                for level in tobelogged:
                    for event in tobelogged[level]:
                        getattr(logging, level)(event)
                errors_occurred = bool(tobelogged['warning'])
            logging.info(dico + ' finished parsing; applying html cleanup and inserting into db')
        try:
            # argspec = inspect.getargspec(parse_func)
            argspec = inspect.getfullargspec(parse_func)
            errors_occurred = False
            dico_path = os.path.join(dico_root, dico)
            if len(argspec.args) == 3: # New style: pass in logging functions directly
                dico_parsed, errors_occurred = parse_func(dico_path, logging.info, logging.warning)
            elif len(argspec.args) == 1: # Old style: return log statements instead of logging in parse function
                dico_parsed, tobelogged = parse_func(dico_path)
                for level in tobelogged:
                    for event in tobelogged[level]:
                        getattr(logging, level)(event)
                errors_occurred = bool(tobelogged['warning'])
            logging.info(dico + ' finished parsing; applying html cleanup and inserting into db')
        except(Exception) as e: # Either error in calling the actual function itself or in documenting normal error
            logging.warning('While parsing %s: %s' % (dico, e))
            sys.stdout.write('\t%s:%suncaught exception; check log and parser. Dico not loaded.\n' % (dico, spcs))
            sys.stdout.flush()
        else: 
            # This little bit comes from the mix of unicode and str types that
            # are typical of Python 2.x; rather than expect one type from the
            # parsers, we just convert everything to UTF-8-encoded strings here
            # logging.debug('Converting everything to UTF-8 string from unicode')
            # for i in range(len(dico_parsed)):
            #     for k in dico_parsed[i]:
            #         if isinstance(dico_parsed[i][k], str):
            #             dico_parsed[i][k] = dico_parsed[i][k].encode('utf-8')

            # Loads entries to SQLite table
            sys.stdout.write('\t%s:%sloading\r' % (dico, spcs))
            sys.stdout.flush()
            if dico in DicoInfo.convert_xml:
                dico_parsed = clean_xml_and_convert(dico_parsed)
            loaded_successfully = dico_loader(dico, dico_parsed, modify)
            if errors_occurred:
                sys.stdout.write('\t%s:%snon-fatal errors during parse; check log.\n' % (dico, spcs))
            elif not loaded_successfully:
                sys.stdout.write('\t%s:%sno entries passed.\n' % (dico, spcs))
            else:
                sys.stdout.write('\t%s:%scomplete.\n' % (dico, spcs))
            
    ########################
    #    CAPITALIZATION    #
    ########################

    # Capitalizes headwords based on dictionaries labled "source" and other entries within the dictionaries;
    # 
    if not performing_capitalization:
        print('Skipping capitalization...')
    else:
        print('Grabbing entries for capitalization...')
        
        # Grab all source dico entries
        query = 'select distinct head, dico from Entries where '
        query += ' or '.join(['dico=(?)']*len(DicoInfo.cap_source)) # "...where dico=(?) or dico=(?) or..."
        c.execute(query, DicoInfo.cap_source)
        all_source_entries = c.fetchall()
        capitalization_sources = {}
        
        # For each distinct headword, put tuples (head, dico name) in a list under it    
        for entry in all_source_entries:
            if not entry[0].lower() in capitalization_sources:
                capitalization_sources[entry[0].lower()] = [entry]
            else:
                capitalization_sources[entry[0].lower()].append(entry)
        
        # Iterate over uncapped dicos
        for ucd in DicoInfo.uncapped:
            spcs = ' '*(25-len(ucd))
            sys.stdout.write('\t%s:%squerying\r' % (ucd, spcs))
            sys.stdout.flush()
            # cols are (in order): head, content, dico, lookupform, rowid
            c.execute('select *, rowid from Entries where dico=(?)', (ucd,))
            this_dico = {}
            for row in c: # Create dict so that each corresponds to a head (and is unique)
                head = row[0]
                rowid = row[-1]
                this_dico['%s|%d' % (head, rowid)] = row[:-1] # not rowid
        
            # Creates ucrefs, a subset of capitalization_sources, which is all the entries of capitalization_sources
            # which are also in the current ucd
            ucrefs = {}    
            done = 0
            todo = len(this_dico)
            for key in this_dico:
                done += 1
                if not done % 100 or done == todo:
                    sys.stdout.write('\t%s:%sgathering %06d/%06d\r' % (ucd, spcs, done, todo))
                    sys.stdout.flush()
                head = key.split('|')[0]
                try:
                    if head.lower() not in ucrefs:
                        ucrefs[head.lower()] = capitalization_sources[head.lower()]
                except(KeyError):
                    pass
                
            # Iterates over ucrefs to modify headwords and lookupforms in this_dico
            todo = len(ucrefs)
            done = 0
            for head in ucrefs:
                lower = False
                done += 1
                sys.stdout.write('\t%s:%sadjusting %06d/%06d\r' % (ucd, spcs, done, todo))
                sys.stdout.flush()

                # Checks if at least one headword is in lowercase; if none are lowercase, sets original head
                # to the first head of the first source dico
                any_heads_lowercase = any(ref[0].islower() for ref in ucrefs[head])             
                if not any_heads_lowercase:            
                    newhead = ucrefs[head][0][0]
                    for each in this_dico:
                        if each.split('|')[0].lower() == newhead.lower():
                            rowid = each.split('|')[1]
                            values = this_dico[each]
                            values = (newhead, values[1], values[2], values[3], change_to_lookup(newhead))
                            del this_dico[each]
                            this_dico['%s|%s' % (newhead, rowid)] = values
            
            todo = len(this_dico)
            done = 0
            if not modify:
                c.execute('delete from Entries where dico=(?)', (ucd,))
            for each in this_dico:
                done += 1
                sys.stdout.write('\t%s:%supdating  %06d/%06d\r' % (ucd, spcs, done, todo))
                sys.stdout.flush()
                entry_query = '('+ ','.join(['?' for x in this_dico[each]]) +')'
                c.execute('insert into Entries values '+entry_query, this_dico[each])
        
            sys.stdout.write('\t%s:%scomplete.' % (ucd, spcs) + (' '*14)+'\n')    

    ########################
    #    HEADWORD LISTS    #
    ########################

    print('Creating headword tables...')

    # Create headword and temp tables in wheel
    c.executescript("""drop table if exists Temp;
                     create table Temp (head text);""")

    # Fill temp and insert sorted, distinct entries into headword; this uses
    # all the dicos, not just selected ones; will be skipped if no Latin-headword dicos
    # were modified
    spcs = ' '*11
    if not parsing_latin:
        sys.stdout.write('\tLatinHeadwords:%sskipped.\n' % spcs)
    else:
        c.executescript('drop table if exists LatinHeadwords; \
                         create table LatinHeadwords (head text);')

        sys.stdout.write('\tLatinHeadwords:%screating \r' % spcs)
        sys.stdout.flush()

        for dico in DicoInfo.latin:
            c.execute('insert into Temp select lookupform from Entries where dico=(?)',\
            (dico,))

        sys.stdout.write('\tLatinHeadwords:%sfilling  \r' % spcs)
        sys.stdout.flush()
        c.executescript('insert into LatinHeadwords select distinct * from Temp ' + \
                        'order by head collate nocase; \
                         delete from Temp;')

        sys.stdout.write('\tLatinHeadwords:%scomplete.\n' % spcs)

    # Make table containing Greek headwords in alphabetical order; will be skipped if no
    # Greek-headword dicos were modified
    if not parsing_greek:
        sys.stdout.write('\tGreekHeadwords:%sskipped.\n' % spcs)
    else:
        sys.stdout.write('\tGreekHeadwords:%screating%s\r' % (spcs, ' '*21))
        sys.stdout.flush()
        
        c.executescript('drop table if exists GreekHeadwords; \
                         drop table if exists Transliterated; \
                         drop index if exists trans_index; \
                         create table GreekHeadwords (head text); \
                         create table Transliterated (normhead text, transhead text); \
                         create index trans_index on Transliterated (transhead);')

        for dico in DicoInfo.greek:
            c.execute('insert into Temp select lookupform from Entries where dico=(?)', (dico,))
       
        # Grab all distinct Greek headwords
        c.execute('select distinct * from Temp')
        gheads = c.fetchall()

        hwords = {}
        done = 0
        todo = len(gheads)

        # Transliteration to Roman letters for sorting
        # ^--- This transliteration has always been broken and I created a new function (tolower()) which
        # instead strips diacritics, lowers the case and then sorts the Greek. Capitals and digamma
        # are now sorted properly in GreekHeadwords. -Walt
        for x in range(todo):
            gheads[x] = gheads[x][0]
            done += 1
            if not done % 100 or done == todo:
                sys.stdout.write('\tGreekHeadwords:%stransliterating %06d/%06d\r' % (spcs, done, todo))
                sys.stdout.flush()
#            sort_head = translit(gheads[x])
            sort_head = tolower(gheads[x])
            
            # Another convoluted work-around: if multiple entries under same sort_head
            # (which happens when words only differ by their accents), create a list
            # of them under the sort_head
            try:
                test = hwords[sort_head]
            except(KeyError):
                hwords[sort_head] = gheads[x]
            else:
                if isinstance(hwords[sort_head], list):
                    hwords[sort_head].append(gheads[x])
                else:
                    hwords[sort_head] = [hwords[sort_head], gheads[x]]
        
        sys.stdout.write('\tGreekHeadwords:%ssorting%s\r' % (spcs, ' '*22))
        sys.stdout.flush()
            
#        sorted_trans = collections.OrderedDict(sorted(hwords.items()))
#        sorted_trans = sorted(hwords.keys(), key=lambda v: (v.upper(), v[0].islower()))
#        sorted_trans = sorted(hwords.keys(), key=str.lower)
#        todo = len(sorted_trans)
        todo = len(hwords)
        done = 0
        
        sys.stdout.write('\tGreekHeadwords:%sfilling%s\r' % (spcs, ' '*22))
        sys.stdout.flush()
        
#        for trans in sorted_trans: # Uses dict to insert correct Greek headwords in order
        for trans in sorted(hwords): # Uses dict to insert correct Greek headwords in order
#            print >> sys.stderr, trans, hwords[trans]
            #c.executemany('insert into GreekHeadwords values (?)', hwords[trans])
            if isinstance(hwords[trans], list):
                for greekhead in hwords[trans]:
                    c.execute('insert into GreekHeadwords values (?)', (greekhead,))
                    done += 1
            else:
                c.execute('insert into GreekHeadwords values (?)', (hwords[trans],))
                done += 1

        sys.stdout.write('\tGreekHeadwords:%scomplete.%s\n' % (spcs, ' '*20))

        # Create transliterated table (i.e. Greek alphabet w/o diacritics)
        sys.stdout.write('\tTransliterated:%screating \r' % spcs)
        sys.stdout.flush()
        
        c.execute('select * from GreekHeadwords')
        greek_heads = c.fetchall()
        #greek_heads = map(lambda x: x[0], c.fetchall())
        
        sys.stdout.write('\tTransliterated:%sfilling  \r' % spcs)
        sys.stdout.flush()
        #trans_heads = map(removediacr, greek_heads)
        #c.executemany('insert into Transliterated values (?,?)', greek_heads, trans_heads)
        for head in greek_heads:
            transhead = removediacr(head[0])
            c.execute('insert into Transliterated values (?,?)', (head[0],transhead))

        sys.stdout.write('\tTransliterated:%scomplete.\n' % spcs)

    c.execute('drop table Temp')

    # Commit changes and exit; only one commit done at the end, so that keyboard interrupts,
    # etc. won't screw up the table
    print('Saving...')
    conn.commit()

    print('Parsing complete.')

if __name__ == '__main__':
    main()
