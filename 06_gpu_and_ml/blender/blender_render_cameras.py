#from subprocess import Popen, PIPE
import subprocess
import modal
from pathlib import Path
import sys
import os
import requests

commands = ["FROM base",
            "RUN apt-get update && \
                apt-get install -y \
                    curl wget nano \
                    bzip2 libfreetype6 libxkbcommon-x11-0 libgl1-mesa-dev \
                    libglu1-mesa \
                    libxi6 libxrender1 && \
                apt-get -y autoremove && \
                pip install --upgrade pip && \
                pip install requests",
            "RUN mkdir /usr/local/blender && \
                wget https://download.blender.org/release/Blender3.4/blender-3.4.1-linux-x64.tar.xz -O blender.tar.xz && \
                tar -xvf blender.tar.xz -C /usr/local/blender --strip-components=1 && \
                rm blender.tar.xz"
            ]

files = [{'identifier': 'test1', 'url': 'https://www.dropbox.com/scl/fi/xu15c679u6l6b9sw7r2m6/silo_template.blend?rlkey=68rw5xjexf98wbbvvq92fx3pt&dl=1'}]

image = modal.Image.debian_slim().extend(
    dockerfile_commands=commands
)

stub = modal.Stub(
    "example-blender-cameras",
    image=image
)

stub.volume = modal.Volume.new()

blenderpath = '/usr/local/blender/blender '
flags = ' -b -P '
render_script = "/tmp/render_all_cameras.py"

def download_file(name, url):
    local_filename = f"/tmp/{name}"
    try:
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        # NOTE the stream=True parameter below
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=10000): 
                    f.write(chunk)
    except BaseException as error: #TODO: Not a great idea. 
        print('An exception occurred: {}'.format(error))
        return -1    
    return local_filename

@stub.function(timeout=36000, \
               volumes = {"/data/": stub.volume})
def download_blenderfile(identifier, url):
    local_filename = f"/tmp/{identifier}/scene.blend"
    try:
        os.makedirs(os.path.dirname(local_filename), exist_ok=True)
        # NOTE the stream=True parameter below
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=10000): 
                    f.write(chunk)
    except BaseException as error: #TODO: Not a great idea. 
        print('An exception occurred: {}'.format(error))
        return -1    
    return local_filename


potential_markers = ['SKETUP', 'RENSKDERING', 'DOSKNE']
def get_value_btwn_markers(test_str):
    for marker in potential_markers:
        val = None
        s_marker = marker + ':'
        e_marker = ':' + marker                                                                                     

        # getting index of substrings
        idx1 = test_str.find(s_marker)
        idx2 = test_str.find(e_marker)
 
        # length of substring 1 is added to
        # get string from next character
        val = test_str[idx1 + len(sub1) + 1: idx2]
        

def render_file (filepath):
    print ("Running..")
    print (blenderpath + filepath + flags + str(render_script))
    # ret_val  = subprocess.check_output(blenderpath + filepath + flags + str(render_script), shell=True)
    # print (ret_val)
    image_num=0
    with subprocess.Popen(blenderpath + filepath + flags + str(render_script), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        print ("render started")
        for line in process.stdout:
            status = line.decode('utf8')
            print (status)

    print ("run complete")
    return 0

#####Render Function######
@stub.function(timeout=36000, \
               volumes = {"/data/": stub.volume},
               mounts=[modal.Mount.from_local_file(\
                            "render_camera.py", \
                            remote_path="/tmp/render_camera.py"),
                       modal.Mount.from_local_file(\
                            "get_camera_names.py", \
                            remote_path="/tmp/get_camera_names.py")], \
               gpu = "any") #leaving timeout at 10hrs now
def render (remote_path, identifier):

    #print ("downloading files")
    # download_file('test1', 'https://www.dropbox.com/scl/fi/4qsf2x16geygaw8z1povb/Wide-Angle-2.jpg?rlkey=6lanc6wwzpdugp3hxnd9lrkde&dl=1')
    # download_file('test2', 'https://www.dropbox.com/scl/fi/wql9z85bvwzijmunqmtmb/DresserHeroAngle.jpg?rlkey=4y3ovqi2a76d2hivf64z3685u&dl=1')

    # if (os.path.isfile('/tmp/test1.jpg')):
    #     print ("file downloaded")
    print (f"Downloading blend file for {identifier} from {remote_path}")
    filename = download_blenderfile(identifier, remote_path)
    if (os.path.isfile(filename)):
        print (f"file downloaded at {filename}")
        #render_file(filename)


    
@stub.local_entrypoint()
def main():
    render.call(files[0].get('url'), files[0].get('identifier'))

