#!/usr/bin/env python

from rudp import *
from rudpException import *
from ip import *
from sys import argv
from json import dumps,loads
import curses

mid = ('54.248.144.148', 39951)
debug = False

NAT = 0x02000000
NAT_CODE_REQUEST = '1'
NAT_CODE_REPLY = '11'
NAT_CODE_NOTIFY = '2'
NAT_CODE_TOUCH = '3'
NAT_CODE_KEEP_ALIVE = '4'

TOUCH_MSG_INT = 1	# second
KEEP_ALIVE_MSG_INT = 3	# seconds

class natStat(object):
	def __init__(self):
		self.lastKeepAliveMsgRcv = dict()


class natService(object):
	def __init__(self, rudpNATSkt, asid = None):
		self.buddyDict = dict()
		self.asid = asid 	# asid: appSocket id
		self.rudpNATSkt = rudpNATSkt
		self.touchMsgToSnd = oDict()
		self.keepAliveMsgToSnd = oDict()
		self.targetMidPeer = None
		self.stat = natStat()
		ip = IP.Instance()
		try: self.myip = ip.myip
		except Exception: self.myip = ''
		try: self.myip2 = ip.myip2
		except Exception: self.myip2 = ''
		self.port = rudpNATSkt.skt.getsockname()[1]

	def start(self, midPeerFlag):
		self.midPeerFlag = midPeerFlag
		natThread = spawn(self.sendNATMsgLoop)
		sleep(0)

	def stop(self):
		natThread.kill()
		self.keepAliveMsgToSnd = None
		self.touchMsgToSnd = None

	def sendNATMsgLoop(self):
		while True:
	#		if debug: print 'Maintaining NAT holes with {0} buddies'.format(len(self.buddyDict.keys()))
			curTime = time()
			timeToWait = KEEP_ALIVE_MSG_INT
			keepAliveMsg = (NAT_CODE_KEEP_ALIVE, None)
	#		if debug: print 'keepAliveMsgToSnd: {0}'.format(self.keepAliveMsgToSnd)
			for addr in self.keepAliveMsgToSnd.keys():
				if self.keepAliveMsgToSnd[addr][0] < curTime:
					self.rudpNATSkt.sendNATMsgto(dumps(keepAliveMsg), addr)
					count = self.keepAliveMsgToSnd[addr][1] + 1
					self.keepAliveMsgToSnd.pop(addr)
					self.keepAliveMsgToSnd[addr] = (curTime + KEEP_ALIVE_MSG_INT, count)
				else:
					timeToWait = self.keepAliveMsgToSnd[addr][0] - curTime
					break
			
			touchMsg = (NAT_CODE_TOUCH, None)
	#		if debug: print 'touchMsgToSnd: {0}'.format(self.touchMsgToSnd)
			for addr in self.touchMsgToSnd.keys():
				if self.touchMsgToSnd[addr][0] < curTime:
					self.rudpNATSkt.sendNATMsgto(dumps(touchMsg), addr)
					count = self.touchMsgToSnd[addr][1] + 1
					self.touchMsgToSnd.pop(addr)
					if count < 5:	# send out 5 touchMsg to compensate for the unreliability of UDP
						self.touchMsgToSnd[addr] = (curTime + TOUCH_MSG_INT, count)
				else:
					timeToWait = self.touchMsgToSnd[addr][0] - curTime
					break
			sleep(timeToWait)

	def process(self, rawNATMsg, addr):
		natMsg = loads(rawNATMsg)
		if natMsg[0] == NAT_CODE_KEEP_ALIVE:
	#		if debug: print 'receive KeepAliveMsg from {0}'.format(addr)
			self.stat.lastKeepAliveMsgRcv[addr] = time()
		elif self.midPeerFlag and natMsg[0] == NAT_CODE_REQUEST:
			self.processRequestMsg(natMsg, addr)
		elif natMsg[0] == NAT_CODE_REPLY and addr == self.targetMidPeer:
			self.processReplyMsg(natMsg, addr)
		elif natMsg[0] == NAT_CODE_NOTIFY and addr == self.targetMidPeer:
			self.processNotifyMsg(natMsg, addr)
		elif natMsg[0] == NAT_CODE_TOUCH:
			self.processTouchMsg(natMsg, addr)
	#		if debug: print 'receive TouchMsg from {0}'.format(addr)
	
	def processRequestMsg(self, natMsg, addr):
		self.reply(addr)
		self.notify(self.buddyDict.keys(), addr)	# only notify once?
		self.buddyDict[addr] = True
		self.keepAliveMsgToSnd[addr] = (time() + TOUCH_MSG_INT, 0)

	def processReplyMsg(self, natMsg, addr):
		self.buddyDict[addr] = True
		self.keepAliveMsgToSnd[addr] = (time() + KEEP_ALIVE_MSG_INT, 0)
		if debug: print natMsg[1]
		for rawAddr in natMsg[1]:
			buddyAddr = (rawAddr[0].encode(), rawAddr[1])
			#if buddyAddr[0]!=self.myip and buddyAddr[1]!=self.port:
			self.buddyDict[buddyAddr] = False# not verified
			self.touchMsgToSnd[buddyAddr] = (time() + TOUCH_MSG_INT, 0)
	
	def processNotifyMsg(self, natMsg, addr):
		newPeerAddr = (natMsg[1][0].encode(), natMsg[1][1])
	#	if debug: print '[Old Peer]: new peer {0} arrives'.format(newPeerAddr)
		self.buddyDict[newPeerAddr] = False
		self.touchMsgToSnd[newPeerAddr] = (time() + TOUCH_MSG_INT, 0)

	def processTouchMsg(self, natMsg, addr):
