# -*- coding: utf-8 -*-
import re
import httpx
from openai import OpenAI
import random
import copy
import json
import time
import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
root_path = 'MMInstruct'

gpt_keys = [
    {"idx":0,"key":"openai-key-1"},
    {"idx":1,"key":"openai-key-2"},
]
MAX_API_RETRY = len(gpt_keys)
REQ_TIME_GAP = 1
proxy_url = 'proxy_url'
key_id = 0

def one_ask(client, text):
    content = []
    content.append({"type": "text", "text": text})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", 'content': 'You are a helpful and precise assistant.'}, 
                  {"role": "user", "content": content}]
    )
    return response.choices[0]

def get_answer(prompt):
    global key_id
    for i in range(3):
        try:
            api_key = gpt_keys[key_id]['key']
            proxy_url = proxy_url
            proxies = {
            "http://": f"{proxy_url}",
            "https://": f"{proxy_url}",
            }
            http_c = httpx.Client(proxies=proxies)
            client = OpenAI(api_key=api_key, http_client=http_c)
            response = one_ask(client, prompt)
            content = response.message.content
            return content
        except Exception as e:
            key_id += 1
            key_id = key_id % MAX_API_RETRY
            logger.info(e)
            time.sleep(2)
    logger.info(f"Failed after {MAX_API_RETRY} retries.")
    return "error"


choice_prompt = 'Giving the description of an image and a question list including five questions, you need to desigin three multiple choice questions related to the <domain>.\n\
For each sample, the meaning of generated question MUST be similar to the question in the provided question list, and you need to output four choices as candidates.\n\
There should be only one choice that is the answer to the question, and this correct choice should be generated according to the description of the image. \n\
These choices should be indexed by captital letters.\n\
The description of the image and question list for you are as follows:\n\
Description: <caption>. \n Question: <original_question_list>. \n  \
You MUST output the generated question, choices and answer in the following format:\n\
<Q1> {the generated question 1} </Q1> <C1> {the choices you give} </C1> <A1> {the right choice of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <C2> {the choices you give} </C2> <A2> {the right choice of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <C3> {the choices you give} </C3> <A3> {the right choice of the question 3} </A3>\n'

choice_prompt = '给出图像的描述和问题列表，你需要设计三个与<domain>相关的中文单项选择问题。\n\
对于每个样本，生成的问题的含义必须与提供的问题列表中的问题相似，并且你需要输出四个选项作为候选者。\n\
并且只有一个选择是问题的正确答案，这个正确答案应该根据图像的描述生成。\n\
这些选择应该通过A、B、C、D四个大写字母进行索引。\n\
图像相关信息（"Empty"表示没有信息）：<prior_knowledge> \n\
描述：<caption>\n\n问题：<question_templates>\n\
我给你的问题<>里的内容是占位符，你只需要选择一个最合适的即可，不需要保留两个或者更多。\
最后，一定保证你生成的问题符合主题，一定不要生成一些和我提供给你的问题列表中含义差别很大的问题。\
你必须以以下格式输出生成的问题、选项和答案：\n\
<Q1> {the generated question 1} </Q1> <C1> {the choices you give: A. xxx B. xxx C. xxx D. xxx} </C1> <A1> {the right choice of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <C2> {the choices you give: A. xxx B. xxx C. xxx D. xxx} </C2> <A2> {the right choice of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <C3> {the choices you give: A. xxx B. xxx C. xxx D. xxx} </C3> <A3> {the right choice of the question 3} </A3>\n'

