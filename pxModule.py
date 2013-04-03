from socket import *
from json import dumps,loads
from rudp import *
from gevent import sleep, spawn

PX_MIDPEER = 1
PX_PEER = 2 	
# The requesting node is called Peer
# The node Peer wants to connect with is called Buddy
MSG_PX_CONNECT = 1		# from Node to Node via Third Party
MSG_PX_REPLY = 2		# from Third Party to Peer
MSG_PX_KEEPALIVE = 3 	# from Node to all connected Nodes
MSG_PX_ARRIVAL = 4


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
		spawn(self.recvLoop)
		sleep(0)

	def __del__(self):
		self.skt.close()

	def getNodes(self):
		return self.rxDict.keys()

	def delNodes(self, node_list, listFlag = True):
		if not listFlag:
			node_addr = (node_list[0].encode(), node_list[1])
			if node_addr[0].__class__() == u'':
				node_addr[0] = node_list[0].encode()
			try: self.rxDict.pop(node_addr)
			except KeyError: pass
		else:
			for i in range(len(node_list)):
				node_list[i] = (node_list[i][0].encode(), node_list[i][1])
				try: self.rxDict.pop(node_list[i])
				except KeyError: pass

	def addNodes(self, node_list, listFlag = True):
		if not listFlag: # Only one node to add
			node_addr = (node_list[0].encode(), node_list[1])
			if node_addr.__class__() == u'':
				node_addr[0] = node_list[0].encode()
			if self.rxDict.get(node_addr) == None:
				self.rxDict[node_addr] = True
		else:
			for i in range(len(node_list)):
				#self.aa = node_list
				node_list[i] = (node_list[i][0].encode(), node_list[i][1])
				if self.rxDict.get(node_list[i]) == None:
					self.rxDict[node_list[i]] = True

	def keepAliveLoop(self):
		while True:
			try:
				if len(self.rxDict): # There exists a node in the list
					nodeList = self.rxDict.keys()
					for i in range(len(nodeList)):
						keepAliveMsg = (str(MSG_PX_KEEPALIVE), None)
						self.skt.sendto(dumps(keepAliveMsg), nodeList[i], True)
						if DEBUG: print 'Send Keep-Alive-Msg to', nodeList[i]
				elif DEBUG: print 'No nodes in the list'
			except MAX_RESND_FAIL: pass
			sleep(5)

	def recvLoop(self):
		while True:
			try:
				data, addr = self.skt.recvfrom(100)
				if not data:
					sleep(0)
					continue
				msg = loads(data)
				if DEBUG: print 'Received msg:', msg, 'from', addr
				if int(msg[0].encode()) == MSG_PX_CONNECT:
					# Third Party receives a request from a new node
					if DEBUG: print 'CONNECT message from', addr
					self.notify(addr, self.getNodes())
					self.addNodes(addr, False)
				elif int(msg[0].encode()) == MSG_PX_REPLY:
					# The new node has received acknowledgement from Third Party
					if DEBUG: print 'REPLY message from', addr
					self.addNodes(addr, False)
					self.addNodes(msg[1])
				elif int(msg[0].encode()) == MSG_PX_ARRIVAL:
					# New node joins
					if DEBUG: 
						print 'ARRIVAL message from', addr
						print 'New node joins at', msg[1][0].encode()
					self.addNodes(msg[1], False)
				sleep(0)
			except NO_RECV_DATA: 
				pass
			except MAX_RESND_FAIL: 
				if DEBUG: print 'recvLoop MAX_RESND_FAIL'
				pass
			sleep(0)
			continue

	def requestPX(self, thirdParty_addr, buddy_id = None):
		msg = (str(MSG_PX_CONNECT), buddy_id)
		self.skt.sendto(dumps(msg), thirdParty_addr, True)
		if DEBUG: print 'Send a CONNECT msg to', thirdParty_addr

	def notify(self, new_node, existing_node_list):
		# Inform the requesting node of the list of existing nodes
		msg = (str(MSG_PX_REPLY), existing_node_list)
		self.skt.sendto(dumps(msg), new_node, True)
		if DEBUG: print 'notify the new node @', new_node
		# Inform the existing nodes of the new node
		if DEBUG: print existing_node_list
		if len(existing_node_list):
			for i in range(len(existing_node_list)):
				msg = (str(MSG_PX_ARRIVAL), new_node)
				self.skt.sendto(dumps(msg), existing_node_list[i], True)
				if DEBUG: print 'notify existing node @', existing_node_list[i]
		sleep(0)