from rudp import *
from rudpException import *
from sys import argv
from json import dumps,loads

mid = ('54.248.144.148', 39951)

debug = True
NAT = 0x02000000
PX_CODE_KEEP_ALIVE = '1'
PX_CODE_ALIVE = '11'
PX_CODE_REQUEST = '2'
PX_CODE_REPLY = '22'
PX_CODE_NOTIFY = '3'
PX_CODE_TOUCH = '4'


class PXService(object):
	def __init__(self, rudpNATSkt, pxID = None):
		self.buddyDict = dict()
		self.pxID = pxID
		self.rudpNATSkt = rudpNATSkt

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
			if debug: 
				print 'Maintaining NAT holes with {0} buddies'.format(len(self.buddyDict.keys()))
			if debug: print 'Buddy List: {0}'.format(self.buddyDict.keys())
			for buddyAddr in self.buddyDict.keys():
				msg = (PX_CODE_KEEP_ALIVE, None)
				self.rudpNATSkt.sendPXMsgto(dumps(msg), buddyAddr)
				#if debug: print 'send KeepAliveMsg to {0}'.format(buddyAddr)
			sleep(5)

	def process(self, rawPXMsg, addr):
		#if debug: print '{0} from {1}'.format(rawPXMsg, addr)
		pxMsg = loads(rawPXMsg)
		if pxMsg[0] == PX_CODE_KEEP_ALIVE:
			if debug: print 'receive KeepAliveMsg from {0}'.format(addr)
			pxResponse = (PX_CODE_ALIVE, None)
			self.rudpNATSkt.sendPXMsgto(dumps(pxResponse), addr)
		elif pxMsg[0] == PX_CODE_ALIVE: pass
		elif pxMsg[0] == PX_CODE_REQUEST:
			# Send my existing buddy list to the new peer
			self.reply(addr)
			# Notify existing buddies of the new peer
			self.notify(self.buddyDict.keys(), addr)
			# Add the new peer to my buddy list
			self.buddyDict[addr] = True
			pass
		elif pxMsg[0] == PX_CODE_REPLY:
			# Add the middle peer to my buddy list
			self.buddyDict[addr] = True
			# Punch holes for existing buddies
			if debug: print pxMsg[1] # e.g. [[u'137.189.98.10', 39951]]
			for item in pxMsg[1]:
				buddyAddr =  (item[0].encode(), item[1])
				self.touch(buddyAddr)
				self.buddyDict[buddyAddr] = True
		elif pxMsg[0] == PX_CODE_NOTIFY:
			newPeerAddr = (pxMsg[1][0].encode(), pxMsg[1][1])
			if debug: print '[Old Peer]: new peer {0} arrives'.format(newPeerAddr)
			self.touch(newPeerAddr)
			self.buddyDict[newPeerAddr] = True
		elif pxMsg[0] == PX_CODE_TOUCH:
			pass

	def request(self, midPeerAddr, buddyID = None):
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

	def touch(self, buddyAddr):
		msg = (PX_CODE_TOUCH, None)
		self.rudpNATSkt.sendPXMsgto(dumps(msg), buddyAddr)

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

print argv

if argv[2] == 'True':
	print 'Middle Peer'
else:
	print 'Ordinary Peer'
	m.getPXService().request(mid)
while True: 
	sleep(0)