def generate_choice(domain, begin_ix):
    captions_path = f'{root_path}/{domain}/{domain}_caption.jsonl'
    generated_queations_path = f'{root_path}/{domain}/{domain}_choice.jsonl'
    seed_json = f'{root_path}/all_seed/{domain}.json'

    questions_model = []
    with open(seed_json, "r", encoding='utf-8') as file:
        try:
            json_data = json.load(file)
            questions_model = json_data["select"]["Chinese"]
        except:
            logger.info('读取问题种子失败')

    ix = 0
    with open(captions_path, 'r', encoding='utf-8') as f:
        for line in f:
            ix += 1
            if ix < begin_ix:
                continue
            
            questions_model_list = random.sample(questions_model, min(3, len(questions_model)))
            caption_dict = json.loads(line)
            prompt = choice_prompt

            prior_knowledge = str(caption_dict.get("bing_tag", 'Empty'))
            if prior_knowledge == "":
                prior_knowledge = "Empty"

            prompt = prompt.replace("<domain>", domain[6:])
            prompt = prompt.replace('<prior_knowledge>', prior_knowledge)
            prompt = prompt.replace("<caption>", caption_dict['gpt4v_caption_interface'].replace("\n\n","\n"))
            prompt = prompt.replace('<question_templates>', str(questions_model_list))
            try:
                out = get_answer(prompt)
                logger.info("[prompt]\n" + prompt)
                logger.info("[image_path]:" + caption_dict['image_path'] + "\n[GPT OUT]: \n" + str(out))

                question_dict = {
                    "image_path": caption_dict['image_path'], 
                    "qa_raw": str(out),
                    "gpt_prompt": prompt    
                }
                open(generated_queations_path, 'a', encoding='utf-8').write(
                    json.dumps(question_dict, ensure_ascii=False)+'\n'
                )

            except Exception as e:
                logger.info(str(ix) + "  [ERROR]")
                logger.info("error info:" + str(repr(e)))
                caption_dict['err'] = str(repr(e))
                logger.info("error image path:" + caption_dict['image_path'])
                open(generated_queations_path, 'a', encoding='utf-8').write(
                    json.dumps(caption_dict, ensure_ascii=False)+'\n'
                )

    logger.info('****done****')
    logger.info("total generate " + str(ix) + " {}  pairs. ")



lqa_prompt = 'Provide a description of an image and a list of multiple questions, you need to desigin three long question answering questions related to the <domain>.\n\
For each sample, the meaning of generated question MUST be similar to the question in the provided question list, and you need to output a detailed answer to the question.\n\
The detailed answer to this question should be generated based on the description of the image.\n\
The description of the image and question list for you are as follows:\n\
Description: <caption>. \n Question: <original_question_list>. \n  \
You MUST output the generated questions and answers in the following format:\n\
<Q1> {the generated question 1} </Q1> <A1> {the long answer of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <A2> {the long answer of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <A3> {the long answer of the question 3} </A3>\n'

lqa_prompt = '给出图像的描述和问题列表，你需要设计三个与<domain>相关的中文长问答问题。\n\
对于每个样本，生成的问题的含义必须与提供的问题列表中的问题相似，并且你需要输出该问题的详细答案。\n\
这个问题的详细答案应该根据图像的描述生成。\n\
图像相关信息（"Empty"表示没有信息）：<prior_knowledge> \n\
描述：<caption>\n 问题：<question_templates>\n\
你必须以以下格式输出生成的问题和答案：\n\
<Q1> {the generated question 1} </Q1> <A1> {the long answer of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <A2> {the long answer of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <A3> {the long answer of the question 3} </A3>\n'

def generate_long_qa(domain, begin_ix=0):
    print("\n\n****start lqa and answer working****\n\n")
    captions_path = f'{root_path}/{domain}/{domain}_caption.jsonl'
    generated_queations_path = f'{root_path}/{domain}/{domain}_lqa.jsonl'
    error_dest_path = f'{root_path}/{domain}/{domain}_lqa_err.jsonl'
    seed_json = f'{root_path}/all_seed/{domain}.json'

    questions_model = []
    with open(seed_json, "r", encoding='utf-8') as file:
        try:
            json_data = json.load(file)
            questions_model = json_data["select"]["Chinese"]
        except:
            print('读取问题种子失败')

    ix = 0
    with open(captions_path, 'r', encoding='utf-8') as f:
        for line in f:
            ix += 1
            if ix < begin_ix:
                continue
            
            questions_model_list = random.sample(questions_model, min(3, len(questions_model)))
            print("questions_model_list: " + str(questions_model_list))

            caption_dict = json.loads(line)
            prompt = lqa_prompt
            prompt = prompt.replace("<domain>", domain)
            prompt = prompt.replace('<prior_knowledge>', str(caption_dict.get("prior", 'Empty')))
            prompt = prompt.replace("<caption>", caption_dict['caption'])
            prompt = prompt.replace('<question_templates>', str(questions_model_list))
            try:
                out = get_answer(prompt)
                print("[image_path]: \n" + caption_dict['image_path'] + "\n\n[GPT OUT]: \n" + str(out))
                question_dict = {
                    "image_path": caption_dict['image_path'], 
                    "qa_raw": str(out),
                    "gpt_prompt": prompt    
                }
                open(generated_queations_path, 'a', encoding='utf-8').write(
                        json.dumps(question_dict, ensure_ascii=False)+'\n'
                    )
            except Exception as e:
                print(str(ix) + "  [ERROR]")
                print("error info:" + str(repr(e)))
                caption_dict['err'] = str(repr(e))
                print("error image path:" + caption_dict['image_path'])
                open(error_dest_path, 'a', encoding='utf-8').write(
                    json.dumps(caption_dict, ensure_ascii=False)+'\n'
                )

    print('****done****')
    print("total generate " + str(ix) + " pairs. ")


