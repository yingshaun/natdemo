'''

	:TODO: dual IP is not resolved properly
'''
import httplib, re #for canyouseeme.org
import socket
from singleton import Singleton

@Singleton
class IP(object):
	def __init__(self):
		self._myip = self.getCurrentIP()
		self._privateip = self.getPrivateIP()

	@property
	def myip(self):
		if self._myip == '':
			self._myip = self.getCurrentIP()
			if self._myip == '':
				raise Exception("Failed to get self ip!")
		return self._myip

	@property
	def myip2(self):
		if self._privateip == '':
			self._privateip = self.getPrivateIP()
			if self._privateip == '':
				raise Exception("Failed to get self ip!")
		return self._privateip

	def getCurrentIP(self):
#		return '192.168.84.206'
		try:
			conn = httplib.HTTPConnection("www.canyouseeme.org")
			conn.request("GET", "/")
			r1 = conn.getresponse()
			m = r1.read()
			s = re.findall('\d+\.\d+\.\d+\.\d+', m)
			return s[0]
		except:
			return ''
		r = 0
		to_addr = ('137.189.97.35', 39504)
		to_addr2 = ('192.168.84.208', 39504)
		s = socket.socket(family=socket.AF_INET, \
				type=socket.SOCK_DGRAM, \
				proto=socket.IPPROTO_UDP)
		s.settimeout(2)
		while r<3:
			s.sendto('hi', to_addr2)
			s.sendto('hi', to_addr)
			try:
				msg,addr = s.recvfrom(100)
				return msg
			except:
				r += 1
		return ''

	def getPrivateIP(self):
		try: return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1][0]
		except KeyError: return ''
