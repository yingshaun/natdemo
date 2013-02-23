NAT Traversal - Peer Exchange Demo Program

The basic scenario is as follows:
Peer R can talk to Peer A and B at the same time. But since both Peer A and B are behind a NAT device, they cannot talk to each other. With the help of Peer R, Peer A and Peer B can talk to each other finally.

Assumption:
1. EIM - Endpoint Independent Mapping: the NAT device will reuse the same mapping for the same internal host address and port number, for subsequent outgoing packets.
2. MidPeer knowledge: both peers can talk to the middle peer regardless of the presence of NAT devices for the midPeer.

The demo program has the following components:
1. midPeer.py: with a public IP addr. (stage 1) or behind a NAT device (stage 2);
2. peer.py: a peer behind a NAT device;
3. config.py: configuration parameters for this demo program;

midPeer.start()
1. wait(): wait for the connection of the 1st peer;
2. wait(): wait for the connection of the 2nd peer;
3. introduce(): exchange the peers' addresses, and tell both peers;

peer.start()
1. connect(midPeer_addr): connects to the midPeer;
2. get(): get the target peer's address from the midPeer;
3. touch(): send a packet to the target peer reliably;
