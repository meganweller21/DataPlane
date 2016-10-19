'''
Created on Oct 12, 2016

@author: mwitt_000
@modified by:
Megan Weller
Ashley Bertrand
'''
import network_3
import link_3
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 1 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads
    
    #create network nodes
    #part 3, add hosts, etc. (and make sure to start the threads)
    client = network_3.Host(1)    #client has address 1
    object_L.append(client)
    server = network_3.Host(2)    #server has address 2
    object_L.append(server)
    host3 = network_3.Host(3)    #host3 has address 3
    object_L.append(host3)
    router_a = network_3.Router(name='A', intf_count=2, outf_count=2, max_queue_size=router_queue_size)
    router_b = network_3.Router(name='B', intf_count=1, outf_count=1, max_queue_size=router_queue_size)
    router_c = network_3.Router(name='C', intf_count=1, outf_count=1, max_queue_size=router_queue_size)
    router_d = network_3.Router(name='D', intf_count=2, outf_count=1, max_queue_size=router_queue_size)
    object_L.append(router_a)
    object_L.append(router_b)
    object_L.append(router_c)
    object_L.append(router_d)
    
    #create a Link Layer to keep track of links between network nodes
    link_layer = link_3.LinkLayer()
    object_L.append(link_layer)
    
    #add all the links
    #client is output, router_a is input, 50 is largest size a packet can be to be transferred over a link
    link_layer.add_link(link_3.Link(client, 0, router_a, 0, 50))   
    link_layer.add_link(link_3.Link(server, 0, router_a, 0, 50))
    link_layer.add_link(link_3.Link(router_a, 0, router_b, 0, 30))  #for part 2, change mtu to 30
    link_layer.add_link(link_3.Link(router_a, 0, router_c, 0, 30))
    link_layer.add_link(link_3.Link(router_b, 0, router_d, 0, 30))
    link_layer.add_link(link_3.Link(router_c, 0, router_d, 0, 30))
    link_layer.add_link(link_3.Link(router_d, 0, host3, 0, 30))
    
    
    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client.__str__(), target=client.run))
    thread_L.append(threading.Thread(name=server.__str__(), target=server.run))
    thread_L.append(threading.Thread(name=host3.__str__(), target=host3.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))
    
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events
    #client transmits 3 packets
    #part 1
    #send message >= 80 characters
    #modify udt_send to break larger data into different packets
    for i in range(3):
        client.udt_send(2, 'Adding characters so length is 80.*********************************Sample data %d' % i) #sending data to host 2
    
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically
