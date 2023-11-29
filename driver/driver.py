import subprocess
import json
import time
import os
import PyPDF2
import copy
import argparse

def get_uuid():
    uuid_command = subprocess.Popen("uuidgen", stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # run uuidgen to generate file uuid
    uuid, _ = uuid_command.communicate()    # extract output from stdout, ignore errors from stderr
    uuid = uuid.decode('utf-8').replace("\n", "")   # convert to usable format
    return uuid

def gen_metadata(uuid, filepath, name, destination):
    # load template from reference
    with open("reference/reference.metadata", "r") as file:
        metadata = json.load(file)

    time_str = str(int(time.time() * 1000))     # get unix time in milliseconds and convert it to string (ignores decimals which may be introduced by the multiplication)

    metadata["createdTime"] = time_str  # set time of file creation
    metadata["lastModified"] = time_str # set last time the file was edited
    metadata["lastOpened"] = time_str   # set last time the file was opened
    metadata["visibleName"] = filepath.split("/")[-1].replace(".pdf", "") if name == "" else name    # set name visible from the UI

    # dump file to destination
    with open(f"{destination}/{uuid}.metadata", "x") as file:
        json.dump(metadata, file ,indent=4)

def gen_content(uuid, filepath, destination, landscape):
    # load template from reference files
    with open("reference/reference.content") as file:
        content = json.load(file)

    # get size in bytes and set appropriate parameter
    size_str = str(os.path.getsize(filepath))
    content["sizeInBytes"] = size_str

    # get total page number and set appropriate parameters
    with open(filepath, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        page_num = len(pdf_reader.pages)
    content["pageCount"] = page_num
    content["cPages"]["original"]["value"] = page_num

    # load page template
    with open("reference/reference.page", "r") as file:
        page_temp = json.load(file)

    alphabet = list("abcdefghijklmnopqrstwxyz")     # alphabet as a list. Used to set idx parameter. (no idea what it does, but i'm following the pattern seen in valid files)

    for i in range(page_num):
        # generate an uuid for each page
        page_id = get_uuid()

        # set some parameters to template page
        page_temp["id"] = page_id
        page_temp["idx"]["value"] = alphabet[1+i//26] + alphabet[i%26]
        page_temp["redir"]["value"] = i

        # create a copy of the reference page with parameters set and append it to the pages list
        content["cPages"]["pages"].append(copy.deepcopy(page_temp))

    # set a few remaining parameters
    content["cPages"]["lastOpened"]["value"] = content["cPages"]["pages"][0]["id"]  # set last page opened to first page's id
    content["orientation"] = "portrait" if not landscape else "landscape"  # set it lo landscape view if the corresponding flag is set

    # dump as file to destination
    with open(f"{destination}/{uuid}.content", "x") as file:
        json.dump(content, file, indent=4)

def convert(filepath, destination, name, landscape):
    # assign an uuid to the file
    uuid = get_uuid()

    # create the files that don't require editing
    subprocess.Popen(["cp", f"{filepath}", f"{destination}/{uuid}.pdf"])   # copy pdf and set its name
    subprocess.Popen(["touch", f"{destination}/{uuid}.pagedata"])  # create empty pagedata file

    # create metadata file with the correct parameters
    gen_metadata(uuid, filepath, name, destination)

    #create content file with the correct parameters
    gen_content(uuid, filepath, destination, landscape)

    return uuid

def upload(uuid, destination, upload):
    # us scp to copy file to the tablet. Assumes a valid key pair has been excanged

    base_command = "scp -o 'UserKnownHostsFile=/dev/null' -o 'StrictHostKeyChecking=no'"    # connect with ssh and ignore host key checks

    subprocess.Popen((base_command + f"{destination}/{uuid}.pdf" + f"root@{upload}:/home/root/.local/share/remarkable/xochitl/").split(" "))   # upload pdf
    subprocess.Popen((base_command + f"{destination}/{uuid}.content" + f"root@{upload}:/home/root/.local/share/remarkable/xochitl/").split(" "))   # upload content
    subprocess.Popen((base_command + f"{destination}/{uuid}.metadata" + f"root@{upload}:/home/root/.local/share/remarkable/xochitl/").split(" "))   # upload metadata
    subprocess.Popen((base_command + f"{destination}/{uuid}.pagedata" + f"root@{upload}:/home/root/.local/share/remarkable/xochitl/").split(" "))   # upload pagedata


def make_list(ip):
    #command = f"ssh -o 'UserKnownHostsFile=/dev/null' -o 'StrictHostKeyChecking=no' root@{ip} ls /home/root/.local/share/remarkable/xochitl/"    # connect with ssh and ignore host key checks
    command = ["ssh", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", f"root@{ip}", "ls", "/home/root/.local/share/remarkable/xochitl/"]
    list_command = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    file_list, _ = list_command.communicate()    # extract output from stdout, ignore errors from stderr
    file_list = file_list.decode('utf-8')   # convert to usable format
    file_list = file_list.split("\n")   # separate filenames
    file_list = [i.split(".")[0] for i in file_list]    # remove extensions
    uuids = []
    [uuids.append(i) for i in file_list if i not in uuids]  # remove duplicates and compile a list of file uuids

    # get information about each document
    file_info = []
    for _,id in enumerate(uuids):
        try:
            # use cat to get the content of the file and parse it with json lib. Exceptions are suppressed because some uuids don't have a corresponding .metadata
            command = ["ssh", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no", f"root@{ip}", "cat", f"/home/root/.local/share/remarkable/xochitl/{id}.metadata"]
            command = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            data = command.communicate()
            data = data[0].decode("utf-8").replace("\n", "")
            data = json.loads(data)
            data["id"] = id
            file_info.append(data)
            #print(data["visibleName"])
        except:
            pass
    print(json.dumps(file_info, indent=4))

def findIP(mac):
    command = subprocess.Popen("arp-scan --localnet".split(" "), stdout=subprocess.PIPE)#, stderr=subprocess.PIPE)  # run arp-scan to get a list of devices and ips
    dev_list, _ = command.communicate()    # extract output from stdout, ignore errors from stderr
    dev_list = dev_list.decode('utf-8').split("\n")   # convert to usable format
    dev_list = [i.split(" ") for i in dev_list]
    match_list = [i for i in dev_list if len(i)>2 and i[1].lower() == mac.lower()]
    [print(i[0]) for i in match_list]

# initialize argument parser and create arguments
parser = argparse.ArgumentParser(description="Interact with reMarkable's file system trough ssh")
parser.add_argument("-c", "--convert", type = str, help="path to the file to convert", default="")
parser.add_argument("-d", "--destination", type = str, help="path to destination folder", default="")
parser.add_argument("-n", "--name", type = str, help="custom name to set to the document", default="")
parser.add_argument("--landscape", action="store_true", help="set the pdf to landscape mode")
parser.add_argument("--ip", type=str, default="", help="ip address used to upload files via ssh")
parser.add_argument("-r", "--reboot", action="store_true", help="automatically reeboot the tablet after execution. Ignored if --ip is not set")
parser.add_argument("-l", "--list", action="store_true", help="list documents on tablet. Requires --ip to be set")
parser.add_argument("-u", "--upload", action="store_true", help="uploads generated files to the tablet. Requires --ip to be set")
parser.add_argument("-s", "--scan", type=str, default="", help="scan the network to find the IP associated with a MAC address")

args = parser.parse_args()  # parse arguments

if (args.scan != ""):
    findIP(args.scan)

# if the corresponding flag is set, create the appropriate files from a pdf
if (args.convert != ""):
    uuid = convert(args.convert, args.destination, args.name, args.landscape)

# if the corresponding flag is set, upload the files generated to the tablet
if (args.upload and args.convert != ""):
    upload(uuid, args.destination, args.ip)

# if --list is set, list the documents on the tablet
if (args.list):
    make_list(args.ip)
    

# if the corrisponding flag is set, reset the tablet's file system trough ssh
if (args.reboot and args.ip != ""):
    subprocess.Popen(["ssh", f"root@{args.ip}", "systemctl", "restart", "xochitl"])
