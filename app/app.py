#!/usr/bin/env python
from flask import Flask, jsonify, render_template
import docker
import requests
import os
top_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
template_dir = os.path.join(top_dir, 'templates')

static_dir = os.path.join(top_dir, 'static')


app = Flask(__name__, static_url_path="", static_folder="../static", template_folder='../templates')

@app.route('/')
def landing():
    return render_template('index.html')


@app.route('/start_containers')
def start_container():
    """
    Gets the list of host and container names and starts them
    """
    logs = []
    f = open("config.txt", "r")
    if not f:
        return "Config file not found!!"
    args = {'Image': 'ubuntu'}
    for configline in f.readlines():
        logline = ""
        url, container_name = configline.strip().split(' ')
        if "http://" not in url:
            url = "http://" + url

        # For each of the entries, do-
        # 1. Create an image
        # 2. Create a container
        # 3. Start the container

        #### 1. Create an image
        image_name = "hello-world"
        img_url = url + "/images/create?fromImage=" + image_name + "&tag=latest"
        response = requests.post(img_url)
        if response.status_code == 200:
            logline = "Created the image - " + image_name
            logs.append(logline)

            #### 2. Create the container.
            #### Delete all the stopped containers before creating to avoid conflict
            del_container = url + "/containers/prune"
            response = requests.post(del_container)
            container_url = url + "/containers/create?name=" + container_name
            response = requests.post(container_url, json= {"Image": image_name})
            if response.status_code == 201:
                container_id = response.json()["Id"]                
                logline = "Created the container with Id- " + container_id
                logs.append(logline)
                
                
                #### 3. Start the container
                container_start_url = url + "/containers/" + container_id + "/start"
                response = requests.post(container_start_url)
                if response.status_code == 204:
                    ### All is well
                    logline = "Started the container - " + container_name
                    logs.append(logline)
                    
                else:
                    logline = "Couldn't start container with id - " + container_start_url + " Response code - " + str(response.status_code)
                    logs.append(logline)
                    
                    
            else:
                logline = "Container creation failed for - " + container_url + " Response code - " + str(response.status_code)
                logs.append(logline)
                
                
        else:
            logline = "Image creation failed for - " + img_url  + " Response code - " + str(response.json())
            logs.append(logline)            
    return jsonify(logs)

@app.route('/stream')
def stream():
    def generate():
        with open('job.log') as f:
            while True:
                yield f.read()
                sleep(1)

    return app.response_class(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

