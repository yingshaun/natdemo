from socket import *
from json import dumps,loads
from rudp import *
from gevent import sleep, spawn

PX_MIDPEER = 1
PX_PEER = 2 	
# The requesting node is called Peer
# The node Peer wants to connect with is called Buddy
MSG_PX_REQUEST = 1  	# from Peer to Third Party
MSG_PX_REPLY = 2		# from Third Party to Peer
MSG_PX_KEEPALIVE = 3 	# from Node to all connected Nodes
MSG_PX_CONNECT = 4		# from Node to Node

DEBUG = True

mid_ip = ('137.189.97.35', 39951)

class pxService():
	def __init__(self, rudpSkt = None, peerRole = None, port = 39951):
		# if skt is undefined, create a UDP socket
		if rudpSkt: 
			self.skt = rudpSkt
		else: 
			self.skt = rudpSocket(port)
			#self.skt = socket(AF_INET, SOCK_DGRAM) # UDP
			#self.skt.bind(('', port)) 
		self.role = peerRole
		self.rxDict = dict()	# Dict of connected Nodes
		spawn(self.keepAliveLoop)
		sleep(0)

	def __del__(self):
		self.skt.close()

	def getNodesFromList(self):
		return self.rxDict.keys()

	def delNodeFromList(self, node_addr):
		try: self.rxDict.pop(node_addr)
		except KeyError: return False	# node_addr does not exist
		return True

	def addNodeToList(self, node_addr):
		if self.rxDict.get(node_addr) == None:
			self.rxDict[node_addr] = True
			return True
		else: return False

	def keepAliveLoop(self):
		while True:
			if len(self.rxDict): # There exists a node in the list
				nodeList = self.rxDict.keys()
				for i in range(len(nodeList)):
					self.skt.sendto('Keep Alive Msg', nodeList[i], True)
					sleep(0)
					if DEBUG: print 'Send Keep-Alive-Msg to', nodeList[i]
			else:
				if DEBUG: print 'No nodes in the list'
			sleep(5)

	def recvLoop(self):
		pass

	def request(self, thirdParty_addr, buddy_id = None):
		pass

'''
	def start(self):
		if self.role == PX_MIDPEER:
			while True:
				data, addr = self.skt.recvfrom(100)
				msg = loads(data)
				# process according to msg
				if DEBUG:
					print "msg:", msg, 'from', addr
				if int(msg[0]) == MSG_PX_REQUEST:
					# Send IP list to the requesting Node
					self.notify(addr, self.rxDict.keys())
					# Check whether the requesting node
					# exists in the rxDict
					if self.rxDict.get(addr) == None:
						self.rxDict[addr] = True

	def request(self, midPeer_addr, buddy_id = None):
		msg = (MSG_PX_REQUEST, midPeer_addr, buddy_id)
		self.skt.sendto(dumps(msg), midPeer_addr)
		if DEBUG: 
			if buddy_id == None:
				print 'Requesting all existing receivers via', midPeer_addr
			else:
				print 'Requesting receiver with ID', buddy_id, 'via', midPeer_addr
		while True:
			data, addr = self.skt.recvfrom(100)
			if addr == midPeer_addr:
				buddyIDList = loads(data)[1]
				for i in range(0, len(buddyIDList)):
					buddyIDList[i] = (buddyIDList[i][0].encode(), buddyIDList[i][1])
				if DEBUG:
					print 'Expected reply from', addr
					print 'buddyIDList:', buddyIDList
				break
			else:
				if DEBUG:
					print 'Unexpected reply from', addr
					print 'Content:', loads(data)
					print 'Keep waiting for replies'
				continue
		return buddyIDList

	def notify(self, nodeA_addr, nodeIPList):
		msg = (MSG_PX_REPLY, nodeIPList)
		self.skt.sendto(dumps(msg), nodeA_addr)
		# Send B's IP address to A

	def connect(self, buddyIPList):
		# Only available to Peers
		for i in range(0, len(buddyIPList)):
			msg = (MSG_PX_CONNECT, None)
			self.skt.sendto(dumps(msg), buddyIPList[i])
			if DEBUG:
				print 'Punching a hole for Buddy @', buddyIPList[i]
		data, addr = self.skt.recvfrom(100)
		if DEBUG:
			print 'Received a packet from Buddy @', addr
		return True
'''
