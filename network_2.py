'''
Created on Oct 12, 2016

@author: mwitt_000
@modified by:
Megan Weller
Ashley Bertrand
'''
import queue
import threading
import math


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
#part 2, implement segmentation (packet will be too large to fit through second link)
#part 3, extend so you can tell where a packet is coming from
class NetworkPacket:
    ## packet encoding lengths 
    full_length = 8
    dst_addr_S_length = 5
    fragflag_length = 1
    length_length = 2
    
    ##@param dst_addr: address of the destination host
    # @param length: length of the data coming in
    # @param fragflag: indication if the packet is ending
    # @param data_S: packet payload
    def __init__(self, dst_addr, length, fragflag, data_S):
        self.dst_addr = dst_addr
        self.length = length
        self.fragflag = fragflag
        self.data_S = data_S
    
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        #Add a zero if it is not full length
        length_S = str(self.length).zfill(self.length_length)
        byte_S += length_S
        byte_S += str(self.fragflag)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        length_s = int(byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.length_length])
        fragflag = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.length_length : NetworkPacket.dst_addr_S_length + NetworkPacket.length_length + NetworkPacket.fragflag_length])
        data_S = byte_S[NetworkPacket.full_length : ]
        return self(dst_addr, length_s, fragflag, data_S)
    

## Implements a network host for receiving and transmitting data
class Host:
    
    packet_data = ''
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    # @param mtu: mtu of the host
    def udt_send(self, dst_addr, data_S, mtu):

        #array for packets to send
        packets = []
        #length- Full length of the data
        length_d = len(data_S)
        start = 0
        end = 0
        
        while (length_d > 0):
            #If the length + the full address is greater than the mtu, it must be split
            if (length_d + NetworkPacket.full_length > mtu):
                #data_l is the length we will send minus the full address
                data_l = mtu - NetworkPacket.full_length
                end+=data_l
                p = NetworkPacket(dst_addr, data_l, 1, data_S[start:end])
                packets.append(p)
                start+=data_l
                length_d-=data_l
            else:
                #Must be the end of the packet, send fragflag of 0
                p = NetworkPacket(dst_addr, length_d, 0, data_S[start:])
                length_d= 0
                packets.append(p)

        #Send all packets
        for p in packets:
            self.out_intf_L[0].put(p.to_byte_S()) 
            print('%s: sending packet "%s"' % (self, p))
        
        
    ## receive packet from the network layer
    #part 2, put packets back together (based on packet's segmentation fields) before printing them out
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            
            p = NetworkPacket.from_byte_S(pkt_S)

            #If the fragflag is 1, not complete
            if p.fragflag == 1:
                self.packet_data += p.data_S
            else:  
                #Once fragflag is 0, end of packet therefore print the packet 
                self.packet_data += p.data_S
                print('%s: received packet "%s"' % (self, self.packet_data))
                #reset packet_data
                self.packet_data = ''
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    #part 3, implement routing table
                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    self.out_intf_L[i].put(p.to_byte_S(), True)
                    print('%s: forwarding packet "%s" from interface %d to %d' % (self, p, i, i))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return
           
