import subprocess
import json
import time
import os
import PyPDF2
import copy
import argparse

# initialize argument parser and create arguments
parser = argparse.ArgumentParser(description="Create reMarkable-format files from a pdf")
parser.add_argument("filepath", type=str, help="path to the file to convert")
parser.add_argument("-d", "--destination", type = str, help="path to destination folder", default="")
parser.add_argument("-n", "--name", type = str, help="custom name to set to the document", default="")
parser.add_argument("-l", "--landscape", action="store_true", help="set the pdf to landscape mode")
parser.add_argument("-u", "--upload", type=str, default="", help="ip address used to upload files via ssh")
parser.add_argument("-r", "--reboot", action="store_true", help="automatically reeboot after upload. Ignored if -u is not set")
args = parser.parse_args()  # parse arguments (filepath, destination, name, landscape)


uuid_command = subprocess.Popen("uuidgen", stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # run uuidgen to generate file uuid
uuid, _ = uuid_command.communicate()    # extract output from stdout, ignore errors from stderr
uuid = uuid.decode('utf-8').replace("\n", "")   # convert to usable format

#subprocess.Popen(["mkdir", f"output/{uuid}"])   # create a directory for output files
subprocess.Popen(["cp", f"{args.filepath}", f"{args.destination}/{uuid}.pdf"])   # copy pdf and set its name
subprocess.Popen(["touch", f"{args.destination}/{uuid}.pagedata"])  # create empty pagedata file

with open("reference/reference.metadata", "r") as file:
    metadata = json.load(file)

# create metadata file

time_str = str(int(time.time() * 1000))     # get unix time in milliseconds and convert it to string (ignores decimals which may be introduced by the multiplication)

# set some parameters
metadata["createdTime"] = time_str
metadata["lastModified"] = time_str
metadata["lastOpened"] = time_str
metadata["visibleName"] = args.filepath.split("/")[-1].replace(".pdf", "") if args.name == "" else args.name
with open(f"{args.destination}/{uuid}.metadata", "x") as file:
    json.dump(metadata, file ,indent=4)

# create content file
with open("reference/reference.content") as file:
    content = json.load(file)

size_str = str(os.path.getsize(args.filepath))
content["sizeInBytes"] = size_str

with open(args.filepath, 'rb') as file:
    pdf_reader = PyPDF2.PdfReader(file)
    page_num = len(pdf_reader.pages)
content["pageCount"] = page_num
content["cPages"]["original"]["value"] = page_num


with open("reference/reference.page", "r") as file:
    page_temp = json.load(file)

alphabet = list("abcdefghijklmnopqrstwxyz")
for i in range(page_num):
    # generate an uuid for each page
    page_uuid_command = subprocess.Popen("uuidgen", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    page_id, _ = page_uuid_command.communicate()
    page_id = page_id.decode('utf-8').replace("\n", "")

    # set parameters to template page
    page_temp["id"] = page_id
    page_temp["idx"]["value"] = alphabet[1+i//26] + alphabet[i%26]
    page_temp["redir"]["value"] = i

    content["cPages"]["pages"].append(copy.deepcopy(page_temp))

content["cPages"]["lastOpened"]["value"] = content["cPages"]["pages"][0]["id"]
content["orientation"] = "portrait" if not args.landscape else "landscape"

with open(f"{args.destination}/{uuid}.content", "x") as file:
    json.dump(content, file, indent=4)

if (args.upload != ""):
    subprocess.Popen(["scp", f"{args.destination}/{uuid}.pdf", f"root@{args.upload}:/home/root/.local/share/remarkable/xochitl/"])   # upload files with scp
    subprocess.Popen(["scp", f"{args.destination}/{uuid}.content", f"root@{args.upload}:/home/root/.local/share/remarkable/xochitl/"])   # upload files with scp
    subprocess.Popen(["scp", f"{args.destination}/{uuid}.metadata", f"root@{args.upload}:/home/root/.local/share/remarkable/xochitl/"])   # upload files with scp
    subprocess.Popen(["scp", f"{args.destination}/{uuid}.pagedata", f"root@{args.upload}:/home/root/.local/share/remarkable/xochitl/"])   # upload files with scp
    if (args.reboot):
        subprocess.Popen(["ssh", f"root@{args.upload}", "systemctl", "restart", "xochitl"])
