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
				node_list[i] = (node_list[i][0].encode(), node_list[i][1])
				if self.rxDict.get(node_list[i]) == None:
					self.rxDict[node_list[i]] = True

	def sendKeepAliveMsg(self):
		if len(self.rxDict): # There exists a node in the list
				nodeList = self.rxDict.keys()
				for i in range(len(nodeList)):
					keepAliveMsg = (str(MSG_PX_KEEPALIVE), None)
					self.skt.sendto(dumps(keepAliveMsg), nodeList[i], True)

	def keepAliveLoop(self):
		while True:
			if DEBUG: print 'Keeping alive with', len(self.getNodes()),'nodes'
			self.sendKeepAliveMsg()
			sleep(5)

	def recvLoop(self):
		while True:
			# Check the self.skt.failed list
			if len(self.skt.failed):
				print ''
			# Check whether incoming packet in self.skt
			try:
				data, addr = self.skt.recvfrom(False)
				if not data:
					sleep(0)
					continue
				msg = loads(data)
				#if DEBUG: print 'Received msg:', msg, 'from', addr
				if int(msg[0].encode()) == MSG_PX_CONNECT:
					# Third Party receives a request from a new node
					if DEBUG: print '[Third Party]: a new node arrives at', addr
					self.notify(addr, self.getNodes())
					self.addNodes(addr, False)
				elif int(msg[0].encode()) == MSG_PX_REPLY:
					# The new node has received acknowledgement from Third Party
					if DEBUG: print '[New Node]: getting the list from Third Party @', addr
					self.addNodes(addr, False)
					if DEBUG: print '[New Node]: adding', len(msg[1]), 'existing nodes to my list'
					self.addNodes(msg[1])
					self.sendKeepAliveMsg()
				elif int(msg[0].encode()) == MSG_PX_ARRIVAL:
					# New node joins
					if DEBUG: print '[Old Node]: adding new node ', (msg[1][0].encode(), msg[1][1]), 'to my list'
					self.addNodes(msg[1], False)
					self.sendKeepAliveMsg()
				sleep(0)
			except NO_RECV_DATA: 
				pass
			sleep(0)
			continue

	def connect(self, thirdParty_addr, buddy_id = None):
		self.requestPX(thirdParty_addr, buddy_id)
		print 'Connecting'
		init_list_len = len(self.getNodes())
		init_time = time()
		while True:
			new_list_len = len(self.getNodes())
			if new_list_len > init_list_len:
				print 'Connected'
				return True
			elif (time() - init_time) > 10:
				print 'Time expired; request failed'
				return False
			else: sleep(0)

	def requestPX(self, thirdParty_addr, buddy_id = None):
		msg = (str(MSG_PX_CONNECT), buddy_id)
		self.skt.sendto(dumps(msg), thirdParty_addr, True)
		if DEBUG: print '[New Node]: connecting to Third Party', thirdParty_addr

	def notify(self, new_node, existing_node_list):
		# Inform the requesting node of the list of existing nodes
		msg = (str(MSG_PX_REPLY), existing_node_list)
		self.skt.sendto(dumps(msg), new_node, True)
		# Make sure the list does not include the new node
		try: existing_node_list.pop(existing_node_list.index(new_node))
		except ValueError: pass
		if DEBUG: 
			print '[Third Party]: telling the new node', new_node
			print '[Third Party]: my existing list is', existing_node_list
		# Inform the existing nodes of the new node
		if not len(existing_node_list): pass
		if DEBUG: 
			print '[Third Party]: telling', len(existing_node_list), 'existing nodes'
			print '[Third Party]: the new node is', new_node
		for i in range(len(existing_node_list)):
			msg = (str(MSG_PX_ARRIVAL), new_node)
			self.skt.sendto(dumps(msg), existing_node_list[i], True)
		sleep(0)