from rudp import *
from rudpException import *
from sys import argv
from json import dumps,loads

mid = ('54.248.144.148', 39951)

debug = True
NAT = 0x02000000
PX_CODE_REQUEST = '1'
PX_CODE_REPLY = '11'
PX_CODE_NOTIFY = '2'
PX_CODE_TOUCH = '3'
PX_CODE_KEEP_ALIVE = '4'
PX_CODE_ALIVE = '4'


TOUCH_MSG_INT = 1	# second
KEEP_ALIVE_MSG_INT = 5	# seconds

class PXService(object):
	def __init__(self, rudpNATSkt, pxID = None):
		self.buddyDict = dict()
		self.pxID = pxID
		self.rudpNATSkt = rudpNATSkt
		self.touchMsgToSnd = oDict()
		self.keepAliveMsgToSnd = oDict()
		self.targetMidPeer = None

	def start(self, midPeerFlag = False):
		# Default: start pxService as an ordinary peer
		# Otherwise: start pxService as a middle peer
		self.midPeerFlag = midPeerFlag
		spawn(self.keepAliveLoop)
		sleep(0)

	def stop(self):
		# kill keepAliveLoop; delete buddyDict
		pass

	def keepAliveLoop(self):
		while True:
			if debug: print 'Maintaining NAT holes with {0} buddies'.format(len(self.buddyDict.keys()))
			#if debug: print 'Buddy List: {0}'.format(self.buddyDict.keys())
			curTime = time()
			timeToWait = KEEP_ALIVE_MSG_INT
			keepAliveMsg = (PX_CODE_KEEP_ALIVE, None)
			if debug: print 'keepAliveMsgToSnd: {0}'.format(self.keepAliveMsgToSnd)
			for addr in self.keepAliveMsgToSnd.keys():
				if self.keepAliveMsgToSnd[addr][0] < curTime:
					self.rudpNATSkt.sendPXMsgto(dumps(keepAliveMsg), addr)
					count = self.keepAliveMsgToSnd[addr][1] + 1
					self.keepAliveMsgToSnd.pop(addr)
					self.keepAliveMsgToSnd[addr] = (curTime + KEEP_ALIVE_MSG_INT, count)
				else:
					timeToWait = self.keepAliveMsgToSnd[addr][0] - curTime
					break
			
			touchMsg = (PX_CODE_TOUCH, None)
			if debug: print 'touchMsgToSnd: {0}'.format(self.touchMsgToSnd)
			for addr in self.touchMsgToSnd.keys():
				if self.touchMsgToSnd[addr][0] < curTime:
					self.rudpNATSkt.sendPXMsgto(dumps(touchMsg), addr)
					count = self.touchMsgToSnd[addr][1] + 1
					self.touchMsgToSnd.pop(addr)
					if count < 5:	# send out 5 touchMsg to compensate for the unreliability of UDP
						self.touchMsgToSnd[addr] = (curTime + TOUCH_MSG_INT, count)
				else:
					timeToWait = self.touchMsgToSnd[addr][0] - curTime
					break

			sleep(timeToWait)

	def process(self, rawPXMsg, addr):
		pxMsg = loads(rawPXMsg)
		if debug: print '{0} from {1}'.format(pxMsg, addr)
		if pxMsg[0] == PX_CODE_KEEP_ALIVE:
			if debug: print 'receive KeepAliveMsg from {0}'.format(addr)
			#pxResponse = (PX_CODE_ALIVE, None)
			#self.rudpNATSkt.sendPXMsgto(dumps(pxResponse), addr)
		elif pxMsg[0] == PX_CODE_ALIVE: pass
		elif self.midPeerFlag and pxMsg[0] == PX_CODE_REQUEST:
			self.processRequestMsg(pxMsg, addr)
		elif pxMsg[0] == PX_CODE_REPLY and addr == self.targetMidPeer:
			self.processReplyMsg(pxMsg, addr)
		elif pxMsg[0] == PX_CODE_NOTIFY and addr == self.targetMidPeer:
			self.processNotifyMsg(pxMsg, addr)
		elif pxMsg[0] == PX_CODE_TOUCH:
			self.processTouchMsg(pxMsg, addr)
			if debug: print 'receive TouchMsg from {0}'.format(addr)
	
	def processRequestMsg(self, pxMsg, addr):
		self.reply(addr)
		self.notify(self.buddyDict.keys(), addr)	# only notify once?
		self.buddyDict[addr] = False
		self.keepAliveMsgToSnd[addr] = (time() + TOUCH_MSG_INT, 0)

	def processReplyMsg(self, pxMsg, addr):
		self.buddyDict[addr] = True
		self.keepAliveMsgToSnd[addr] = (time() + KEEP_ALIVE_MSG_INT, 0)
		if debug: print pxMsg[1]
		for rawAddr in pxMsg[1]:
			buddyAddr = (rawAddr[0].encode(), rawAddr[1])
			#self.touch(buddyAddr)
			self.buddyDict[buddyAddr] = False	# not verified
			self.touchMsgToSnd[buddyAddr] = (time() + TOUCH_MSG_INT, 0)
	
	def processNotifyMsg(self, pxMsg, addr):
		newPeerAddr = (pxMsg[1][0].encode(), pxMsg[1][1])
		if debug: print '[Old Peer]: new peer {0} arrives'.format(newPeerAddr)
		self.buddyDict[newPeerAddr] = False
		self.touchMsgToSnd[newPeerAddr] = (time() + TOUCH_MSG_INT, 0)

	def processTouchMsg(self, pxMsg, addr):
		try:
			#self.touchMsgToSnd.pop(addr)
			self.buddyDict[addr] = True	# buddy is verified, start sending KeepAliveMsg
			self.keepAliveMsgToSnd[addr] = (time() + KEEP_ALIVE_MSG_INT, 0)
		except KeyError: pass

	def request(self, midPeerAddr, buddyID = None):
		self.targetMidPeer = midPeerAddr
		msg = (PX_CODE_REQUEST, buddyID)
		self.rudpNATSkt.sendPXMsgto(dumps(msg), midPeerAddr)
		if debug: 
			print '[New Peer]: connecting to the middle peer {0}'.format(midPeerAddr)

	def reply(self, newPeerAddr):
		msg = (PX_CODE_REPLY, self.buddyDict.keys())
		self.rudpNATSkt.sendPXMsgto(dumps(msg), newPeerAddr)

	def notify(self, buddyAddrList, newPeerAddr):
		msg = (PX_CODE_NOTIFY, newPeerAddr)
		for buddyAddr in buddyAddrList:
			self.rudpNATSkt.sendPXMsgto(dumps(msg), buddyAddr)

	#def touch(self, buddyAddr):
	#	msg = (PX_CODE_TOUCH, None)
	#	self.rudpNATSkt.sendPXMsgto(dumps(msg), buddyAddr)

