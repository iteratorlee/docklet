import sys
sys.path.append("../src/")
import os,json
from datetime import datetime
from model import db, VCluster, Container, PortMapping, Image, BillingHistory

timeFormat = "%Y-%m-%d %H:%M:%S"
dockletPath = "/opt/docklet/global"
usersdir = dockletPath + "/users/"

try:
    VCluster.query.all()
except Exception as err:
    print("Create database...")
    db.create_all()

print("Update vcluster...")
for user in os.listdir(usersdir):
    tmppath = usersdir+user+"/clusters/"
    if not os.path.exists(tmppath):
        continue
    print("Update User: "+str(user))
    clusterfiles = os.listdir(tmppath)
    for cluname in clusterfiles:
        cluFile = open(tmppath+cluname,"r")
        cluinfo = json.loads(cluFile.read())
        vcluster = VCluster(cluinfo['clusterid'],cluname,user,cluinfo['status'],cluinfo['size'],cluinfo['nextcid'],cluinfo['proxy_server_ip'],cluinfo['proxy_public_ip'])
        vcluster.create_time = datetime.strptime(cluinfo['create_time'],timeFormat)
        vcluster.start_time = cluinfo['start_time']
        for coninfo in cluinfo['containers']:
            lastsavet = datetime.strptime(coninfo['lastsave'],timeFormat)
            con = Container(coninfo['containername'], coninfo['hostname'], coninfo['ip'], coninfo['host'], coninfo['image'], lastsavet, coninfo['setting'])
            vcluster.containers.append(con)
        for pminfo in cluinfo['port_mapping']:
            pm = PortMapping(pminfo['node_name'], pminfo['node_ip'], int(pminfo['node_port']), int(pminfo['host_port']))
            vcluster.port_mapping.append(pm)
        if "billing_history" in cluinfo.keys():
            for nodename in cluinfo['billing_history'].keys():
                bhinfo = cluinfo['billing_history'][nodename]
                bh = BillingHistory(nodename,bhinfo['cpu'],bhinfo['mem'],bhinfo['disk'],bhinfo['port'])
                vcluster.billing_history.append(bh)
        try:
            db.session.add(vcluster)
            db.session.commit()
        except Exception as err:
            print(err)
        cluFile.close()

print("Update Images...")
for shareStr in ['private/','public/']:
    print("Update "+shareStr+" Images...")
    for user in os.listdir(dockletPath+"/images/"+shareStr):
        print("Update User: "+user)
        tmppath = dockletPath+"/images/"+shareStr+user+"/"
        files = os.listdir(tmppath)
        images = []
        for file in files:
            if file[0] == "." or file[-3] != ".":
                continue
            images.append(file[:-3])
        for img in images:
            infofile = open(tmppath+"."+img+".info","r")
            imginfo = infofile.read().split('\n')
            infofile.close()
            desfile = open(tmppath+"."+img+".description","r")
            desinfo = desfile.read()
            dbimage = Image.query.filter_by(imagename=img,ownername=user).first()
            if dbimage is None:
                dbimage = Image(img,False,False,user,desinfo)
                dbimage.create_time = datetime.strptime(imginfo[0],timeFormat)
            if shareStr == 'public/':
                dbimage.hasPublic = True
            else:
                dbimage.hasPrivate = True
            try:
                db.session.add(dbimage)
                db.session.commit()
            except Exception as err:
                print(err)
print("Finished!")