sqa_prompt = 'Provide a description of an image and a list of multiple questions, you need to desigin three short question answering questions related to the <domain>.\n\
For each sample, the meaning of generated question MUST be similar to the question in the provided question list, and you need to output a few words or short sentences as a short answer to the question.\n\
The answer to this question should be generated based on the description of the image.\n\
The description of the image and question list for you are as follows:\n\
Description: <caption>. \n Question: <original_question_list>. \n  \
You MUST output the generated questions and answers in the following format:\n\
<Q1> {the generated question 1} </Q1> <A1> {the short answer of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <A2> {the short answer of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <A3> {the short answer of the question 3} </A3>\n'

sqa_prompt = '给出图像的描述和问题列表，你需要设计三个与<domain>相关的中文短问答问题。\n\
对于每个样本，生成的问题的含义必须与提供的问题列表中的问题相似，并且你需要输出几个单词或短句作为问题的简短答案。\n\
这个问题的短答案应该根据图像的描述生成。\n\
图像相关信息（"Empty"表示没有信息）：<prior_knowledge> \n\
描述：<caption>\n 问题：<question_templates>\n\
你必须以以下格式输出生成的问题和答案：\n\
<Q1> {the generated question 1} </Q1> <A1> {the short answer of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <A2> {the short answer of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <A3> {the short answer of the question 3} </A3>\n'

def generate_short_qa(domain, begin_ix=0):
    print("\n\n****start sqa and answer working****\n\n")
    captions_path = f'{root_path}/{domain}/{domain}_caption.jsonl'
    generated_queations_path = f'{root_path}/{domain}/{domain}_sqa.jsonl'
    error_dest_path = f'{root_path}/{domain}/{domain}_sqa_err.jsonl'
    seed_json = f'{root_path}/all_seed/{domain}.json'

    questions_model = []
    with open(seed_json, "r", encoding='utf-8') as file:
        try:
            json_data = json.load(file)
            questions_model = json_data["select"]["Chinese"]
        except:
            print('读取问题种子失败')

    ix = 0
    with open(captions_path, 'r', encoding='utf-8') as f:
        for line in f:
            ix += 1
            if ix < begin_ix:
                continue

            questions_model_list = random.sample(questions_model, min(3, len(questions_model)))
            caption_dict = json.loads(line)

            prompt = sqa_prompt
            prompt = prompt.replace("<domain>", domain)
            prompt = prompt.replace('<prior_knowledge>', str(caption_dict.get("prior", 'Empty')))
            prompt = prompt.replace("<caption>", caption_dict['caption'])
            prompt = prompt.replace('<question_templates>', str(questions_model_list))
            try:
                out = get_answer(prompt)
                print("[image_path]: \n" + caption_dict['image_path'] + "\n\n[GPT OUT]: \n" + str(out))
                question_dict = {
                    "image_path": caption_dict['image_path'], 
                    "qa_raw": str(out),
                    "gpt_prompt": prompt    
                }
                open(generated_queations_path, 'a', encoding='utf-8').write(
                    json.dumps(question_dict, ensure_ascii=False)+'\n'
                )
            except Exception as e:
                print(str(ix) + "  [ERROR]")
                print("error info:" + str(repr(e)))
                caption_dict['err'] = str(repr(e))
                print("error image path:" + caption_dict['image_path'])
                open(error_dest_path, 'a', encoding='utf-8').write(
                    json.dumps(caption_dict, ensure_ascii=False)+'\n'
                )

    print('****done****')
    print("total generate " + str(ix) + " pairs. ")



