from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import BertTokenizer, BertModel
import transformers
import torch
import json
import requests
import re
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import json
from sklearn.metrics import (
    precision_recall_fscore_support,
    accuracy_score,
    confusion_matrix,
)
from typing import List, Dict, Tuple
from itertools import combinations
from openai import OpenAI
import numpy as np
from wrench._logging import LoggingHandler
from wrench.dataset import load_dataset
from wrench.endmodel import BertClassifierModel
from wrench.explainer import Explainer, modify_training_labels
from wrench.labelmodel import FlyingSquid
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors


def model_init(model_id="./model/gemma-2-9b-it", dtype=torch.bfloat16, device="cuda"):
    model_id = model_id
    dtype = dtype

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map=device,
        torch_dtype=dtype,
    )
    return model, tokenizer


def prompt_for_yesno(question, text, model, tokenizer):
    text = text
    question = question
    prompt_tail = "Only answer in Yes or No with no any other words"
    desired_format = "yes|no"
    chat = [
        {
            "role": "user",
            "content": "Prompt:{%s %s}. \nText:{%s} . \nDesired format: {%s}"
            % (question, prompt_tail, text, desired_format),
        },
    ]
    prompt = tokenizer.apply_chat_template(
        chat, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
    outputs = model.generate(
        input_ids=inputs.to(model.device), max_new_tokens=150, do_sample=False
    )  # 采样温度)
    outputs = tokenizer.decode(outputs[0])

    return outputs


def prompt_for_keywords(text, tokenizer, model):
    """
    根据给定的text,由大语言模型生成若干个合适的关键词

    参数：
    - text (str): 待生成的文本
    -tokenizer:初始化后的语言模型
    -model:初始化后的语言模型
    返回：
    大语言模型的输出。
    格式为:<bos><start_of_turn>user
    Prompt:{Based on text, give the 20 most appropriate words to fill [MASK]. The output should be a list of 20 words with no any other words}.
    Text:{The coolest geek shopping list ever: 129 of the best screens, cams, phones, games and gadgets of the year, from Wired magazine. It's a news about [MASK]} .
    Desired format: {[word1,word2,...,word20]}<end_of_turn>
    <start_of_turn>model
    [tech, update, release, news, gadget, product, review, roundup, list, collection, best, annual, must-haves, trends, innovations, future, electronics, techie, enthusiasts, aficionados, aficionados]<eos>
    """
    prompt_head = "Based on text, give the 20 most appropriate words to fill [MASK]. The output should be a list of 20 words with no any other words"
    prompt_tail = "It's a news about [MASK]"
    chat = [
        {
            "role": "user",
            "content": "Prompt:{%s}. \nText:{%s %s} . \nDesired format: {[word1,word2,...,word20]}"
            % (prompt_head, text, prompt_tail),
        },
    ]
    prompt = tokenizer.apply_chat_template(
        chat, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")

    outputs = model.generate(
        input_ids=inputs.to(model.device), max_new_tokens=150, do_sample=False
    )  # 采样温度)
    outputs = tokenizer.decode(outputs[0])
    # 使用正则表达式提取包含关键词的数组

    return outputs


def prompt_for_keywords_yesno(keywords, text, label, label_list, tokenizer, model):
    """
    根据给定的keywords，判断text是否属于label（以此为其打上弱标签）

    参数：
    - keywords (list): 一维数组，包含若干关键词。
    - text (str): 待标记的文本
    -label (int): 所属的类别。
    -label_list (list): 类别对应的标签名称，e.g. ["World","Sports","Business","Sci/Tech"]。
    -tokenizer:初始化后的语言模型
    -model:初始化后的语言模型
    返回：
    大语言模型的输出。
    格式为:<bos><start_of_turn>user
        Prompt:{Does any words in the Keywords can fill the [MASK] consistent with the original intention?Only the most direct semantics are considered. Keywords contains a set of words related to economics. Only answer in Yes or No with no any other words}.
        Text:{JERUSALEM Israeli security officials say the nation is preparing to hand over security in the northern Gaza Strip to Palestinians well before Israel withdraws from the area in mid-2005. It's a news about [MASK]} .
        Keywords:['economic crisis', 'default', 'negotiations', 'agreement', 'restructuring', 'payment', 'terms', 'development', 'effort', 'process', 'speculation', 'market', 'leadership change', 'Sudden departure', 'downfall', 'crisis', 'Market crash', 'property slump', 'stagnation', 'recession', 'speculation', 'uncertainty', 'economic growth', 'figures', 'growth rate', 'month-on-month', 'trend', 'Embezzlement', 'Corruption', 'Securities', 'Economic', 'Business', 'Financial', 'Fraud']
        Desired format: {yes|no}<end_of_turn>
        <start_of_turn>model
        No<eos>
    """
    question = f"Does any words in the Keywords can fill the [MASK] consistent with the original intention? Only the most direct semantics are considered. Keywords contains a set of words related to {label_list[label]}."
    prompt_tail = "Only answer in Yes or No with no any other words"
    text_tail = "It's a news about [MASK]"
    desired_format = "yes|no"
    chat = [
        {
            "role": "user",
            "content": "Prompt:{%s %s}. \nText:{%s %s} . \nKeywords:%s \nDesired format: {%s}"
            % (question, prompt_tail, text, text_tail, keywords, desired_format),
        },
    ]
    prompt = tokenizer.apply_chat_template(
        chat, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
    outputs = model.generate(
        input_ids=inputs.to(model.device), max_new_tokens=150, do_sample=False
    )  # 采样温度)
    outputs = tokenizer.decode(outputs[0])
    # 使用正则表达式提取包含关键词的数组
    return outputs


def keywords_clean(key_word):
    """
    从各种形式的输出中提取关键词

    参数：
    - key_word (str): 大语言模型的输出，可能由多种形式。
    返回：
    - keyword_array (list): 提取后的关键词列表
    """

    match1 = re.search(r"<start_of_turn>model\n\[(.*?)\]<eos>", key_word)
    match2 = re.search(r"<start_of_turn>model\n\{(.*?)\}<eos>", key_word)
    match3 = re.search(r"<start_of_turn>model\s*(.*?-.*?)\s*<eos>", key_word, re.DOTALL)

    if match1:
        keyword_array_str = match1.group(1)
        keyword_array = [word.strip() for word in keyword_array_str.split(",")]
    elif match2:
        keyword_array_str = match2.group(1)
        keyword_array = [word.strip() for word in keyword_array_str.split(",")]

    elif match3:
        keyword_list_str = match3.group(1)
        keyword_array = [word.strip() for word in keyword_list_str.split("\n- ")]
        keyword_array[0] = keyword_array[0].split("- ")[-1]
        # print(keyword_array)
    return keyword_array


def LF_employed(
    tokenizer,
    model,
    flag,
    label_list=["World", "Sports", "Business", "Sci/Tech"],
    data_path="./wrench_data/classification/agnews/train.json",
    rule_path="./data/rule.json",
):
    """
    根据给定的关键词形式的LF为数据添加弱标签

    参数：
    - keywords (list): 一维数组，包含若干关键词。
    -label (int): 所属的类别。
    -label_list (list): 类别对应的标签名称，e.g. ["World","Sports","Business","Sci/Tech"]。
    -tokenizer:初始化后的语言模型
    -model:初始化后的语言模型
    -data_path(str):待标记数据的路径
    -rule_path(str):LF的路径
    返回：
    data(json): 返回添加标记后的json文件
    """

    with open(data_path, "r") as f:
        # 路径之后要变
        data = json.load(f)

    with open(rule_path, "r") as f:
        rules = json.load(f)

    for i, rule in enumerate(rules):
        for key, item in tqdm(data.items()):
            text = item["data"]["text"]
            if flag == 0:
                answer = prompt_for_keywords_yesno(
                    rule["keywords"],
                    text,
                    labelToNum(label_list, rule["label"]),
                    label_list,
                    tokenizer,
                    model,
                )
            else:
                answer = prompt_for_yesno(rule["prompt"], text, model, tokenizer)
            match = re.search(r"<start_of_turn>model\n\s*(.*?)<eos>", answer, re.DOTALL)
            if match:
                choice = match.group(1).lower()  # 转换为小写形式
                choice_num = (
                    labelToNum(label_list, rule["label"]) if choice == "yes" else -1
                )
            item["weak_labels"].append(choice_num)

    # 将处理后的结果保存为一个新的 JSON 文件
    with open("newdata_LF.json", "w") as f:
        json.dump(data, f, indent=4)
        return data


def LF(question, answer, label, model, tokenizer, device="cuda"):

    return


def embedding_model_init(model_id="./model/bert-base-uncased"):
    """
    加载bert模型，用于计算嵌入，将其放在gpu上
    """
    model_name = model_id

    tokenizer = BertTokenizer.from_pretrained(model_name)
    model = BertModel.from_pretrained(model_name)
    model = model.to("cuda")

    return model, tokenizer


def labelToNum(label_list, label):
    """
    这个函数接收一个标签列表和一个单独的标签作为输入。
    它返回给定标签在列表中的位置（索引）。

    输入:
    - label_list: 一个字符串列表，表示标签。
      例如: ["World", "Sports", "Business", "Sci/Tech"]
    - label: 一个字符串，表示要在列表中查找的标签。
      例如: "World"

    输出:
    - 一个整数，表示标签在列表中的索引位置。
      如果找到标签，返回从零开始的索引。
      如果没有找到标签，返回-1。

    示例:
    >>> labelToNum(["World", "Sports", "Business", "Sci/Tech"], "World")
    0
    >>> labelToNum(["World", "Sports", "Business", "Sci/Tech"], "Business")
    2
    >>> labelToNum(["World", "Sports", "Business", "Sci/Tech"], "Politics")
    -1
    """

    # 检查标签是否在列表中，并返回其索引
    if label in label_list:
        return label_list.index(label)
    else:
        # 如果没有找到标签，返回-1
        return -1


def get_embedding(one_word, tokenizer, model):
    """
    将文本转为嵌入

    one_word:一个单词（预测出的20个关键词或规则内的词语）
    tokenizer、model：均为bert模型
    """
    inputs = tokenizer(one_word, return_tensors="pt", padding=True, truncation=True)
    inputs = inputs.to("cuda")

    with torch.no_grad():
        outputs = model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1)

    return embedding


def keyword_similarity(
    keyword_list,
    tokenizer,
    model,
    label_list=["World", "Sports", "Business", "Sci/Tech"],
):
    """
    将关键词与每一个规则中的词语的嵌入进行比较，保留最高的相似度和对应规则的标签值
    自动读取当前规则文件中的规则

    参数：
    -keyword_list：预测的20个关键词，以列表形式传入
    -tokenizer、model：载入bert模型计算嵌入

    """
    with open("./data/rules_keywords.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    simi_list = []
    for k, one_keyword in enumerate(keyword_list):
        max_simi = 0
        max_label = ""
        for i, one_data in enumerate(data):
            for j, one_word in enumerate(one_data["keywords"]):
                simi = cosine_similarity(
                    get_embedding(one_word, tokenizer, model).cpu(),
                    get_embedding(one_keyword, tokenizer, model).cpu(),
                )
                similarity = float(simi[0, 0])
                if similarity > max_simi:
                    max_simi = similarity
                    max_label = one_data["label"]
        one_simi = {}
        one_simi["keyword"] = one_keyword
        one_simi["similarity"] = round(max_simi, 3)
        one_simi["label"] = labelToNum(
            ["World", "Sports", "Business", "Sci/Tech"], max_label
        )
        simi_list.append(one_simi)

    return simi_list


def keyword_similarity(keyword_list, tokenizer, model):
    """
    将关键词与每一个规则中的词语的嵌入进行比较，保留最高的相似度和对应规则的标签值
    自动读取当前规则文件中的规则

    参数：
    -keyword_list：预测的20个关键词，以列表形式传入
    -tokenizer、model：载入bert模型计算嵌入

    """
    with open("./data/rules_keywords.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    simi_list = []
    for k, one_keyword in enumerate(keyword_list):
        max_simi = 0
        max_label = ""
        for i, one_data in enumerate(data):
            for j, one_word in enumerate(one_data["keywords"]):
                simi = cosine_similarity(
                    get_embedding(one_word, tokenizer, model).cpu(),
                    get_embedding(one_keyword, tokenizer, model).cpu(),
                )
                similarity = float(simi[0, 0])
                if similarity > max_simi:
                    max_simi = similarity
                    max_label = one_data["label"]
        one_simi = {}
        one_simi["keyword"] = one_keyword
        one_simi["similarity"] = round(max_simi, 3)
        one_simi["label"] = labelToNum(
            ["World", "Sports", "Business", "Sci/Tech"], max_label
        )
        simi_list.append(one_simi)

    return simi_list


def load_data_from_json(data_path, data_name):
    with open(data_path + data_name + ".json", "r") as f:
        data = json.load(f)
        # print(data)

    true_labels = []
    weak_labels = []

    num_labelers = len(next(iter(data.values()))["weak_labels"])
    weak_labels = [[] for _ in range(num_labelers)]

    for item in data.values():
        true_labels.append(item["label"])
        for i, weak_label in enumerate(item["weak_labels"]):
            weak_labels[i].append(weak_label)
    # print(true_labels)
    return true_labels, weak_labels


def evaluate_weak_labelers(data_path, data_name):
    # 输入输出格式：
    # 输入：
    #  -data_path、data_name：存储标记后文件的位置
    # 输出：
    # - metrics: List[Dict[str, Dict[str, float | Dict[int, float] | Dict[int, Dict[int, int]]]]]
    #   其中每个字典包含一个弱标记器的评估指标，
    #   键为指标名称，值为另一个字典，包含该指标下每个标签的值，例如：
    #   [
    #       {
    #           'name': 'LF_1',
    #           'accuracy': 0.67,
    #           'precision': {2: 0.5, 3: 1.0},
    #           'recall': {2: 1.0, 3: 0.5},
    #           'f1_score': {2: 0.67, 3: 0.67},
    #           'confusion_matrix': {2: {2: 1, 3: 0}, 3: {2: 1, 3: 1}},
    #           'conflict_count': 1,
    #           'conflicts_with': {'LF_2': 1, 'LF_3': 2}
    #       },
    #       ...
    #   ]
    true_labels, weak_labels = load_data_from_json(data_path, data_name)
    num_labelers = len(weak_labels)
    metrics = []

    conflict_matrix = [[0 for _ in range(num_labelers)] for _ in range(num_labelers)]
    total_conflict_count = 0

    for i in range(len(true_labels)):
        labels = [
            (j, weak_labels[j][i])
            for j in range(num_labelers)
            if weak_labels[j][i] != -1
        ]
        if len(labels) > 1:
            for (j1, label1), (j2, label2) in combinations(labels, 2):
                if label1 != label2:
                    conflict_matrix[j1][j2] += 1
                    conflict_matrix[j2][j1] += 1
                    total_conflict_count += 1

    for i in range(num_labelers):
        weak_labeler = weak_labels[i]
        valid_indices = [idx for idx, label in enumerate(weak_labeler) if label != -1]

        filtered_true_labels = [true_labels[idx] for idx in valid_indices]
        filtered_weak_labels = [weak_labeler[idx] for idx in valid_indices]

        coverage = len(valid_indices) / len(true_labels)

        if not filtered_true_labels:
            metrics.append(
                {
                    "name": f"LF_{i+1}",
                    "accuracy": 0.0,
                    "precision": {},
                    "recall": {},
                    "f1_score": {},
                    "confusion_matrix": {},
                    "conflict_count": 0,
                    "conflicts_with": {},
                    "coverage": coverage,
                }
            )
            continue

        accuracy = accuracy_score(filtered_true_labels, filtered_weak_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            filtered_true_labels, filtered_weak_labels, average=None, zero_division=0
        )

        labels = sorted(set(filtered_true_labels))
        precision_dict = {label: precision[i] for i, label in enumerate(labels)}
        recall_dict = {label: recall[i] for i, label in enumerate(labels)}
        f1_dict = {label: f1[i] for i, label in enumerate(labels)}

        conf_matrix = confusion_matrix(
            filtered_true_labels, filtered_weak_labels, labels=labels
        )
        conf_matrix_dict = {
            label: {l: conf_matrix[i][j] for j, l in enumerate(labels)}
            for i, label in enumerate(labels)
        }

        conflicts_with = {
            f"LF_{j+1}": conflict_matrix[i][j]
            for j in range(num_labelers)
            if conflict_matrix[i][j] > 0
        }

        metrics.append(
            {
                "name": f"LF_{i+1}",
                "accuracy": accuracy,
                "precision": precision_dict,
                "recall": recall_dict,
                "f1_score": f1_dict,
                "confusion_matrix": conf_matrix_dict,
                "conflict_count": sum(conflicts_with.values()),
                "conflicts_with": conflicts_with,
                "coverage": coverage,
            }
        )

    return metrics


def evaluate_current_lf(data_path, data_name, n):
    # 当更新规则时,只评估当前传入的id为n的lf(n即Lf的顺序索引,即id)产生的弱标记数据

    true_labels, weak_labels = load_data_from_json(data_path, data_name)
    weak_labeler = weak_labels[n]

    # 找到有效的标签索引
    valid_indices = [idx for idx, label in enumerate(weak_labeler) if label != -1]
    filtered_true_labels = [true_labels[idx] for idx in valid_indices]
    filtered_weak_labels = [weak_labeler[idx] for idx in valid_indices]

    coverage = len(valid_indices) / len(true_labels)

    if not filtered_true_labels:
        accuracy = 0.0
    else:
        accuracy = accuracy_score(filtered_true_labels, filtered_weak_labels)

    metrics = {"name": f"LF_{n+1}", "accuracy": accuracy, "coverage": coverage}

    return metrics


def parse_json_string(json_string):
    # 移除多余的空格和换行符
    json_string = json_string.strip()

    # 匹配最外层的大括号中的内容
    pattern = r'"([^"]+)":\s*(\[[^\]]+\]|\{[^\}]+\}|".+?"|[^\s,]+)'
    matches = re.findall(pattern, json_string, re.DOTALL)

    result_dict = {}
    for key, value in matches:
        # 去掉外层的引号并去掉前后空格
        key = key.strip().strip('"')

        # 处理嵌套的字典
        if value.startswith("{") and value.endswith("}"):
            nested_dict = parse_json_string(value)
            result_dict[key] = nested_dict
        # 处理列表
        elif value.startswith("[") and value.endswith("]"):
            result_dict[key] = re.findall(r'"([^"]+)"', value)
        # 处理字符串值
        elif value.startswith('"') and value.endswith('"'):
            result_dict[key] = value.strip('"')
        else:
            result_dict[key] = value.strip()

    return result_dict


def asking_for_prompt(
    text,
    requirements,
    dataset_type,
    label,
    existing_LF,
    model_name="gpt-4",
    if_explanation=False,
    tail="LF must be a general question. \nResponses must follow Expected format",
    api_key=''
):
    """
    text: text for asking
    requirements：dim for control   e.g. data_dict = {'coverage': 'low','accuracy': 'high','Granularity': 'high','Generalization': 'high','Specificity': 'low'}
    dataset_type: e.g. 'Sentiment classification'
    dataset_label: e.g. "Positive"
    model_name: Selected model type
    is_exaplanation: False: Only return prompt. True: following a explanation
    tail: control the output of gpt

    Output: the prompt LF e.g. '{Prompt: Does the review primarily discuss positive aspects of the movie such as good actors, strong direction, and enjoyable storyline?}'
    """
    # client = OpenAI(
    #     base_url="https://api.openai-proxy.org/v1",
    #     api_key=api_key,
    # )
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": api_key}
    Descriptions = f"This is a sample from a {dataset_type} dataset, where the label is {label}, combined this sample to give a prompt label function for weakly supervised classification of the dataset. LF must be a general question. You must answer in the following JSON object format"
    Requirements = ", ".join(
        [f"{key}: '{value}'" for key, value in requirements.items()]
    )
    Expected_format = "Prompt: <prompt LF>"
    Existing_LF = existing_LF
    Tail = tail if if_explanation == False else ""
    content = (
        "Text:{%s}.\nRequirements:{%s}\nExisting LFs:{%s}\nDescriptions{%s}\nExpected format: {%s}\n%s"
        % (text, Requirements, Existing_LF, Descriptions, Expected_format, Tail)
    )
    # print(content)
    messages = (
        [
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    data = {"model": model_name, "messages": messages, "type": "json_object"}
    chat_completion = requests.post(url, headers=headers, data=json.dumps(data)).json()
    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": content,
    #         }
    #     ],
    #     model=model_name,
    #     response_format={"type": "json_object"},
    # )
    print(chat_completion.choices[0].message.content)

    result_dict = parse_json_string(chat_completion.choices[0].message.content)
    # # 提取花括号 {} 内的内容
    # pattern = r"\{(.+?)\}"
    # matches = re.findall(pattern, chat_completion.choices[0].message.content, re.DOTALL)

    # # print("maches---")
    # # print(matches)
    # # 将提取的内容存储为字典
    # result_dict = {}
    # for match in matches:
    #     # 使用 json.loads 解析提取的 JSON 内容
    #     extracted_dict = json.loads(f"{{{match}}}")
    #     result_dict.update(extracted_dict)
    return result_dict


def asking_for_keywords(
    text,
    dataset_type,
    label,
    num_of_keywords,
    model_name="gpt-4",
    if_explanation=False,
    tail="",
    api_key='',
):
    """
    text: text for asking
    requirements：dim for control   e.g. data_dict = {'coverage': 'low','accuracy': 'high','Granularity': 'keywords','Generalization': 'low','Specificity': 'high'}
    dataset_type: e.g. 'Sentiment classification'
    dataset_label: e.g. "Positive"
    model_name: Selected model type
    is_exaplanation: False: Only return prompt. True: following a explanation
    tail: control the output of gpt

    Output: the list of keywords e.g. '[great, noble, emotion, well, quickly, better, enjoy, storyline, direction, addressed]'
    """
    # client = OpenAI(
    #     base_url="https://api.openai.com/v1/chat/completions",
    #     api_key=api_key,
    # )
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": api_key}
    Descriptions = f"This is a sample from a {dataset_type} dataset, where the label is {label},  give the {num_of_keywords} most appropriate words for a prompt label function for weakly supervised classification of the dataset. Words can come from the text, or from associations"
    Expected_format = f"[word1,word2,...,word{num_of_keywords}]"
    Tail = (
        f"The output should be a list of {num_of_keywords} words with no any other words"
        if if_explanation == False
        else ""
    )
    content = "Text:{%s}. \nDescriptions{%s}\nExpected format: {%s}\n%s" % (
        text,
        Descriptions,
        Expected_format,
        Tail,
    )
    # print(content)
    messages = (
        [
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    data = {"model": model_name, "messages": messages}
    chat_completion = requests.post(url, headers=headers, data=json.dumps(data)).json()
    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": content,
    #         }
    #     ],
    #     model=model_name,
    # )
    return chat_completion.choices[0].message.content


def asking_for_dims(
    text,
    dataset_type,
    label,
    model_name="gpt-4",
    if_explanation=False,
    dim_num=6,
    tail="LF must be a general question. \nResponses must follow Expected format",
    api_key='',
):
    """
    text: text for asking
    dataset_type: e.g. 'Sentiment classification'
    dataset_label: e.g. "Positive"
    model_name: Selected model type
    dim_num： number for the dims
    Output: dim for control   e.g. data_dict = {'coverage': 'low','accuracy': 'high','Granularity': 'high','Generalization': 'high','Specificity': 'low'}
    """
    # client = OpenAI(
    #     base_url="https://api.openai-proxy.org/v1",
    #     api_key=api_key,
    # )
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": api_key}
    Descriptions = f"This is a sample from a {dataset_type} dataset, where the label is {label}, combined the datapoint to give prompt label functions for weakly supervised classification of the dataset. First, define {dim_num} dimensions which can control, classify and evaluate prompt LFs，giving all possible values for each dimension. Dimensions should be used for prompt LF generation and should not be directly related to {dataset_type}.Then, choose the most appropriate values for each dimension and use them to generate an optimal prompt LF. I will give you an EXAMPLE of Dimension and value. Prompt LF must be a general question for a yes or no answer. You must answer in the following JSON object format"
    Example = "{Coverage:[Low,Moderate,High]}"
    Expected_format = " {<Dimension_name>: [Value1,Value2,...]\n<Dimension_name>:[Value1,Value2,...]\n...\n<Dimension_name>:[Value1,Value2,...]\nOptimality:{<Dimension_name>:<Value>,<Dimension_name>:<Value>,LF:<prompt LF>}} "
    content = "{Text:%s. \nDescriptions:%s\nExample:%s\nExpected format: %s\n}" % (
        text,
        Descriptions,
        Example,
        Expected_format,
    )
    print(content)
    messages = (
        [
            {
                "role": "user",
                "content": content,
            }
        ],
    )
    data = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.2,
        "type": "json_object",
    }
    chat_completion = requests.post(url, headers=headers, data=json.dumps(data)).json()
    print(chat_completion)
    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": content,
    #         }
    #     ],
    #     response_format={"type": "json_object"},
    #     model=model_name,
    #     temperature=0.2,
    # )
    # print(chat_completion.choices[0].message.content)
    result_dict = parse_json_string(chat_completion.choices[0].message.content)

    # # 提取花括号 {} 内的内容
    # pattern = r'\{(.+?)\}'
    # matches = re.findall(pattern, chat_completion.choices[0].message.content, re.DOTALL)

    # # 将提取的内容存储为字典
    # result_dict = {}
    # for match in matches:
    #     # 使用 json.loads 解析提取的 JSON 内容
    #     extracted_dict = json.loads(f"{{{match}}}")
    #     result_dict.update(extracted_dict)
    return result_dict


def transform_data(data):
    # 将首次推荐的维度和LF转换为目标格式
    result = {"dimension": [], "degree": {}, "Prompt": {}}
    # 获取 'dimension' 列表
    for key in data:
        if key != "Optimality":
            result["dimension"].append(key)
            result["degree"][key] = data[key]

    # 处理 'Prompt' 部分
    for key, value in data["Optimality"].items():
        if key in result["degree"]:
            result["Prompt"][key] = [value]  # 转换为列表形式
        else:
            result["Prompt"][key] = value  # 保持原样

    # 处理 'Prompt' 中的其他字段
    if "LF" in data["Optimality"]:
        result["Prompt"]["LF"] = data["Optimality"]["LF"]
    if "Focus" in result["dimension"]:
        result["dimension"].remove("Focus")
        result["dimension"].append("Intent")

    return result


# v1版本:
def prompt_for_yes_no_v1(prompt, text, tokenizer, model):
    prompt_head = prompt
    prompt_tail = "Only answer Yes or No.\n\n"
    desired_format = "yes|no"
    chat = [
        {
            "role": "user",
            "content": "Prompt:{%s %s}. \nText:{%s} . \nDesired format: {%s}"
            % (prompt_head, prompt_tail, text, desired_format),
        }
    ]
    prompt = tokenizer.apply_chat_template(
        chat, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
    # inputs=torch.cat([inputs,inputs],dim=0)
    # print(inputs.shape)
    outputs = model.generate(
        input_ids=inputs.to(model.device), max_new_tokens=150, do_sample=False
    )  # 采样温度)
    outputs = tokenizer.decode(outputs[0])
    # 使用正则表达式提取包含关键词的数组
    return outputs


def convert_to_serializable(obj):
    if isinstance(obj, (np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    return obj


def calculate_conflicts_and_redundancies(dataset_name, round_time):
    # 得先计算影响分数
    # 冲突-冗余矩阵图的数据:冲突为负值,冗余为正值,并将左对角线上的0值替换为当前LF的影响分数
    with open(f"./data/labelFunction/{dataset_name}/train.json", "r") as f1:
        data = json.load(f1)
    with open(f"./data/labelFunction/{dataset_name}/{round_time}/LF.json", "r") as f2:
        rules = json.load(f2)

    num_rules = len(rules)

    conflicts = [[0] * num_rules for _ in range(num_rules)]
    redundancies = [[0] * num_rules for _ in range(num_rules)]

    for item in data.values():
        weak_labels = item["weak_labels"]
        for i in range(num_rules):
            for j in range(i + 1, num_rules):
                if weak_labels[i] != -1 and weak_labels[j] != -1:
                    if weak_labels[i] != weak_labels[j]:
                        conflicts[i][j] -= 1  # 将冲突的值设为负数
                    elif weak_labels[i] == weak_labels[j]:
                        redundancies[i][j] += 1

    conf_redun_matrix = [
        [conflicts[i][j] + redundancies[i][j] for j in range(num_rules)]
        for i in range(num_rules)
    ]

    # 将矩阵左对角线上的数值替换为该条规则的影响分数
    with open(
        f"./data/labelFunction/{dataset_name}/{round_time}/LFsif.json", "r"
    ) as f3:
        sifs = json.load(f3)
        for i in range(num_rules):
            conf_redun_matrix[i][i] = round(sifs[i]["LF_sif"], 3)

    # 保存数组为.npy文件
    np.save("conf_redun_matrix.npy", conf_redun_matrix)

    return conf_redun_matrix


def find_index_by_id(lf, target_id):
    # 找到规则集合中更新的规则,返回
    for index, obj in enumerate(lf):
        if obj["id"] == target_id:
            return index
    return -1  # 返回 -1 表示未找到


def analyze_weak_labels(weak_labels):
    # 评估弱标签标记情况：冲突1，正常0，无效-1
    # 使用集合存储非-1标签
    label_set = {label for label in weak_labels if label != -1}

    # 根据集合的大小和内容返回相应的值
    if len(label_set) == 0:
        return -1  # 全是-1
    elif len(label_set) > 1:
        return 1  # 存在两种及以上标签，即为冲突
    else:
        return 0  # 只有一种有效标签


def influence_score(data, round_time):
    # 计算三种组件的影响分数:data、data_prompt、prompt
    """
    计算各组件影响分数
    输入格式:
    data:'sms'  (str)
    round_time:'Round_1'
    输出:
    prompt_data_sif.json:  [{
        "dataKey": "332", "dataif": 1.6666289269924164,"label":0,
        "conflictFlag":1,(标志位，-1表示一直未被标记，0表示正常，1表示冲突)
        "weak_labels":[-1,1,0...]
        "promptsif": {
            "LF0": 0.108804851770401,
            "LF1": 0.8979405164718628,
            "LF2": 0.6598835587501526,
            "LF3": 0.0,
            "LF4": 0.0
        }},...]
    LFsif.json:   [{"LF_id": 0,"LF_sif": 13.390268325805664},...]
    """

    dataset_home = "./data/labelFunction"
    device = torch.device("cuda")
    train_data, valid_data, test_data = load_dataset(
        dataset_home,
        data,
        extract_feature=True,
        extract_fn="bert",
        cache_name="bert",
        model_name="./model/bert-base-cased",
        device=torch.device("cuda"),
    )
    label_model = FlyingSquid()
    label_model.fit(dataset_train=train_data, dataset_valid=valid_data)

    L = np.array(train_data.weak_labels)
    aggregated_soft_labels = label_model.predict_proba(train_data)

    explainer = Explainer(train_data.n_lf, train_data.n_class)
    approx_w = explainer.approximate_label_model(L, aggregated_soft_labels)
    if_type = "sif"  # 'sif'源感知 or 'relatif' or 'if'普通影响函数
    mode = "RW"  # 重新加权方法（只有此方法下影响力的加和属性才是成立的） or 'WM'权重移动 or 'normal'
    lr, weight_decay, epochs, batch_size = 0.01, 0.0, 10, 32
    IF_score = explainer.compute_IF_score(
        L,
        np.array(train_data.features),
        np.array(valid_data.features),
        np.array(valid_data.labels),
        if_type=if_type,
        mode=mode,
        lr=lr,
        weight_decay=weight_decay,
        epochs=epochs,
        batch_size=batch_size,
        device=device,
    )

    Lf_num = len(IF_score[0])
    prompt_data_if = np.sum(IF_score, axis=2)

    # 将每个数据中打上弃权的规则索引找到,并将对应分数赋值为0->规则的得分\数据样本得分\数据-规则得分都应该改变
    with open(f"./data/labelFunction/{data}/train.json", "r") as f2:
        labelsData = json.load(f2)

        data_related_sif = []
        for i, (key, item) in enumerate(labelsData.items()):
            # 单条数据的key值不是索引,开发集和无标签数据集中重复key的具体值不相同,因此此处采用顺序索引来找数据
            # 第i-1个数据,第LF_index-1个规则
            one_data_related = {
                "dataKey": key,
                "label": item["label"],
                "dataif": 0,
                "promptsif": {},
            }
            for LF_index in range(Lf_num):
                if item["weak_labels"][LF_index] == -1:
                    prompt_data_if[i][LF_index] = 0

                one_data_related["promptsif"][f"LF{LF_index}"] = prompt_data_if[i][
                    LF_index
                ].astype(float)
                one_data_related["dataif"] += prompt_data_if[i][LF_index].astype(float)
                one_data_related["weak_labels"] = item["weak_labels"]
                one_data_related["conflictFlag"] = analyze_weak_labels(
                    item["weak_labels"]
                )

            data_related_sif.append(one_data_related)

    with open(
        f"./data/labelFunction/{data}/{round_time}/prompt_data_sif.json", "w"
    ) as new_file1:
        json.dump(data_related_sif, new_file1)

    prompt_if = np.sum(prompt_data_if, axis=0).astype(float)
    prompt_if_result = [
        {"LF_id": j, "LF_sif": prompt_if[j]} for j in range(len(prompt_if))
    ]

    with open(f"./data/labelFunction/{data}/{round_time}/LFsif.json", "w") as new_file2:
        json.dump(prompt_if_result, new_file2)


def sort_LF(data, round_time):
    # 对LF排序，相同标签的相邻
    with open(f"./data/labelFunction/{data}/{round_time}/LF.json", "r") as f2:
        labelsData = json.load(f2)
        lf_dict = {}

    for item in labelsData:
        label = item["label"]
        lf_id = f"LF{item['id']}"
        if label not in lf_dict:
            lf_dict[label] = {}
        lf_dict[label][lf_id] = item

    sorted_lf_dict = {
        label: dict(sorted(lf_items.items(), key=lambda x: x[0]))
        for label, lf_items in lf_dict.items()
    }

    lf_list = []
    label_list = []

    # Populate the lists
    for label, items in sorted_lf_dict.items():
        for lf_id in items:
            lf_list.append(lf_id)
            label_list.append(label)
    return lf_list, label_list


def classify_data(data, ruleLabel, index):
    categories = {"wrong": [], "miss": [], "same": [], "correctMiss": []}

    for key, item in data.items():
        weak_label_at_index = item["weak_labels"][index]
        original_label = item["label"]

        if weak_label_at_index == original_label and original_label == ruleLabel:
            category = "same"

        if ruleLabel == original_label and weak_label_at_index == -1:
            category = "miss"

        if weak_label_at_index != -1 and ruleLabel != original_label:
            category = "wrong"

        if weak_label_at_index == -1 and original_label != ruleLabel:
            category = "correctMiss"

        item["category"] = category
        item["index"] = key
        categories[category].append(item)

    # 合并分类后的数据
    sorted_data = (
        categories["wrong"]
        + categories["miss"]
        + categories["same"]
        + categories["correctMiss"]
    )
    return sorted_data


def get_sorted_samples(dataset, index, sort_order):
    # 读取样本数据
    with open(f"./data/unlabel/{dataset}.json", "r") as f2:
        samples = json.load(f2)

    # 读取相似性矩阵
    sim_matrix = np.load(f"data/unlabel/sim_matrix/{dataset}.npy")
    num_samples = sim_matrix.shape[0]

    if index < 0 or index >= num_samples:
        raise ValueError(f"Index {index}超出界限")

    # 获取指定索引的相似性向量
    sim_vector = sim_matrix[index]

    # 获取排序索引
    if sort_order == 0:  # 从高到低
        sorted_indices = np.argsort(-sim_vector)  # 负号用于从高到低排序
    elif sort_order == 1:  # 从低到高
        sorted_indices = np.argsort(sim_vector)
    else:
        raise ValueError("Invalid sort_order. Use 0 for descending or 1 for ascending.")

    # 不包括自身
    sorted_indices = [i for i in sorted_indices if i != index]

    # 将目标索引置于第一位
    sorted_indices.insert(0, index)

    # 返回排序后的样本，并为每个样本添加相似性属性
    sorted_samples = {}
    for idx in sorted_indices:

        sample = samples[str(idx)]
        sample["similarity"] = float(sim_vector[idx])  # 添加相似性属性
        sorted_samples[str(idx)] = sample

    min_similarity = min(sample["similarity"] for sample in sorted_samples.values())

    return sorted_samples, min_similarity


def estimate_missing_points(a, b, k):
    """
    使用k近邻算法推断b矩阵中剩余点的坐标
    参数：
    a: 2D numpy array, 大小为(n, d)，表示n个已知点的坐标
    b: 2D numpy array, 大小为(n+m, n+m)，表示相似性矩阵，前n行对应a中已知点
    k: int, 使用k个最近邻来推断坐标

    返回：
    estimated_points: 2D numpy array, 大小为(m, d)，表示推断的m个点的坐标
    """
    n = a.shape[0]  # 已知点的个数
    m = b.shape[0] - n  # 需要推断的点的个数

    # 使用KNN找到每个未知点的k个最近邻
    knn = NearestNeighbors(n_neighbors=k, metric="precomputed")

    # 只考虑b矩阵的前n行和前n列（表示已知点的相似性）
    knn.fit(b[:n, :n])

    # 对于未知点（b的n+m行中的m行），计算它们到已知点的距离
    distances, indices = knn.kneighbors(b[n:, :n])

    # 根据最近邻的点的坐标，估计未知点的坐标
    estimated_points = np.zeros((m, a.shape[1]))

    for i in range(m):
        # 找到最近的k个点的坐标
        neighbors_coords = a[indices[i]]

        # 使用最近邻点的坐标的加权平均来估计未知点的坐标
        weights = 1 / (distances[i] + 1e-5)  # 防止除以0
        estimated_points[i] = np.average(neighbors_coords, axis=0, weights=weights)

    return estimated_points


def delete_rule(datasetName, delIndex):
    # 规则文件
    with open(f"./data/labelFunction/{datasetName}/Round_1/LF.json", "r") as file:
        LfData = json.load(file)

    # 将删除的规则另外存储
    with open(f"./data/labelFunction/{datasetName}/Round_1/delLF.json", "r") as file5:
        delLFs = json.load(file5)
        delLFs.append(LfData[delIndex])

    with open(f"./data/labelFunction/{datasetName}/Round_1/delLF.json", "w") as f:
        json.dump(delLFs, f)

    del LfData[delIndex]

    # 重新赋值 ID 从删除位置之后的对象开始，并重新存储文件
    for i in range(delIndex, len(LfData)):
        LfData[i]["id"] = i
    with open(f"./data/labelFunction/{datasetName}/Round_1/LF.json", "w") as file2:
        json.dump(LfData, file2)

    # 弱标签文件
    with open(f"./data/labelFunction/{datasetName}/train.json", "r") as file3:
        weakData = json.load(file3)

    for key, value in weakData.items():
        if 0 <= delIndex < len(value["weak_labels"]):
            value["weak_labels"].pop(delIndex)

    with open(f"./data/labelFunction/{datasetName}/train.json", "w") as file4:
        json.dump(weakData, file4)

    return LfData
