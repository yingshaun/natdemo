from socket import *
from config import *
from json import dumps,loads
from sys import argv
from time import sleep
from random import randint

class peer():
	def __init__(self, port):
		#self.skt = rudpSocket(port)
		self.skt = socket(AF_INET, SOCK_DGRAM) # uDP
		self.skt.bind(('', port)) 

	def connect(self, destAddr):
		# msg = (type, content)
		msg = (TYPE_CONNECT, 'connection request msg')
		self.skt.sendto(dumps(msg), destAddr)
		print 'peer connecting to midPeer'

	def get(self):
		data, addr = self.skt.recvfrom(100)
		# extract target peer address from recvPkt
		msg = loads(data)
		if msg[0] == TYPE_ADDREX:
			ip_addr = msg[1][0].encode('utf-8')
			port = msg[1][1]
			print 'peer getting target peer addr from midPeer'
			return (ip_addr, port)
		else:
			print 'unexpected messages received'

	def touch(self, target_addr):
		sleep(1) # make sure the hole has been punched
		msg = (TYPE_PUNCHHOLE, 'hole-punching msg')
		self.skt.sendto(dumps(msg), target_addr)
		print 'peer punching a hole for', target_addr
		
		sleep(1)
		msg = (TYPE_DATA, 'data msg')
		self.skt.sendto(dumps(msg), target_addr)
		print 'peer sending to target peer'

		data, addr = self.skt.recvfrom(100)
		msg = loads(data)
		print 'peer receives a msg from ', addr

	def sendData(self, target_addr):
		# send data packets to the target addr three times
		for i in range(1,4):
			sleep(1)
			self.skt.sendto('hello', target_addr)
			print 'peer has sent a packet @ ', i

			recvPkt, addr = self.skt.recvfrom(100)
			print 'peer has received a packet from ', addr

	def start(self):
		self.connect(midPeer_addr)
		target_addr = self.get()
		self.touch(target_addr)
		self.sendData(target_addr)

if len(argv) == 2:
	a = peer(int(argv[1]))
	a.start()
else:
	# choose a random port number
	a = peer(39000 + randint(1,100))
	a.start()