#		try:
		self.touchMsgToSnd.pop(addr)
		self.buddyDict[addr] = True	# buddy is verified, start sending KeepAliveMsg
		self.keepAliveMsgToSnd[addr] = (time() + KEEP_ALIVE_MSG_INT, 0)
#		except KeyError: print 'Error'

	def request(self, midPeerAddr, buddyID = None):
		self.targetMidPeer = midPeerAddr
		msg = (NAT_CODE_REQUEST, buddyID, (self.myip2, self.port))
		self.rudpNATSkt.sendNATMsgto(dumps(msg), midPeerAddr)
	#	if debug: print '[New Peer]: connecting to the middle peer {0}'.format(midPeerAddr)

	def reply(self, newPeerAddr):
		msg = (NAT_CODE_REPLY, self.buddyDict.keys())
		self.rudpNATSkt.sendNATMsgto(dumps(msg), newPeerAddr)

	def notify(self, buddyAddrList, newPeerAddr):
		msg = (NAT_CODE_NOTIFY, newPeerAddr)
		for buddyAddr in buddyAddrList:
			self.rudpNATSkt.sendNATMsgto(dumps(msg), buddyAddr)


class rudpNATSocket(rudpSocket):
	def __init__(self, srcPort):
		super(rudpNATSocket, self).__init__(srcPort)
		self.natServiceDict = dict()	

	def getNATService(self, asid = 0):
		if self.natServiceDict.get(asid) == None:
			self.natServiceDict[asid] = natService(self, asid)
		return self.natServiceDict[asid]

	def delNATService(self, asid = 0):
		self.natServiceDict.pop(asid)

	def startNATService(self, midPeerFlag = False, asid = 0):
		self.natServiceDict[asid].start(midPeerFlag)

	def getBuddies(self, asid = 0):
		if self.natServiceDict[asid] == None: print 'No NAT service is started'
		else: return self.natServiceDict[asid].buddyDict.keys()

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

	def sendto(self, string, destAddr, isReliable = False):
		super(rudpNATSocket, self).sendto(string, destAddr, isReliable)
		# If data packets are sent to a destination,
		# renew the time of next to-be-send KeepAliveMsg
		if keepAliveMsgToSnd.get(destAddr) != None:
			count = self.keepAliveMsgToSnd[addr][1] + 1
			self.keepAliveMsgToSnd.pop(addr)
			self.keepAliveMsgToSnd[addr] = (curTime + KEEP_ALIVE_MSG_INT, count)

	def proNAT(self, recvPkt, addr):
	#	print recvPkt, addr
		self.natServiceDict[recvPkt['id']].process(recvPkt['data'], addr)

	def sendNATMsgto(self, natMsg, destAddr, asid = 0):
		self.skt.sendto( encode(rudpPacket(NAT, asid, False, natMsg)), destAddr)

def pbar(window, nat):
	while True:
		if nat.midPeerFlag: window.addstr(2, 5, 'Peer Role: Middle Peer/Sender')
		else: window.addstr(2, 5, 'Peer Role: Ordinary Peer/Receiver')
		window.addstr(3, 5, 'Public IP: {0}, Private IP: {1}, Port: {2}'.format(nat.myip, nat.myip2, nat.port))
		buddyList = nat.buddyDict.keys()
		window.addstr(5, 5, 'Buddy Count: {0}'.format(len(buddyList)))
		for i in range(min( 5, len(buddyList))):
			window.addstr( 6 + 3*i, 5, 'Buddy [{0}]: {1}, Status: {2}'.format( i, buddyList[i], nat.buddyDict[buddyList[i]]))
			nextKeepAliveMsgToSnd = nat.keepAliveMsgToSnd.get(buddyList[i])
			if nextKeepAliveMsgToSnd:
				window.addstr( 7 + 3*i, 5, '      Next KeepAliveMsg Snd: {0}'.format(nextKeepAliveMsgToSnd))
				window.addstr( 8 + 3*i, 5, '      Last KeepAliveMsg Rcv: {0}'.format(nat.stat.lastKeepAliveMsgRcv.get(buddyList[i])))
		if len(buddyList) >= 6:
			window.addstr( 17, 5, '...')
			window.addstr( 18, 5, '(top 10 entries are shown)')
		window.addstr( 19, 5, 'KeepAliveMsgToSnd: {0} entries'.format(len(nat.keepAliveMsgToSnd.keys())))
		window.addstr( 20,5, 'TouchMsgToSnd: {0} entries'.format(len(nat.touchMsgToSnd.keys())))
		window.border()
		window.refresh()
		sleep(0.5) 


if __name__ == "__main__":
	m = rudpNATSocket(int(argv[1]))
	m.getNATService()
	if argv[2] == 'True':
		m.startNATService(True)
	else:
		m.startNATService(False)

	if argv[2] == 'False':
		m.getNATService().request(mid)

	curses.wrapper(pbar, m.getNATService())