class rudpNATSocket(rudpSocket):
	def __init__(self, srcPort):
		super(rudpNATSocket, self).__init__(srcPort)
		# a peer may be involved in many PXServices as diff. roles
		self.pxServiceDict = dict()	

	def getPXService(self, id = 0):
		# only one PXService is allowed
		if self.pxServiceDict.get(id) == None:
			self.pxServiceDict[id] = PXService(self, id)
		return self.pxServiceDict[id]

	def delPXService(self, id = 0):
		self.pxServiceDict.pop(id)

	def startPXService(self, midPeerFlag = False, id = 0):
		self.pxServiceDict[id].start(midPeerFlag)

	def getBuddies(self, id = 0):
		if self.pxServiceDict[id] == None: print 'No PX service is started'
		else: return self.pxServiceDict[id].buddyDict.keys()

	def recvLoop(self):
		while True:
			data, addr = self.skt.recvfrom(MAX_DATA)
			recvPkt = decode(data)
			if recvPkt['type'] == DAT: self.proDAT(recvPkt, addr)
			elif recvPkt['type'] == ACK: self.proACK(recvPkt, addr)
			#########################################################
			elif recvPkt['type'] == NAT: self.proNAT(recvPkt, addr) #
			#########################################################
			sleep(0)

	def proNAT(self, recvPkt, addr):
		self.pxServiceDict[recvPkt['id']].process(recvPkt['data'], addr)

	def sendPXMsgto(self, pxMsg, destAddr, pxID = 0):
		self.skt.sendto( encode(rudpPacket(NAT, pxID, False, pxMsg)), destAddr)


m = rudpNATSocket(int(argv[1]))
m.getPXService()
m.startPXService(bool(argv[2]))


if argv[2] == 'True':
	print 'Middle Peer'
else:
	print 'Ordinary Peer'
	m.getPXService().request(mid)
while True: 
	sleep(0)
