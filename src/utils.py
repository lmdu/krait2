import gzip

#__all__ = [get_uncompressed_size]

def get_uncompressed_size(gzfile):
	fileobj = open(gzfile, 'rb')
	fileobj.seek(-8, 2)
	crc32 = gzip.read32(fileobj)
	isize = gzip.read32(fileobj)
	fileobj.close()
	return isize

if __name__ == '__main__':
	print(get_uncompressed_size('test1.fa.gz'))