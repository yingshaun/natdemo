from rudp import *
from rudpException import *

midPeer_addr = ('137.165.1.114', 39951)

class peer():
	def __init__(self, port):
		self.skt = rudpSocket(port)

	def connect(self, destAddr):
		self.skt.sendto('connecting', destAddr, True)
		print 'peer connecting to midPeer'

	def get(self):
		# get target peer's IP address from midPeer
		# blocking
		recvPkt, addr = self.skt.recvfrom()
		# extract target peer address from recvPkt
		ip_addr = recvPkt.split('(')[1].split(')')[0].split(',')[0][1:-1]
		port = int(recvPkt.split('(')[1].split(')')[0].split(',')[1])
		print 'peer getting target peer addr from midPeer'
		return (ip_addr, port)

	def touch(self, target_addr):
		self.skt.sendto('sending', target_addr, False)
		print 'peer punching a hole for', target_addr
		
		sleep(1)
		self.skt.sendto('hello world', target_addr, False)
		print 'peer sending to target peer'

		recvPkt, addr = self.skt.recvfrom()
		print 'peer has been contacted by target peer at', addr

	def keepalive(self, target_addr):
		while True:
			sleep(1)
			self.skt.sendto('hello', target_addr, False)
			print 'peer has sent a packet @', str(int(time()))[-3:]

			recvPkt, addr = self.skt.recvfrom()
			print 'peer has received a packet from ', addr


	def start(self):
		self.connect(midPeer_addr)
		target_addr = self.get()
		self.touch(target_addr)
		self.keepalive(target_addr)

