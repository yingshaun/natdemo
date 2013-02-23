from rudp import *
from rudpException import *

class midPeer():
	def __init__(self):
		self.skt = rudpSocket(39951)
		self.list = []

	def wait(self):
		# wait for the connection request from peerlist
		# blocking
		recvPkt, addr = self.skt.recvfrom()
		return addr

	def introduce(self, peerA_addr, peerB_addr):
		self.skt.sendto(str(peerA_addr), peerB_addr, True)
		self.skt.sendto(str(peerB_addr), peerA_addr, True)

	def start(self):
		print 'midPeer is up; waiting for connection requests'

		addr = self.wait() # blocking
		self.list.append(addr)
		print '1st peer is connected', addr

		addr = self.wait() # blocking
		self.list.append(addr)
		print '2nd peer is connected', addr

		if self.list.__len__() == 2:
			self.introduce(self.list[0], self.list[1])
			print 'introducing peers to each other'
		else: 
			print 'Error: no enough peers'

		print 'midPeer has done its job'