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
    full_length = 9
    dst_addr_S_length = 5
    fragflag_length = 1
    length_length = 2
    offset_length = 1
    source = ""
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, length, fragflag, offset, data_S, source):
        self.dst_addr = dst_addr
        self.data_S = data_S
        self.length = length
        self.fragflag = fragflag
        self.offset = offset
        self.source = source
    
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
        byte_S += str(self.offset)
        byte_S += self.data_S
        return byte_S

    def get_source(self):
        return self.source
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length])
        length_s = int(byte_S[NetworkPacket.dst_addr_S_length : NetworkPacket.dst_addr_S_length + NetworkPacket.length_length])
        fragflag = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.length_length : NetworkPacket.dst_addr_S_length + NetworkPacket.length_length + NetworkPacket.fragflag_length])
        offset = int(byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.fragflag_length + NetworkPacket.length_length : NetworkPacket.dst_addr_S_length + NetworkPacket.length_length + NetworkPacket.fragflag_length + NetworkPacket.offset_length])
        data_S = byte_S[NetworkPacket.dst_addr_S_length + NetworkPacket.fragflag_length + NetworkPacket.length_length + NetworkPacket.offset_length : ]
        source = self.get_source(self)
        return self(dst_addr, length_s, fragflag, offset, data_S, source)
    

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
    def udt_send(self, dst_addr, data_S):
        #split large data into 2 packets
        first_data, second_data = data_S[:len(data_S)//2], data_S[len(data_S)//2:]

        #Offset must be a factor of 8, the full address is 9 characters
        #We start by giving 16 bytes of the data, 16 in the second, and 8 bytes left over
        p1 = NetworkPacket(dst_addr, 16, 1, 0, first_data[:16], "client")
        p2 = NetworkPacket(dst_addr, 16, 1, int(16/8), first_data[16:32], "source")
        p3 = NetworkPacket(dst_addr, 8, 0, int(24/8), first_data[32:], "client")

        p4 = NetworkPacket(dst_addr, 16, 1, 0, second_data[:16], "source")
        p5 = NetworkPacket(dst_addr, 16, 1, int(16/8), second_data[16:32], "client")
        p6 = NetworkPacket(dst_addr, 8, 0, int(24/8), second_data[32:], "source")

        #send packets always enqueued successfully
        self.out_intf_L[0].put(p1.to_byte_S()) 
        self.out_intf_L[0].put(p2.to_byte_S())
        self.out_intf_L[0].put(p3.to_byte_S())
        self.out_intf_L[0].put(p4.to_byte_S())
        self.out_intf_L[0].put(p5.to_byte_S())
        self.out_intf_L[0].put(p6.to_byte_S())

        print('%s: sending packet "%s"' % (self, p1))
        print('%s: sending packet "%s"' % (self, p2))
        print('%s: sending packet "%s"' % (self, p3))
        print('%s: sending packet "%s"' % (self, p4))
        print('%s: sending packet "%s"' % (self, p5))
        print('%s: sending packet "%s"' % (self, p6))
        
        
    ## receive packet from the network layer
    #part 2, put packets back together (based on packet's segmentation fields) before printing them out
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            #Get the fragment flag... could use the offset?
            fragflag = int (pkt_S[NetworkPacket.dst_addr_S_length + NetworkPacket.length_length : NetworkPacket.dst_addr_S_length + NetworkPacket.fragflag_length +NetworkPacket.length_length])

            #If the fragflag is 1, not complete
            if fragflag == 1:
                self.packet_data += pkt_S[NetworkPacket.dst_addr_S_length + NetworkPacket.length_length + NetworkPacket.fragflag_length + NetworkPacket.offset_length :]
            else:  
                #Once fragflag is 0, end of packet therefore print the packet 
                self.packet_data += pkt_S[NetworkPacket.dst_addr_S_length + NetworkPacket.length_length + NetworkPacket.fragflag_length + NetworkPacket.offset_length :]
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
    # @param intf_count: the number of input interfaces 
    # @param outf_count: the number of output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, outf_count, max_queue_size, routing_table):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(outf_count)]
        self.routing_table = routing_table

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
                    print("Source:", p.get_source())
                    if (p.get_source() == "client") :
                        route = self.routing_table[0]
                        print("ROUTE\n\n\n", route)
                    elif (p.get_source() == "server"):
                        route = self.routing_table[1]
                        print("ROUTE\n\n\n", route)
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
           
