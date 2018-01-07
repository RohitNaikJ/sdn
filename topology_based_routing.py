# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This component is for use with the OpenFlow tutorial.

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()



class Tutorial (object):
  """
  A Tutorial object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection
    self.fanout = 2

    print('Switch with DPID {} connected to the controller'.format(connection.dpid))
    # print((connection.ID), connection.eth_addr)

    # This binds our PacketIn event listener
    connection.addListeners(self)

    # Use this table to keep track of which ethernet address is on
    # which switch port (keys are MACs, values are ports).
    self.mac_to_port = {}


  def resend_packet (self, packet_in, out_port):
    """
    Instructs the switch to resend a packet that it had sent to us.
    "packet_in" is the ofp_packet_in object the switch had sent to the
    controller due to a table-miss.
    """
    msg = of.ofp_packet_out()
    msg.data = packet_in

    # Add an action to send to the specified port
    action = of.ofp_action_output(port = out_port)
    msg.actions.append(action)

    # Send message to switch
    self.connection.send(msg)


  def act_like_hub (self, packet, packet_in):
    """
    Implement hub-like behavior -- send all packets to all ports besides
    the input port.
    """

    # We want to output to all ports -- we do that using the special
    # OFPP_ALL port as the output port.  (We could have also used
    # OFPP_FLOOD.)
    self.resend_packet(packet_in, of.OFPP_ALL)

    # Note that if we didn't get a valid buffer_id, a slightly better
    # implementation would check that we got the full data before
    # sending it (len(packet_in.data) should be == packet_in.total_len)).


  def getNetPart(self, layer):
	dpid = self.connection.dpid
	S = (pow(self.fanout, layer) - 1) / (self.fanout - 1)
	K = dpid - S + 1
	net = [1 for i in range(layer)]
	count = 1
	while count < K:
		count = count + 1
		if net[-1] < self.fanout:
			net[-1] = net[-1] + 1
		else:
			index = len(net) - 1
			while True:
				if net[index] < self.fanout:
					net[index] = net[index] + 1
					break
				else:
					net[index] = 1
					index = index - 1

	# now net has the IP address match for the gien dpid
	print('DPID: {}, layer: {}, netPart: {}'.format(dpid, layer, net))
	return net

  def topo_forwarding(self, packet, packet_in):
  	if hasattr(packet.next, 'dstip') and len(str(packet.next.dstip).split('.')) == 4 and str(packet.next.dstip).split('.')[0] != '255' and str(packet.next.dstip).split('.')[1] != '255':
  		# print('Destination IP: {}, will forward it to port: {}'.format(str(packet.next.dstip), int(str(packet.next.dstip).split('.')[1])))

  		if self.connection.dpid > 1000:
  			msg = of.ofp_flow_mod()
  			msg.match = of.ofp_match()
  			msg.match.dl_type = 0x800
 			ip = str(packet.next.dstip).split('.')
			ip[2] = '0'
			ip[3] = '0'
			port = int(ip[1])
			new_ip = '.'.join(ip) + '/%s' % 16

			msg.match.nw_dst = new_ip
			msg.buffer_id = packet_in.buffer_id
			msg.actions.append(of.ofp_action_output(port = port))
			self.connection.send(msg)
			print('FLowMod sent at DPID: {} with DESTIP: {} and port forwarding to: {}'.format(self.connection.dpid, new_ip, port))

		else:
			k = 0
			tmp = self.connection.dpid
			while pow(self.fanout, k) <= tmp:
				tmp = tmp - pow(self.fanout, k)
				k = k + 1

			netPart = self.getNetPart(k)
			netPart = [str(i) for i in netPart]

			ip = str(packet.next.dstip).split('.')

			print('dstip of packet: {}, netPart of the switch:{}'.format(ip, netPart))
			flag = True
			for i in range(len(netPart)):
				if netPart[i] != ip[i+1]:
					flag = False
					break

			# Deciding whether it's a wildcard flow or not
			if flag == False:
				# wildcard flow
				if len(netPart) == 1:
					netPart.insert(0, '192')
					netPart.append('0')
					netPart.append('0')
					for i in range(self.fanout):
						netPart[2] = str(i+1)
						msg = of.ofp_flow_mod()
				  		msg.match = of.ofp_match()
				  		msg.match.dl_type = 0x800
				  		msg.match.nw_dst = '.'.join(netPart) + '/' + str(24)
				  		msg.priority = 10
				  		msg.buffer_id = None
				  		msg.actions.append(of.ofp_action_output(port = i+2))
				  		self.connection.send(msg)

				elif len(netPart) == 2:
					netPart.insert(0, '192')
					netPart.append('0')
					for i in range(self.fanout):
						netPart[3] = str(i+1)
						msg = of.ofp_flow_mod()
				  		msg.match = of.ofp_match()
				  		msg.match.dl_type = 0x800
				  		msg.match.nw_dst = '.'.join(netPart) + '/' + str(32)
				  		msg.priority = 10
				  		msg.buffer_id = None
				  		msg.actions.append(of.ofp_action_output(port = i+2))
				  		self.connection.send(msg)

				msg = of.ofp_flow_mod()
		  		msg.match = of.ofp_match()
		  		msg.match.dl_type = 0x800
		  		msg.match.nw_dst = None
		  		msg.priority = 1
		  		msg.buffer_id = packet_in.buffer_id
		  		msg.actions.append(of.ofp_action_output(port = 1))
		  		self.connection.send(msg)
		  		print('Wildcard mod sent at switch with DPID: {} for destination IP: {}'
		  			.format(self.connection.dpid, str(packet.next.dstip)))

			else:
				# Not a wildcard flow. Setting more specific match requirements
				if len(netPart) == 1:
					# 192.1.X.X
					ip[3] = '0'
					netSize = 24
					port = int(ip[2])+1

				elif len(netPart) == 2:
					# 192.1.1.X
					netSize = 32
					port = int(ip[3])+1

				new_ip = '.'.join(ip) + '/' + str(netSize)

				msg = of.ofp_flow_mod()
		  		msg.match = of.ofp_match()
		  		msg.match.dl_type = 0x800
		  		msg.match.nw_dst = new_ip
		  		msg.priority = 10
		  		msg.buffer_id = packet_in.buffer_id
		  		msg.actions.append(of.ofp_action_output(port = port))
		  		self.connection.send(msg)
		  		print('FLOW MOD set at switch with DPID: {}, for packet_IP:{}, to port: {}, match_ip: {}'
		  			.format(self.connection.dpid, ip, port, new_ip))

  	else:
  		self.resend_packet(packet_in, of.OFPP_ALL)


  	# 	msg = of.ofp_flow_mod()
  	# 	msg.match = of.ofp_match()
  	# 	msg.match.dl_type = 0x800

  	# 	ip = str(packet.next.dstip).split('.')
  	# 	new_ip = ''
  	# 	for i in range(networkLen, 4):
  	# 		ip[i] = '0'
  	# 	new_ip = '.'.join(ip) + '/' + str(networkLen * 8)
  	# 	msg.match.nw_dst = new_ip

  	# 	msg.buffer_id = packet_in.buffer_id

  	# 	msg.actions.append( of.ofp_action_output( port = int(str(packet.next.dstip).split('.')[1]) ) )
  	# 	self.connection.send(msg)
  	# 	print('SENT FLOW_MOD with nw_dst: {}'.format(new_ip))


  def act_like_switch (self, packet, packet_in):
    """
    Implement switch-like behavior.
    """

    # """ # DELETE THIS LINE TO START WORKING ON THIS (AND THE ONE BELOW!) #

    # Here's some psuedocode to start you off implementing a learning
    # switch.  You'll need to rewrite it as real Python code.

    # Learn the port for the source MAC
    self.mac_to_port[str(packet.src)] = packet_in.in_port

    if str(packet.dst) in self.mac_to_port:
      # Send packet out the associated port
      # self.resend_packet(packet_in, self.mac_to_port[str(packet.dst)])

      # Once you have the above working, try pushing a flow entry
      # instead of resending the packet (comment out the above and
      # uncomment and complete the below.)

      log.debug("Installing flow...")
      # Maybe the log statement should have source/destination/port?

      msg = of.ofp_flow_mod()
      
      ## Set fields to match received packet
      # msg.match = of.ofp_match.from_packet(packet)
      msg.match = of.ofp_match()
      msg.match.dl_dst = packet.dst
      
      #<Set other fields of flow_mod (timeouts? buffer_id?) >
      msg.buffer_id = packet_in.buffer_id

      #<Add an output action, and send -- similar to resend_packet() >
      msg.actions.append(of.ofp_action_output(port = self.mac_to_port[str(packet.dst)]))
      self.connection.send(msg)

    else:
      # Flood the packet out everything but the input port
      # This part looks familiar, right?
      self.resend_packet(packet_in, of.OFPP_ALL)

    # """ # DELETE THIS LINE TO START WORKING ON THIS #

  def printFields(self, packet, packet_in):
  	# print(dir(packet), dir(packet_in))	
  	print("Incoming portNo: {}\tMAC: {}".format(packet_in.in_port, str(packet.src)))
  	print("Destination MAC: {} of type: {}".format(packet.dst, type(packet.dst)))	
  	# print(type(packet), type(packet_in))
  	print('SRCIP')
  	if hasattr(packet.next, 'srcip'):
  		print(packet.next.srcip, str(packet.next.srcip), type(packet.next.srcip))
  	print('DSTIP')
  	if hasattr(packet.next, 'dstip'):
  		print(packet.next.dstip, str(packet.next.dstip), type(packet.next.dstip))
  	# print('Destination IP from .find("ipv4"): {}'.format(packet.find('ipv4')))


  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """

    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return

    # log.debug("Rohit: %s"%str(packet))

    packet_in = event.ofp # The actual ofp_packet_in message.

    # function which prints fields regarding packets necessary for being able to define act_like_switch() method
    # self.printFields(packet, packet_in)

    # Comment out the following line and uncomment the one after
    # when starting the exercise.
    # self.act_like_hub(packet, packet_in)
    # self.act_like_switch(packet, packet_in)

    # Our approach of Packet forwarding based on IP
    self.topo_forwarding(packet, packet_in)

def launch ():
  """
  Starts the component
  """
  def start_switch (event):
    log.debug("Controlling %s" % (event.connection,))
    Tutorial(event.connection)
  core.openflow.addListenerByName("ConnectionUp", start_switch)
