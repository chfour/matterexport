#!/usr/bin/env python3
import requests, os, hashlib, json, argparse

parser = argparse.ArgumentParser()
parser.add_argument("sid", type=str,
                    help="SID of the house/object/whatever")
parser.add_argument("-o", "--output", type=str, default="output/",
                    help="directory to output to, default is output/")

args = parser.parse_args()

print("* loading model index json...")
r = requests.get(f"https://my.matterport.com/api/v1/player/models/{args.sid}/")
model_index = r.json()

os.makedirs(f"{args.output}/{args.sid}", exist_ok=True)
os.chdir(f"{args.output}/{args.sid}")

with open("modelindex.json", "wb") as f: f.write(r.content)
print(f"  ...{len(model_index['sweeps'])} sweeps")

os.makedirs("tiles", exist_ok=True)
os.chdir("tiles")

for sweep in model_index["sweeps"]:
    os.makedirs(sweep, exist_ok=True)
    
    for a in range(10):
        os.makedirs(f"{sweep}/{a:0>2}", exist_ok=True)
        
        a_hashes = {}
        if os.path.exists(f"{sweep}/{a:0>2}/hashes.json"):
            try:
                with open(f"{sweep}/{a:0>2}/hashes.json", "r") as f:
                    a_hashes = json.load(f)
            except:
                print(" * couldn't load existing hashes.json")
        for b in range(10):
            print()
            
            print("* loading templates...")
            r = requests.get(f"https://my.matterport.com/api/v1/player/models/{args.sid}/files?type=3")
            cdns = r.json()["templates"]
            print(f"  ...{len(cdns)} CDN[s] available")
            
            for c in range(10):
                for size in ["512", "1k", "2k"]:
                    for cdn_no, cdn in enumerate(cdns):
                        file_path = f"{sweep}/{a:0>2}/{size}_{b:0>2}_{c:0>2}.jpg"
                        
                        print(f" -> cdn#{cdn_no} : {sweep}/{size}_{a}_{b}_{c}")
                        
                        if os.path.exists(file_path):
                            print(" *  already downloaded")
                            with open(file_path, "rb") as f: tile_hash = hashlib.md5(f.read()).hexdigest()
                            a_hashes[f"{size}_{a}_{b}_{c}"] = tile_hash
                            print(f" *  md5: {tile_hash}")
                            break
                        
                        r = requests.get(cdn.replace("{{filename}}", f"tiles/{sweep}/{size}_face{a}_{b}_{c}.jpg"), headers={"accept": "image/jpeg"})
                        if not r.ok:
                            print(f" !  {r.status_code}")
                            continue
                        else:
                            print(f" <- {r.status_code}")

                        tile_hash = hashlib.md5(r.content).hexdigest()
                        if tile_hash in a_hashes.values():
                            print(" *  duplicate tile")
                            break
                        
                        print(f" *  {file_path}")
                        print(f" *  md5: {tile_hash}")
                        with open(file_path, "wb") as f: f.write(r.content)
                        a_hashes[f"{size}_{b}_{c}"] = tile_hash
                        break
        with open(f"{sweep}/{a:0>2}/hashes.json", "w") as f:
            json.dump(a_hashes, f, separators=(',', ':'))
