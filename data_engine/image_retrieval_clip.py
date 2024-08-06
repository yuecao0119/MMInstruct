      
import os
import json
import tqdm
from clip_retrieval.clip_client import ClipClient, Modality
import requests

root_path = 'MMInstruct'  
domain_list = os.listdir(root_path + '/images')
domain_list = sorted(domain_list, key=str.lower) 
istart_list = [0]*len(domain_list)
os.makedirs(root_path + '/clip_retrieval_images', exist_ok=True)
os.makedirs(root_path + '/clip_retrieval_images/json', exist_ok=True) 

for ix, domain in enumerate(domain_list):
    in_images_path = os.path.join(root_path, "source_domain", domain, "images" )
    in_images_list = [i for i in os.listdir(in_images_path) if i.endswith('.jpg') or i.endswith('.png')]
    out_images_dir = os.path.join(root_path, "clip_retrieval_images", domain)
    out_json_path = os.path.join(root_path, "clip_retrieval_images/json", domain + ".jsonl")
    err_json_path = os.path.join(root_path, "clip_retrieval_images/json", domain + "_err.jsonl")

    client = ClipClient(url="https://knn.laion.ai/knn-service", indice_name="laion5B-L-14", num_images=200)

    if not os.path.exists(out_images_dir):
        os.makedirs(out_images_dir)
        message = f"The directory '{out_images_dir}' has been created."
    else:
        message = f"The directory '{out_images_dir}' already exists."

    for i in tqdm.tqdm(range(len(in_images_list))):
        if i < istart_list[ix]:
            continue

        aug_item = {'image_path': in_images_list[i]}
        image_path = os.path.join(in_images_path, in_images_list[i])
        aug_item["retrieval"] = []

        try:
            results = client.query(image=image_path) 
        except Exception as e: 
            print(repr(e))
            open(err_json_path, 'a', encoding='utf-8').write(json.dumps(aug_item, ensure_ascii=False)+'\n')
            continue

        count = 0
        for i, item in enumerate(results):
            try:
                url = item['url'] 
                file_path = out_images_dir + '/{}.jpg'.format(item['id']) 
                response = requests.get(url, timeout=5)
            except:
                print("Skip fig {}".format(item['id']))
                continue
            if response.status_code == 200:
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                print(f'download {file_path}')
                aug_item["retrieval"].append({"image_path":file_path, "caption":item['caption'], "similarity":item['similarity']})
                count += 1
            else:
                print('HTTP Error:', response.status_code)
        aug_item["count"] = count
        open(out_json_path, 'a', encoding='utf-8').write(json.dumps(aug_item, ensure_ascii=False)+'\n')
