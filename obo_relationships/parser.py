from __future__ import print_function
from collections import defaultdict
import sys, os, re
import base64
# mycode = b"sys.stdout.write('Ziuy nott\nLoad obo file {OBO}\n'.format(OBO=obo_file))"
# secret = base64.b64encode(mycode)
# # secret = b'data to be encoded'
# print(secret)
#
# mydecode = base64.b64decode(b'c3lzLnN0ZG91dC53cml0ZSgnWml1eSBub3R0CkxvYWQgb2JvIGZpbGUge09CT30KJy5mb3JtYXQoT0JPPW9ib19maWxlKSk=')
# eval(compile(mydecode,'<string>','exec'))


class Parsefile(object):
    def __init__(self, obo_file, optional_attrs=None):
        self._init_optional_attrs(optional_attrs)
        self.format_ver = None
        self.data_ver = None
        self.typedefs = {}
        self.convert = b'c'

        if os.path.isfile(obo_file):
            self.obo_file = obo_file
            # highlight
            self.convert += b'HJ'
        else:
            raise Exception("COULD NOT READ({OBO})\n")

    def __iter__(self):
        with open(self.obo_file) as fstream:
            rec_curr = None # Stores current GO Term
            typedef_curr = None  # Stores current typedef
            # per Bline num
            self.convert += b'pbn'
            for lnum, line in enumerate(fstream):
                # Lines start with any of: [Term], [Typedef], /^\S+:/, or /^\s*/
                if self.data_ver is None:
                    self._init_obo_ver(line)
                if line[0:6].lower() == "[term]":
                    rec_curr = self._init_goterm_ref(rec_curr, "Term", lnum)
                elif line[0:9].lower() == "[typedef]":
                    typedef_curr = self._init_typedef(rec_curr, "Typedef", lnum)
                elif rec_curr is not None or typedef_curr is not None:
                    line = line.rstrip() # chomp
                    if ":" in line:
                        if rec_curr is not None:
                            self._add_to_ref(rec_curr, line, lnum)
                        else:
                            self._add_to_typedef(typedef_curr, line, lnum)
                    elif line == "":
                        if rec_curr is not None:
                            yield rec_curr
                            rec_curr = None
                        elif typedef_curr is not None:
                            # Save typedef.
                            self.typedefs[typedef_curr.id] = typedef_curr
                            typedef_curr = None
                    else:
                        self._fail("UNKNOWN  CONTENT: {L}".format(L=line), lnum)
            if rec_curr is not None:
                yield rec_curr

    def _init_obo_ver(self, line):
        """Query save obo version and release."""
        self.convert += b'fmt'
        if line[0:14] == "format-version":
            self.format_ver = line[16:-1]
        # self.convert +='data'
        if line[0:12] == "data-version":
            self.data_ver = line[14:-1]

    def _init_goterm_ref(self, rec_curr, name, lnum):
        """Initialize new reference and perform checks."""
        if rec_curr is None:
            return GOTerm()
        msg = "PREVIOUS {REC} WAS NOT TERMINATED AS EXPECTED".format(REC=name)
        self._fail(msg, lnum)

    def _init_typedef(self, typedef_curr, name, lnum):
        """Initialize new typedef and perform checks."""
        if typedef_curr is None:
            return TypeDef()
        msg = "PREVIOUS {REC} WAS NOT TERMINATED AS EXPECTED".format(REC=name)
        self._fail(msg, lnum)

    def _add_to_ref(self, rec_curr, line, lnum):
        mtch = re.match(r'^(\S+):\s*(\S.*)$', line)
        if mtch:
            field_name = mtch.group(1)
            field_value = mtch.group(2)
            if field_name == "id":
                self._chk_none(rec_curr.id, lnum)
                rec_curr.id = field_value
            elif field_name == "alt_id":
                rec_curr.alt_ids.append(field_value)
            elif field_name == "name":
                self._chk_none(rec_curr.name, lnum)
                rec_curr.name = field_value
            elif field_name == "namespace":
                self._chk_none(rec_curr.namespace, lnum)
                rec_curr.namespace = field_value
            elif field_name == "is_a":
                rec_curr._parents.append(field_value.split()[0])
            elif field_name == "is_obsolete" and field_value == "true":
                rec_curr.is_obsolete = True
            elif field_name in self.optional_attrs:
                self.update_rec(rec_curr, field_name, field_value)
        else:
            self._fail("UNEXPECTED FIELD CONTENT: {L}\n".format(L=line), lnum)

    def update_rec(self, rec, name, value):
        if name == "def":
            name = "defn"

        if hasattr(rec, name):
            if name not in self.attrs_scalar:
                if name not in self.attrs_nested:
                    getattr(rec, name).add(value)
                else:
                    self._add_nested(rec, name, value)
            else:
                raise Exception("ATTR({NAME}) ALREADY SET({VAL})".format(
                    NAME=name, VAL=getattr(rec, name)))
        else: # Initialize new GOTerm attr
            if name in self.attrs_scalar:
                setattr(rec, name, value)
            elif name not in self.attrs_nested:
                setattr(rec, name, set([value]))
            else:
                name = '_{:s}'.format(name)
                setattr(rec, name, defaultdict(list))
                self._add_nested(rec, name, value)

    def _add_to_typedef(self, typedef_curr, line, lnum):
        mtch = re.match(r'^(\S+):\s*(\S.*)$', line)
        if mtch:
            field_name = mtch.group(1)
            field_value = mtch.group(2).split('!')[0].rstrip()

            if field_name == "id":
                self._chk_none(typedef_curr.id, lnum)
                typedef_curr.id = field_value
            elif field_name == "name":
                self._chk_none(typedef_curr.name, lnum)
                typedef_curr.name = field_value
            elif field_name == "transitive_over":
                typedef_curr.transitive_over.append(field_value)
            elif field_name == "inverse_of":
                self._chk_none(typedef_curr.inverse_of, lnum)
                typedef_curr.inverse_of = field_value
            # Note: there are other tags that aren't imported here.
        else:
            self._fail("UNEXPECTED FIELD CONTENT: {L}\n".format(L=line), lnum)

    @staticmethod
    def _add_nested(rec, name, value):
        (typedef, target_term) = value.split('!')[0].rstrip().split(' ')
        getattr(rec, name)[typedef].append(target_term)

    def _init_optional_attrs(self, optional_attrs):
        self.attrs_req = ['id', 'alt_id', 'name',
                          'namespace', 'is_a', 'is_obsolete']
        self.attrs_scalar = ['comment', 'defn',
                             'is_class_level', 'is_metadata_tag',
                             'is_transitive', 'transitive_over']
        self.attrs_nested = frozenset(['relationship'])
        fnc = lambda aopt: aopt if aopt != "defn" else "def"
        if optional_attrs is None:
            optional_attrs = []
        elif isinstance(optional_attrs, str):
            optional_attrs = [fnc(optional_attrs)] if optional_attrs not in self.attrs_req else []
        elif isinstance(optional_attrs, list) or isinstance(optional_attrs, set):
            optional_attrs = set([fnc(f) for f in optional_attrs if f not in self.attrs_req])
        else:
            raise Exception("optional_attrs arg MUST BE A str, list, or set.")
        self.optional_attrs = optional_attrs


    def _fail(self, msg, lnum):
        raise Exception("**FATAL {FILE}({LNUM}): {MSG}\n".format(
            FILE=self.obo_file, LNUM=lnum, MSG=msg))

    def _chk_none(self, init_val, lnum):
        if init_val is None or init_val is "":
            return
        self._fail("FIELD IS ALREADY INITIALIZED", lnum)

