"""
A simple datacenter topology script for Mininet.
 
    [ s1 ]================================.
      ,---'       |           |           |
    [ s1r1 ]=.  [ s1r2 ]=.  [ s1r3 ]=.  [ s1r4 ]=.
    [ h1r1 ]-|  [ h1r2 ]-|  [ h1r3 ]-|  [ h1r4 ]-|
    [ h2r1 ]-|  [ h2r2 ]-|  [ h2r3 ]-|  [ h2r4 ]-|
    [ h3r1 ]-|  [ h3r2 ]-|  [ h3r3 ]-|  [ h3r4 ]-|
    [ h4r1 ]-'  [ h4r2 ]-'  [ h4r3 ]-'  [ h4r4 ]-'
"""
 
from mininet.topo import Topo
from mininet.util import irange
 
class DatacenterBasicTopo( Topo ):
    "Datacenter topology with 4 hosts per rack, 4 racks, and a root switch"
 
    # def build( self ):
    #     self.racks = []
    #     rootSwitch = self.addSwitch( 's1' )
    #     for i in irange( 1, 4 ):
    #         rack = self.buildRack( i )
    #         self.racks.append( rack )
    #         for switch in rack:
    #             self.addLink( rootSwitch, switch )
 
    # def buildRack( self, loc ):
    #     "Build a rack of hosts with a top-of-rack switch"
 
    #     dpid = ( loc * 16 ) + 1
    #     switch = self.addSwitch( 's1r%s' % loc, dpid='%x' % dpid )
 
    #     for n in irange( 1, 4 ):
    #         host = self.addHost( 'h%sr%s' % ( n, loc ) )
    #         self.addLink( switch, host )
 
    #     # Return list of top-of-rack switches for this rack
    #     return [switch]

    def recCreateTopo(self, switch_id, ip_prefix, depth):
        if depth == (self.total_depth - 1):
            # Adding Hosts to the 'TOR' switches
            for i in range(1, self.fanout+1):
                host_id = 'h%s' % self.host_count
                host_ip = ip_prefix + '.%s' % i
                self.host_count = self.host_count + 1

                # Adding the host to the topology
                host = self.addHost(host_id, ip=host_ip)
                
                # Adding the Link between the host and the parent switch
                self.addLink(self.switches_list[switch_id], host)

        else:
            for i in range(1, self.fanout+1):
                new_switch_id = switch_id * self.fanout + i
                new_ip_prefix = ip_prefix + '.%s' % i
                
                # Adding new Switch
                s_new = self.addSwitch('s%s'%new_switch_id, dpid='%x'%new_switch_id)
                self.switches_list[new_switch_id] = s_new

                # Adding new Link
                self.addLink(self.switches_list[switch_id], s_new)

                self.recCreateTopo(new_switch_id, new_ip_prefix, depth+1)

    def build(self):
        self.total_depth = 3
        self.fanout = 4
        self.switches_list = {}
        
        s0 = self.addSwitch('s0', dpid='%x'%1920)
        self.switches_list[0] = s0
        self.host_count = 1
        
        self.recCreateTopo(switch_id=0, ip_prefix='192', depth=0)

        # s1 = self.addSwitch('s0', dpid='%x'%3)
        # s2 = self.addSwitch('s1', dpid='%x'%1)
        # s3 = self.addSwitch('s2', dpid='%x'%2)
        # h1 = self.addHost('h1', ip='192.1.1.1')
        # h2 = self.addHost('h2', ip='192.1.1.2')
        # h3 = self.addHost('h3', ip='192.1.1.1')
        # h4 = self.addHost('h4', ip='192.1.1.2')
        # self.addLink(s1, s2)
        # self.addLink(s1, s3)
        # self.addLink(s2, h1)
        # self.addLink(s2, h2)
        # self.addLink(s3, h3)
        # self.addLink(s3, h4)
        
 
# Allows the file to be imported using `mn --custom <filename> --topo dcbasic`
topos = {
    'dcbasic': DatacenterBasicTopo
}