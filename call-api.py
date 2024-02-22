import base64
import os
import requests
import json
import argparse
import jsonlines
from requests.auth import HTTPBasicAuth
from datetime import datetime
from tqdm import tqdm
from tenacity import RetryError, retry, wait_random_exponential, stop_after_attempt
from concurrent.futures import ThreadPoolExecutor
from functools import partial

API_KEY = "" # TODO your openai api key

def encode_image(image_path):
    if not os.path.exists(image_path):
        print("not exist: ", image_path)
        exit(1)
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@retry(wait=wait_random_exponential(min=2, max=10), stop=stop_after_attempt(5))
def query_single_turn(image_paths, question, history=None, model="gpt-4-vision-preview", temperature=0, max_tokens=4096):
    content = [{"type": "text", "text": question}]
    for image_path in image_paths:
        encoded_image = encode_image(image_path)
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}", "detail": "high"}})
    
    messages = [
        {
            "role": "user",
            "content": content
        }
    ]
    if history is not None:
        messages = history + messages
    
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.post(url=url, headers=headers, json=payload)

    response_json = response.json()
    response_text = response_json["choices"][0]["message"]["content"]
    print(">>> get api response: ", response_text)
    return response_json
    
def query_single_turn_and_save(exp_name, image_paths, question, history=None, model="gpt-4-vision-preview", temperature=0, max_tokens=4096, additional_save=None):
    
    def get_today_str():
        current_datetime = datetime.now()
        date_string = current_datetime.strftime("%Y-%m-%d")
        return date_string

    try:
        response = query_single_turn(image_paths, question, history, model, temperature, max_tokens)
    except RetryError as e:
        print(">>> api error:", e)
        response = None
    overall = {
        "exp": exp_name,
        "image_paths": image_paths,
        "history": history,
        "question": question,
        "model": model,
        "temperature": temperature,
        "response": response
    }

    if additional_save is not None:
        overall.update(additional_save)
    save_dir = os.path.join("log", get_today_str())
    save_file = os.path.join(save_dir, f"{exp_name}.json")
    os.makedirs(os.path.dirname(save_file), exist_ok=True)
    with open(save_file, "w") as f:
        f.write(json.dumps(overall, indent=2, ensure_ascii=False))
        f.close()

def examples_inference(data_file="data/examples/example.jsonl", mode="scaffold", parallel=1):

    def get_output_inst():
        return [{
            "role": "system",
            "content": [{
                "type": "text",
                "text": f'''Finally, you must conclude your answer in format [[ANSWER]], such as [[true]] or [[false]].'''
            }]
        }]

    def get_textual_guidelines(h, w):
        """
        the textual guidelines for LMMs to use coordinates properly (deliver both the original and the processed images to LMM)
        note that the fourth guideline is a requirement for output format, should be different among different tasks or applications
        """
        return [{
            "role": "system",
            "content": [{
                "type": "text",
                "text": f'''I will provide you with two images of the same scene. The second image is overlaid with a dot matrix of a shape of {h} * {w} to help you with your task, and each dot is labeled with two-dimensional coordinates (x,y).\n 1. When you mention any key objects in the image, first output their nearest coordinates then identify them.\n 2. You use the coordinates to determine the spatial relationships of the objects. Within each column, the x-coordinate increases from top to bottom, and within each row, the y-coordinate increases from left to right.\n 3. You can search and reason region by region with the help of the dots.\n 4. Finally, you must conclude your answer in format [[ANSWER]], such as [[true]] or [[false]].'''
            }]
        }]

    def get_textual_guidelines_single(h, w):
        """
        the textual guidelines for LMMs to use coordinates properly (only deliver the processed image to LMM)
        note that the fourth guideline is a requirement for output format, should be different among different tasks or applications
        """
        return [{
            "role": "system",
            "content": [{
                "type": "text",
                "text": f'''The image is overlaid with a dot matrix of a shape of {h} * {w} to help you with your task, and each dot is labeled with two-dimensional coordinates (x,y).\n 1. When you mention any key objects in the image, first output their nearest coordinates then identify them.\n 2. You use the coordinates to determine the spatial relationships of the objects. Within each column, the x-coordinate increases from top to bottom, and within each row, the y-coordinate increases from left to right.\n 3. You can search and reason region by region with the help of the dots.\n 4. Finally, you must conclude your answer in format [[ANSWER]], such as [[true]] or [[false]].'''
            }]
        }]
    
    def run_doc(doc, mode):
        img_path = doc["image_path"]
        id_ = doc["question_id"]
        exp_name = f"examples/{mode}/{id_}"
        qs = doc["question"]
        additional_save = {"ground_truth": doc["answer"]}
        if mode == "direct":
            query_single_turn_and_save(exp_name, [img_path], qs, history=get_output_inst(), additional_save=additional_save)
        elif mode == "cot":
            query_single_turn_and_save(exp_name, [img_path], qs + "\n Let's think step by step", history=get_output_inst(), additional_save=additional_save)
        elif mode == "scaffold":
            dots_image = img_path.replace(".jpg", "_dots.jpg")
            if not os.path.exists(dots_image):
                print(">>> processed image not exist:", dots_image, " please run image_processor.py first")
                return
            query_single_turn_and_save(exp_name, [img_path, dots_image], qs, history=get_textual_guidelines(6, 6), additional_save=additional_save)
        elif mode == "scaffold_single":
            dots_image = img_path.replace(".jpg", "_dots.jpg")
            if not os.path.exists(dots_image):
                print(">>> processed image not exist:", dots_image, " please run image_processor.py first")
                return
            query_single_turn_and_save(exp_name, [dots_image], qs, history=get_textual_guidelines_single(6, 6), additional_save=additional_save)
        else:
            print(">>> invalid mode:", mode)
            exit(1)

    docs = []
    with jsonlines.open(data_file, "r") as f:
        for doc in f:
            docs.append(doc)
        f.close()

    if parallel == 1:
        for doc in tqdm(docs):
            run_doc(doc, mode)
    else:
        run_sample_and_save_wrapper = partial(run_doc, mode=mode)
        with ThreadPoolExecutor(parallel) as executor:
            for _ in tqdm(
                executor.map(run_sample_and_save_wrapper, docs), total=len(docs)
            ):
                pass

if __name__=="__main__":
    """
    run scaffold prompting on example questions
    mode: choose from ["direct", "cot", "scaffold", "scaffold_single"]
    """
    parser = argparse.ArgumentParser(description='Scaffold example.')
    parser.add_argument('--mode', type=str, help='Different prompting methods', default="Scaffold")
    parser.add_argument('--parallel', type=int, help='Number of parallel queries', default=1)
    parser.add_argument('--data-file', type=str, help='Data path')
    args = parser.parse_args()
    print(args)

    examples_inference(data_file=args.data_file, mode=args.mode, parallel=args.parallel)