judge_prompt = 'Provide a description of an image and a list of multiple questions, you need to desigin three true or false questions related to the <domain>.\n\
For each sample, the meaning of generated question MUST be similar to the question in the provided question list, and you need to output "Yes" or "No" as the answer to the question.\n\
The answer to this question should be generated based on the description of the image.\n\
The description of the image and question list for you are as follows:\n\
Description: <caption>. \n Question: <original_question_list>. \n  \
You MUST output the generated questions and answers in the following format:\n\
<Q1> {the generated question 1} </Q1> <C1> {"Yes",  "No"} </C1> <A1> {the right choice of the question 1} </A1>\n\
<Q2> {the generated question 2} </Q2> <C2> {"Yes",  "No"} </C2> <A2> {the right choice of the question 2} </A2>\n\
<Q3> {the generated question 3} </Q3> <C3> {"Yes",  "No"} </C3> <A3> {the right choice of the question 3} </A3>\n'

judge_prompt = '给出图像的描述和问题列表，你需要设计四个与<domain>相关的中文判断题。\n\
对于每个样本，生成的问题的含义必须与提供的问题列表中的问题相似，并且你需要输出“是”或“否”作为问题的答案。\n\
注意答案只能是“是”或“否”的其中之一，这个正确答案应该根据图像的描述生成。\n\
图像相关信息（"Empty"表示没有信息）：<prior_knowledge> \n\
描述：<caption>\n 问题：<question_templates>\n\
我给你的问题<>里的内容是占位符，你需要进行根据图像相关信息和描述来生成。\n\
你生成的四个判断题题目，应该保证其根据图像的描述生成的对应正确答案中的两个为“是”，另外两个为“否”。\n\
答案为“否”的判断题题目，你可以随机生成一些错误但与图像相关信息和描述相关的词语。\n\
最后，一定保证你生成的问题逻辑通顺、符合主题且与图像相关信息和描述相关。\n\
你必须以下格式输出生成的问题、选项和答案：\n\
<Q1> {the generated question 1} </Q1> <C1> {"是",  "否"} </C1> <A1> {"是" or "否"} </A1>\n\
<Q2> {the generated question 2} </Q2> <C2> {"是",  "否"} </C2> <A2> {"是" or "否"} </A2>\n\
<Q3> {the generated question 3} </Q3> <C3> {"是",  "否"} </C3> <A3> {"是" or "否"} </A3>\n\
<Q4> {the generated question 3} </Q4> <C4> {"是",  "否"} </C4> <A4> {"是" or "否"} </A4>\n\
'

def generate_judge(domain, begin_ix=0):
    print("\n\n****start judge and answer working****\n\n")
    captions_path = f'{root_path}/{domain}/{domain}_caption.jsonl'
    generated_queations_path = f'{root_path}/{domain}/{domain}_judge.jsonl'
    seed_json = f'{root_path}/all_seed/{domain}.json'

    questions_model = []
    with open(seed_json, "r", encoding='utf-8') as file:
        try:
            json_data = json.load(file)
            questions_model = json_data["judge"]["Chinese"]
        except:
            logger.info('读取问题种子失败')
            return

    ix = 0
    with open(captions_path, 'r', encoding='utf-8') as f:
        for line in f:
            ix += 1
            if ix < begin_ix:
                continue

            questions_model_list = random.sample(questions_model, min(3, len(questions_model)))
            caption_dict = json.loads(line)

            prompt = judge_prompt
            prompt = prompt.replace("<domain>", domain[6:])
            prior_knowledge = str(caption_dict.get("bing_tag", 'Empty'))
            if prior_knowledge == "":
                prior_knowledge = "Empty"
            prompt = prompt.replace('<prior_knowledge>', prior_knowledge)
            prompt = prompt.replace("<caption>", caption_dict['gpt4v_caption_interface'].replace("\n\n","\n"))
            prompt = prompt.replace('<question_templates>', str(questions_model_list))
            try:
                out = get_answer(prompt)
                question_dict = {
                    "image_path": caption_dict['image_path'], 
                    "qa_raw": str(out),
                    "gpt_prompt": prompt    
                }
                open(generated_queations_path, 'a', encoding='utf-8').write(
                    json.dumps(question_dict, ensure_ascii=False)+'\n'
                )
                
            except Exception as e:
                logger.info(str(ix) + "  [ERROR]")
                logger.info("error info:" + str(repr(e)))
                caption_dict['err'] = str(repr(e))
                logger.info("error image path:" + caption_dict['image_path'])
                open(generated_queations_path, 'a', encoding='utf-8').write(
                        json.dumps(caption_dict, ensure_ascii=False)+'\n'
                    )

    logger.info('****done****')
    logger.info("total generate " + str(ix) + " pairs. ")

if __name__ == "__main__":
    domain = "poster"
    generate_choice(domain,begin_ix=0)
