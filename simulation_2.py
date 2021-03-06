'''
Created on Oct 12, 2016

@author: mwitt_000
@modified by:
Megan Weller
Ashley Bertrand
'''
import network_2
import link_2
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 1 #give the network sufficient time to transfer all packets before quitting
mtu = 30

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network nodes
    #part 3, add hosts, etc. (and make sure to start the threads)
    client = network_2.Host(1)    #client has address 1
    object_L.append(client)
    server = network_2.Host(2)    #server has address 2
    object_L.append(server)
    router_a = network_2.Router(name='A', intf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_a)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_2.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    #client is output, router_a is input, 50 is largest size a packet can be to be transferred over a link
    link_layer.add_link(link_2.Link(client, 0, router_a, 0, 50))
    link_layer.add_link(link_2.Link(router_a, 0, server, 0, mtu))   #for part 2, change mtu to 30
    
    
    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client.__str__(), target=client.run))
    thread_L.append(threading.Thread(name=server.__str__(), target=server.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events
    #client transmits 3 packets
    #part 1
    #send message >= 80 characters
    #modify udt_send to break larger data into different packets
    for i in range(3):
        client.udt_send(2, 'Adding characters so length is 80.*********************************Sample data %d' % i, mtu) #sending data to host 2
    
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically
