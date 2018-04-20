#!/usr/bin/env python
from flask import Flask, jsonify, render_template, request
import docker
import requests
import os
import json
from threading import Thread
import logging
import copy
from time import sleep
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
template_dir = os.path.join(top_dir, 'templates')

static_dir = os.path.join(top_dir, 'static')

ip_container=[]
app = Flask(__name__, static_url_path="", static_folder="../static", template_folder='../templates')

cpustat = {}
containermap={}

# logger = logging.getLogger('myapp')
# hdlr = logging.FileHandler('./myapp.log')
# formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# hdlr.setFormatter(formatter)
# logger.addHandler(hdlr) 
# logger.setLevel(logging.WARNING)

@app.route('/', methods = ["GET", "POST"])
def landing():
    return render_template('index.html')


@app.route('/start_containers', methods = ["GET", "POST"])
def start_containers():
    """
    Gets the list of host and container names and starts them
    """
    global ip_container
    logs = []
    f = request.form['clusterConfigArea'].split('\n')
    logging.info(f)
    ip_container=copy.deepcopy(f)
    logging.info("Value of - " + str(ip_container))

    if not f:
        return "Config file not found!!"
    args = {'Image': 'ubuntu'}
    for configline in f:
        logline = ""
        url, container_name = configline.strip().split(' ')
        if "http://" not in url:
            url = "http://" + url

        # For each of the entries, do-
        # 1. Create an image
        # 2. Create a container
        # 3. Start the container

        #### 1. Create an image
        image_name = "progrium/stress"
        img_url = url + "/images/create?fromImage=" + image_name + "&tag=latest"
        # response = requests.post(img_url)
        okay = True
        if okay:
            logline = "Created the image - " + image_name
            logging.info(logline)

            #### 2. Create the container.
            #### Delete all the stopped containers before creating to avoid conflict
            del_container = url + "/containers/prune"
            response = requests.post(del_container)
            container_url = url + "/containers/create?name=" + container_name
            response = requests.post(container_url, json= {"Image": image_name, "Cmd": ["--cpu", "2",  "--io", "1", "--vm", "2",  "--vm-bytes", "256M"]})
            if response.status_code == 201:
                container_id = response.json()["Id"]                
                logline = "Created the container with Id- " + container_id
                logging.info(logline)
                
                
                #### 3. Start the container
                container_start_url = url + "/containers/" + container_id + "/start"
                response = requests.post(container_start_url)
                if response.status_code == 204:
                    ### All is well
                    logline = "Started the container - " + container_name
                    logging.info(logline)
                else:
                    logline = "Couldn't start container with id - " + container_start_url + " Response code - " + str(response.status_code)
                    logging.info(logline)           
            else:
                logline = "Container creation failed for - " + container_url + " Response code - " + str(response.status_code)
                logging.info(logline)             
        else:
            logline = "Image creation failed for - " + img_url  + " Response code - " + str(response.json())
            logging.info(logline)
    return render_template('index.html')

@app.route('/stream', methods=["GET", "POST"])
def stream():
    return jsonify(open("myapp.log").readlines())

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
    global cpustat
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
    container_stats["cpu_usage"] = (float(stat["cpu_stats"]["cpu_usage"]["total_usage"]-cpustat[key][0])/float(stat["cpu_stats"]["system_cpu_usage"] - cpustat[key][1])) *100
    container_stats["mem_usage"] = (float(float(stat["memory_stats"]["usage"])/float(stat["memory_stats"]["limit"]))) * 100
    logging.info(container_stats)

    if (container_stats["cpu_usage"] > 80 or container_stats["mem_usage"] > 35):
        logging.info("RESOURCE LIMIT EXCEEDED")
        take_action(container_stats["ip"], 0, container_stats["container_name"])
        logging.info("Stopped container successfully")
        logging.info("Host : %s, container name : %s", container_stats["ip"], container_stats["container_name"])
        del containermap[container_stats["ip"]]

@app.route('/monitor', methods = ["GET", "POST"])
def monitor():
    global ip_container
    global containermap
    
    logging.info("Inside monitor")
    logging.info(ip_container)
    for line in ip_container:
        logging.info("Starting with " + str(line))        
        
        line.replace("http://", "")
        res=line.strip().split(" ")
        container_name = res[1]
        logging.info("Analyzing the Container " + container_name)
        
        res1 = res[0].strip().split(":")[0]
        containermap[res1] = [container_name]
    st = 0

    while st < 10:
        helper()
        # sleep(1)
        st += 1
    
    return render_template('index.html')

def helper():
    global containermap
    stat_threads=[]
    for ip in containermap:
        # print "ip: %s , container: %s" % (ip, containermap[ip])
        logging.info("Connecting to " + str(ip))
        
        for container in containermap[ip]:
            stat_threads.append( Thread(target=get_container_stat, args=(ip, container)))
#               get_container_stat(ip, containermap[ip])
    for thread in stat_threads:
            thread.start()
    for thread in stat_threads:
            thread.join()

def take_action(host_id, action_code, container_name):
	if action_code == 0:
		stop_url = 'http://' + host_id + ':4243/containers/' + container_name + '/stop'
		resp = request_retry_session(backoff_factor = 1).post(stop_url)
		logging.info(resp.status_code)
		if resp.status_code != 204 and resp.status_code != 304:
			raise Exception('Unable to stop the container! ' + resp.text)
	elif action_code == 1:
		restart_url = 'http://' + host_id + ':4243/containers/' + container_name + '/restart'
		resp = request_retry_session(backoff_factor = 1).post(restart_url)
		logging.info(resp.status_code)
		if resp.status_code != 204:
			raise Exception('Unable to stop the container! ' + resp.text)

# Create a custom retry session with an exponential backoff strategy
def request_retry_session(
	retries=3,
	backoff_factor=0.3,
	status_forcelist=(500),
	session=None):
	session = session or requests.Session()
	retry = Retry(
		total=retries,
		read=retries,
		connect=retries,
		backoff_factor=backoff_factor,
		status_forcelist=status_forcelist,
	)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount('http://', adapter)
	session.mount('https://', adapter)
	return session

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename="myapp.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")
    app.run(debug=True, host='0.0.0.0', port=5001)