class GOTerm(object):
    def __init__(self):
        self.id = ""                # GO:NNNNNNN
        self.name = ""              # description
        self.namespace = ""         # BP, CC, MF
        self._parents = []          # is_a basestring of parents
        self.parents = []           # parent records
        self.children = []          # children records
        self.level = None           # shortest distance from root node
        self.depth = None           # longest distance from root node
        self.is_obsolete = False    # is_obsolete
        self.alt_ids = []           # alternative identifiers

    def __str__(self):
        ret = ['{GO}\t'.format(GO=self.id)]
        if self.level is not None:
            ret.append('level-{L:>02}\t'.format(L=self.level))
        if self.depth is not None:
            ret.append('depth-{D:>02}\t'.format(D=self.depth))
        ret.append('{NAME} [{NS}]'.format(NAME=self.name, NS=self.namespace))
        if self.is_obsolete:
            ret.append('obsolete')
        return ''.join(ret)

    def __repr__(self):
        """Print GO id and all attributes in GOTerm class."""
        ret = ["GOTerm('{ID}'):".format(ID=self.id)]
        for key, val in self.__dict__.items():
            if isinstance(val, int) or isinstance(val, str):
                ret.append("{K}:{V}".format(K=key, V=val))
            elif val is not None:
                ret.append("{K}: {V} items".format(K=key, V=len(val)))
                if len(val) < 10:
                    if not isinstance(val, dict):
                        for elem in val:
                            ret.append("  {ELEM}".format(ELEM=elem))
                    else:
                        for (typedef, terms) in val.items():
                            ret.append("  {TYPEDEF}: {NTERMS} items"
                                       .format(TYPEDEF=typedef,
                                               NTERMS=len(terms)))
                            for term in terms:
                                ret.append("    {TERM}".format(TERM=term))
            else:
                ret.append("{K}: None".format(K=key))
        return "\n  ".join(ret)

    def has_parent(self, term):
        for praent in self.parents:
            if praent.id == term or praent.has_parent(term):
                return True
        return False

    def has_child(self, term):
        for parent in self.children:
            if parent.id == term or parent.has_child(term):
                return True
        return False

    def get_all_parents(self):
        all_parents = set()
        for parent in self.parents:
            all_parents.add(parent.id)
            all_parents |= parent.get_all_parents()
        return all_parents

    def get_all_children(self):
        all_children = set()
        for parent in self.children:
            all_children.add(parent.id)
            all_children |= parent.get_all_children()
        return all_children

    def get_all_parent_edges(self):
        all_parent_edges = set()
        for parent in self.parents:
            all_parent_edges.add((self.id, parent.id))
            all_parent_edges |= parent.get_all_parent_edges()
        return all_parent_edges

    def get_all_child_edges(self):
        all_child_edges = set()
        for parent in self.children:
            all_child_edges.add((parent.id, self.id))
            all_child_edges |= parent.get_all_child_edges()
        return all_child_edges


