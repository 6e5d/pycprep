from importer import importer
importer("../../gid/gid", __file__)
importer("../../syslib/syslib", __file__)
importer("../../pyctok/pyctok", __file__)

from gid import path2gid, gid2c
from syslib import symtable as build_symtable
from pyctok import Tokenizer

def getlines(file):
	if not file.exists():
		return []
	result = []
	for line in open(file):
		line = line.strip()
		if not line:
			continue
		if not line.isalnum():
			continue
		result.append(line)
	return result

def replace_ns(line, gid):
	rule = gid[-1]
	istype = False
	idx = line.find(rule + "(")
	if idx == -1:
		idx = line.find(rule.capitalize() + "(")
		if idx == -1:
			return (False, line)
		istype = True
	head = line[:idx]
	tail = line[idx:]
	pleft = tail.find("(")
	pright = tail.find(")")
	if pleft == -1 or pright <= pleft:
		raise Exception(line, tail)
	sym = tail[pleft + 1:pright]
	concat = list(gid)
	if sym:
		concat.append(sym)
	if istype:
		concat = gid2c(concat, "camel")
	else:
		concat = gid2c(concat, "snake")
	return (True, head + concat + tail[pright + 1:])

def getsrclines(file, kjkjs):
	defines = dict()
	result = []
	for line in open(file):
		line = line.strip()
		idx = line.find("//")
		if idx >= 0 and line[idx:].find('"') == -1:
			line = line[:idx]
		line = line.strip()
		if not line:
			continue
		idx = line.find("__FILE__")
		if idx >= 0:
			line = line[:idx] + f'"{str(file)}"' + line[idx + 8:]
		if line[0] == "#":
			if line.startswith("#define"):
				sp = line.split(" ")
				if len(sp) != 3:
					print("warning, skip:", line)
					continue
				defines[sp[1]] = sp[2]
			continue
		while True:
			flag = True
			for kjkj in kjkjs:
				replaced, line = replace_ns(line, kjkj)
				if replaced:
					flag = False
			if flag:
				break
		result.append(line)
	return result, defines

def step1(proj):
	kjkjs = []
	gids = []
	fsys = proj / ".lpat/syslib.txt"
	for line in getlines(fsys):
		gids.append(["com", "6e5d", "syslib"] + line.split("_"))
	symtable = build_symtable(gids)
	fkjkj = proj / ".lpat/deps.txt"
	for line in getlines(fkjkj):
		gid = path2gid(proj.parent / line)
		kjkjs.append(gid)
	kjkjs.append(path2gid(proj))
	return symtable, kjkjs

def step2_readall(proj, kjkjs):
	lines = []
	defines = dict()
	if (proj / "include").exists():
		for file in (proj / "include").iterdir():
			line, define = getsrclines(file, kjkjs)
			lines += line
			defines.update(define)
	if (proj / "src").exists():
		for file in (proj / "src").iterdir():
			line, define = getsrclines(file, kjkjs)
			defines.update(define)
			lines += line
	return lines, defines

def step2(proj, symtable, kjkjs):
	lines, defines = step2_readall(proj, kjkjs)
	t = Tokenizer()
	toks = []
	for line in lines:
		tok = t.tokenize(line)
		toks += tok
	for idx, (ty, sym) in enumerate(toks):
		if sym in symtable:
			if symtable[sym][0] == "type":
				toks[idx] = (21, sym)
			else:
				assert symtable[sym][0] == "name"
				toks[idx] = (22, sym)
	return toks, defines

def pycprep(proj):
	symtable, kjkjs = step1(proj)
	return step2(proj, symtable, kjkjs)
