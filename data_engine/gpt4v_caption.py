# -*- coding: utf-8 -*-
import json
from openai import OpenAI
from PIL import Image
import imghdr
import base64
import io
import httpx
import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gpt_keys = [
    {"idx":0,"key":"openai-key-1"},
    {"idx":1,"key":"openai-key-2"},
]

MAX_API_RETRY = len(gpt_keys)
key_id = 0
proxy_url = 'proxy_url'

def list_to_str(tmp):
    res = ''
    for item in tmp:
        res += '\n' + str(item)
    return res

def one_ask(text, image_paths, image_size=(512, 512), detail='low'):
    global key_id
    for i in range(MAX_API_RETRY):
        try:
            api_key = gpt_keys[key_id]['key']
            proxy_url = proxy_url
            proxies = {
                "http://": f"{proxy_url}",
                "https://": f"{proxy_url}",
            }
            http_c = httpx.Client(proxies=proxies)
            client = OpenAI(api_key=api_key, http_client=http_c)

            content = []
            content.append({"type": "text", "text": text})
            for image in image_paths:
                image_type = imghdr.what(image)

                with Image.open(image) as img:
                    # 缩略图
                    if img.size[0] > image_size[0] or img.size[1] > image_size[1]:
                        img.thumbnail(image_size, Image.LANCZOS)
                    byte_stream = io.BytesIO()
                    img.save(byte_stream, format=image_type)
                    encoded_string = base64.b64encode(byte_stream.getvalue()).decode('utf-8')

                img_src_attr_value = f'data:image/{image_type};base64,{encoded_string}'
                content.append({"type": "image_url", "image_url": {"url": img_src_attr_value, "detail": detail}})

            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[{"role": "user", "content": content}],
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            logger.info(text)
            logger.info(content)
            key_id += 1
            key_id = key_id % MAX_API_RETRY

            return content
        except Exception as e:
            key_id += 1
            key_id = key_id % MAX_API_RETRY
            logger.error('[error in one ask]:' + repr(e))
            time.sleep(1.5)
    logger.error(f"Failed after {MAX_API_RETRY} retries.")
    return "error"


caption_prompt = "Please describe the image for me in as much detail as possible. You need to generate a description of at least 120 words. If you can, identify what objects are present in the image."
caption_prompt = "请尽可能详细描述这幅图像。你需要生成至少200字的描述。如果可以的话，识别图像中的物体。"

caption_prompt_text = "这是一张图和图中的文字信息，文字信息内容为：<ocr_text>。根据图片本身和其中的文本内容理解这幅图，然后尽可能详细描述这幅图像，生成至少200字的描述。"
caption_prompt_text = "This is an image accompanied by text information, with the content of the text being: <ocr_text>. Based on both the image itself and the text content, understand the image and then describe it as comprehensively as possible, generating a description of at least 200 words."

def get_gpt4v_caption(img_folder, source_path, dest_path, begin_ix):
    with open(source_path, 'r', encoding='utf-8') as f:
        source_json = json.load(f)
    
    for ix, data in enumerate(source_json):
        if ix < begin_ix:
            continue

        logger.info("processing " + str(ix) +" total " + str(len(source_json)))
        try: 
            prompt = caption_prompt
            if len(data['text']) >= 1:
                # if text in image, new prompt
                prompt = caption_prompt_text.replace("<ocr_text>",list_to_str(data['text']))

            image_file = os.path.join(img_folder, data['image_path'])
            logger.info(image_file)
            gptout = one_ask(prompt, [image_file] ) # max 4 image at one ask
        
            new_item = data.copy()
            new_item['gpt4v_caption_interface'] = gptout
            new_item['gpt4v_prompt'] = prompt

            open(dest_path, 'a', encoding='utf-8').write(
                json.dumps(new_item, ensure_ascii=False)+'\n'
            )
            time.sleep(1.5)
        except Exception as e:
            logger.error("[error]: " + str(repr(e)))


if __name__ == '__main__':
    img_folder  = 'poster'
    source_path = 'poster.jsonl'
    dest_path =  'poster_caption.jsonl'
    begin_ix = 0
    get_gpt4v_caption(img_folder, source_path, dest_path, begin_ix)
    logger.info("done.")