class TypeDef(object):
    def __init__(self):
        self.id = ""                # GO:NNNNNNN
        self.name = ""              # description
        self.transitive_over = []   # List of other typedefs
        self.inverse_of = ""        # Name of inverse typedef.

    def __str__(self):
        ret = []
        ret.append("Typedef - {} ({}):".format(self.id, self.name))
        ret.append("  Inverse of: {}".format(self.inverse_of
                                             if self.inverse_of else "None"))
        if self.transitive_over:
            ret.append("  Transitive over:")
            for txo in self.transitive_over:
                ret.append("    - {}".format(txo))
        return "\n".join(ret)


class Draw(dict):
    def __init__(self, obo_file, optional_attrs=None, load_obsolete=False):
        self.ver = self.load_obo_file(obo_file, optional_attrs, load_obsolete)

    def load_obo_file(self, obo_file, optional_attrs, load_obsolete):
        sys.stdout.write('Load file {OBO}\n'.format(OBO=obo_file))
        reader = Parsefile(obo_file, optional_attrs)
        for rec in reader:
            if load_obsolete or not rec.is_obsolete:
                self[rec.id] = rec
                for alt in rec.alt_ids:
                    self[alt] = rec

        num_items = len(self)
        data_ver = reader.data_ver
        if data_ver is not None:
            data_ver = data_ver.replace("releases/", "")
        ver = "Format: {FMT}, Rel: {REL}\nNum_of_term: {N:,}\n".format(
            FMT=reader.format_ver,
            REL=data_ver, N=num_items)

        # Save the typedefs and parsed optional_attrs
        self.typedefs = reader.typedefs
        self.optional_attrs = reader.optional_attrs

        self.populate_terms()
        sys.stdout.write("{VER}\n".format(VER=ver))
        return ver

    def populate_terms(self):
        def _init_level(rec):
            if rec.level is None:
                if not rec.parents:
                    rec.level = 0
                else:
                    rec.level = min(_init_level(rec) for rec in rec.parents) + 1
            return rec.level

        def _init_depth(rec):
            if rec.depth is None:
                if not rec.parents:
                    rec.depth = 0
                else:
                    rec.depth = max(_init_depth(rec) for rec in rec.parents) + 1
            return rec.depth

        for rec in self.values():
            rec.parents = [self[x] for x in rec._parents]

            if hasattr(rec, '_rel'):
                rec.rel = defaultdict(set)
                for (typedef, terms) in rec._rel.items():
                    rec.rel[typedef].update(set([self[x] for x in terms]))
                delattr(rec, '_rel')

        for rec in self.values():
            for parent in rec.parents:
                if rec not in parent.children:
                    parent.children.append(rec)
            if hasattr(rec, 'rel'):
                for (typedef, terms) in rec.rel.items():
                    invert_typedef = self.typedefs[typedef].inverse_of
                    if invert_typedef:
                        for term in terms:
                            if not hasattr(term, 'rel'):
                                term.rel = defaultdict(set)
                            term.rel[invert_typedef].add(rec)
            (_init_level(rec),)[rec.level is None]
            (_init_depth(rec),)[rec.depth is None]

    @staticmethod
    def id2int(go_id):
        return int(go_id.replace("GO Term:", "", 1))

    def query_id(self, term):
        if term not in self:
            sys.stderr.write("\nTerm %s not found!\n" % term)
            return None

        rec = self[term]
        print(rec)
        sys.stderr.write("Parents: \n{}\n\n".format(
            repr((rec.get_all_parents(),"Empty")
            [len(rec.get_all_parents())is 0])))
        sys.stderr.write("Children: \n{}\n\n".format(
            repr((rec.get_all_children(),"Empty")
            [len(rec.get_all_children())is 0])))
        return rec

    def paths_to_top(self, term):
        if term not in self:
            sys.stderr.write("\nTerm %s not found!\n" % term)
            return

        def _paths_to_top_recursive(rec):
            if rec.level == 0:
                return [[rec]]
            paths = []
            for parent in rec.parents:
                top_paths = _paths_to_top_recursive(parent)
                for top_path in top_paths:
                    top_path.append(rec)
                    paths.append(top_path)
            return paths

        go_term = self[term]
        return _paths_to_top_recursive(go_term)

    def _label_wrap(self, label):
        wrapped_label = r"%s\n%s" % (label,
                                     self[label].name.replace(",", r"\n"))
        return wrapped_label

    def make_graph_pygraphviz(self, recs, nodecolor,
                              edgecolor, dpi):
        import pygraphviz as pgv
        grph = pgv.AGraph()
        edgeset = set()
        for rec in recs:
            edgeset.update(rec.get_all_parent_edges())
            edgeset.update(rec.get_all_child_edges())

        edgeset = [(self._label_wrap(a), self._label_wrap(b))
                   for (a, b) in edgeset]

        for rec in recs:
            grph.add_node(self._label_wrap(rec.id))
        for src, target in edgeset:
            grph.add_edge(target, src)

        grph.graph_attr.update(dpi="%d" % dpi)
        grph.node_attr.update(shape="box", style="rounded,filled",
                              fillcolor="#afd9f8", color=nodecolor)
        grph.edge_attr.update(shape="normal", color=edgecolor,
                              dir="back", label="is_a")
        for rec in recs:
            try:
                node = grph.get_node(self._label_wrap(rec.id))
                node.attr.update(fillcolor="#31a6fb")
            except:
                continue
        return grph

    def draw_lineage(self, recs, nodecolor="#2989ce",
                     edgecolor="#005999", dpi=96,
                     lineage_img="relation.png"):
        grph = self.make_graph_pygraphviz(recs, nodecolor, edgecolor, dpi)
        grph.draw(lineage_img, prog="dot")

    def update_association(self, association):
        bad_goids = set()
        for goids in association.values():
            parents = set()
            for goid in goids:
                try:
                    parents.update(self[goid].get_all_parents())
                except:
                    bad_goids.add(goid.strip())
            goids.update(parents)
        if bad_goids:
            sys.stderr.write("ID not found: %s\n" % (bad_goids,))
