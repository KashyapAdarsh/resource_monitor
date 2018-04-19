import requests
import json
from threading import Thread


deployment_stats = []
containermap={"54.183.224.168":["testphoton","testphoton1"]}
cpustat = {}

def diaplay_stats():
	print deployment_stats

def get_staturl(ip, container):
#        staturl = 'http://54.183.224.168:4243/containers/testphoton/stats'
	url=[]
	url.append('http://')
	url.append(ip)
	url.append(':4243/containers/')
	url.append(container)
	url.append('/stats')
	staturl= ''.join(url)
        return staturl

def get_container_stat(ip, container):
        staturl = get_staturl(ip, container)
        payload = {'stream': 'false'}
        container_stats = {}
        r = requests.get(staturl, params=payload)

        k=[]
        k.append(ip)
        k.append(container)
        key = ''.join(k)

        stat=json.loads(r.text)
        prev_cpu = []
        try:
                prev_cpu = cpustat[key]
        except KeyError:
                prev_cpu.append(float(stat["cpu_stats"]["cpu_usage"]["total_usage"]))
                prev_cpu.append(float(stat["cpu_stats"]["system_cpu_usage"]))
                cpustat[key] = prev_cpu
                return

        container_stats["ip"] = ip
        container_stats["container_name"] = container
        container_stats["cpu_usage"] = stat["cpu_stats"]["cpu_usage"]["total_usage"]
	container_stats["mem_usage"] = (float(float(stat["memory_stats"]["usage"])/float(stat["memory_stats"]["limit"]))) * 100
#        print(container_stats)
        deployment_stats.append(container_stats)

def get_stats(containermap):
        stat_threads=[]
	deployment_stats = []
        for ip in containermap:
#                print "ip: %s , container: %s" % (ip, containermap[ip])
		for container in containermap[ip]:
			stat_threads.append( Thread(target=get_container_stat, args=(ip, container)))
#               get_container_stat(ip, containermap[ip])
        for thread in stat_threads:
                thread.start()
        for thread in stat_threads:
                thread.join()

get_stats(containermap)
get_stats(containermap)
diaplay_stats()
