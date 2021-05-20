import sys
import struct

__all__ = ["get_uncompressed_size", "is_gzip_compressed",
			"iupac_numerical_multiplier"]

def is_gzip_compressed(fpath):
	with open(fpath, 'rb') as f:
		return f.read(2) == b'\x1f\x8b'

def get_uncompressed_size(fpath):
	with open(fpath, 'rb') as f:
		f.seek(-4, 2)
		size, = struct.unpack("<I", f.read(4))

	return size

#https://en.wikipedia.org/wiki/IUPAC_numerical_multiplier
#https://www.qmul.ac.uk/sbcs/iupac/misc/numb.html
def iupac_numerical_multiplier(num):
	mapping = {
		-1: 'mono',
		-2: 'di',
		 1: 'hen',
		 2: 'do',
		 3: 'tri',
		 4: 'tetra',
		 5: 'penta',
		 6: 'hexa',
		 7: 'hepta',
		 8: 'octa',
		 9: 'nona',
		10: 'deca',
		11: 'undeca',
		20: 'icosa',
		30: 'triaconta',
		40: 'tetraconta',
		50: 'pentaconta',
		60: 'hexaconta',
		70: 'heptaconta',
		80: 'octaconta',
		90: 'nonaconta',
		100: 'hecta',
		200: 'dicta',
		300: 'tricta',
		400: 'tetracta',
		500: 'pentacta',
		600: 'hexacta',
		700: 'heptacta',
		800: 'octacta',
		900: 'nonacta',
		1000: 'kilia',
		2000: 'dilia',
		3000: 'trilia',
		4000: 'tetralia',
		5000: 'pentalia',
		6000: 'hexalia',
		7000: 'heptalia',
		8000: 'octalia',
		9000: 'nonalia'
	}

	assert num < 10000, "the number is too large"

	if num == 1 or num == 2:
		num = -num

	affix = mapping.get(num, None)

	if affix is not None:
		return affix

	affixs = []
	scales = [0, 10, 100, 1000]

	num = [int(i) for i in list(str(num))]
	num.reverse()

	for i, n in enumerate(num):
		if n > 0:
			if i > 0:
				n = n*scales[i]

			affixs.append(mapping[n])

	return ''.join(affixs)

if __name__ == '__main__':
	affix = iupac_numerical_multiplier(int(sys.argv[1]))
	print(affix)