NAT Traversal - Peer Exchange Demo Program

The basic scenario is as follows:
Peer R can talk to Peer A and B at the same time. But since both Peer A and B are behind a NAT device, they cannot talk to each other. With the help of Peer R, Peer A and Peer B can talk to each other finally.

Assumption:
1. EIM - Endpoint Independent Mapping: the NAT device will reuse the same mapping for the same internal host address and port number, for subsequent outgoing packets.
2. MidPeer knowledge: every new peer can talk to the middle peer, no matter whether the middle peer is behind a NAT device.

The demo program has the following components:
1. midPeer.py: with a public IP addr. (stage 1) or behind a NAT device (stage 2);

2. iniPeer.py: the initial peer within the pool;

3. newPeer.py: the new peer who wants to join the pool with the help of midPeer.py; each existing peer in the pool will follow Peer Exchange procedure, and talk to the new peer; communication within the pool is full-mesh;

4. config.py: configuration parameters for this demo program
