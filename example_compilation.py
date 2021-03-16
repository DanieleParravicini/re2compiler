import re2compiler

data 	= '/(([KRQZX])([LIVMAX])(.{2}?)([GSTALIVX])([^FYWPGDN])(.{2}?)([LIVMSAX])(.{4,9}?)([LIVMFX])(.)([^PLH])([LIVMSTAX])([GSTACILX])([^GPK])([^F])(.)([GANBQZRFX])([LIVMFYX])(.{4,5}?)([LFYX])(.{3}?)([FYIVAX])([^FYWHCM])([^PGVI])(.{2}?)([GSADBEZNBQZKRX])(.)([NBSTAPKLX])([PARLX]))/'
output	= re2compiler.compile(data=data, frontend='pcre')
print(output)