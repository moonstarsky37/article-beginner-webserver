import os
import os.path as op
import sys
from parser import Draw
sys.path.insert(0, op.join(op.dirname(__file__), ".."))


if __name__ == '__main__':
    import optparse
    p = optparse.OptionParser("%prog [obo_file]")
    p.add_option("--id", dest="id", action="store", type="string",
                 default=None)

    opts, args = p.parse_args()

    if not len(args):
        obo_file = "go-basic.obo"
    else:
        obo_file = args[0]
        assert os.path.exists(obo_file), "file %s not found!" % obo_file

    D = Draw(obo_file)

    if opts.id is not None:
        rec = D.query_id(opts.id)
        if rec is not None:
            D.draw_lineage([rec])
