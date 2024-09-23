from flask_cors import CORS
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from backend import *
import re
import os


app = Flask(__name__)
cors = CORS(app)

app.config["SERVER_NAME"] = "127.0.0.1:5001"
model, tokenizer = model_init(model_id="/gemma-2-9b-it")

api_key = "YOUR_KEY"


@app.route("/api/show_initial_rules", methods=["POST"])
def show_prompts():
    # 将新的规则集合存储到Json文件中，添加id，并返回所有LF
    dataset = request.json["datasetValue"]
    request_round = "Round_1"

    file_name = "./data/labelFunction/" + dataset + "/" + request_round + "/LF.json"
    if not os.path.isfile(file_name):
        # 创建文件并写入空数组
        with open(file_name, "w") as file:
            json.dump([], file)

    with open(
        "./data/labelFunction/" + dataset + "/" + request_round + "/LF.json", "r"
    ) as file:
        originalLF = json.load(file)
        return jsonify(originalLF)


@app.route("/api/save_rules", methods=["POST"])
def receive_prompts():
    new_lf = request.json["LF"]
    fileName = request.json["datasetName"]
    request_round = "Round_1"

    with open(
        "./data/labelFunction/" + fileName + "/" + request_round + "/LF.json", "r"
    ) as file:
        originalLF = json.load(file)

        # 除了前端给予的key-value外 额外添加/修改
        new_lf["id"] = len(originalLF)
        new_lf["updateFlag"] = 0  # 加入标志位,标志是否迭代过,是1否0,初始值均为0
        new_lf["currentLen"] = 1
        new_lf["promptHistory"] = [new_lf["prompt"]]
        new_lf["designContentList"] = [new_lf["designContent"]]  # 改为列表形式
        new_lf["dataKeyList"] = [new_lf["selectedDataKey"]]  # 改为列表形式

        # 应用弱标记并评估
        with open(f"./data/labelFunction/{fileName}/train.json", "r") as f1:
            data_sample = json.load(f1)
        for key, item in tqdm(data_sample.items()):
            text = item["data"]["text"]
            key_word = prompt_for_yesno(
                new_lf["prompt"], text, model=model, tokenizer=tokenizer
            )
            match = re.search(
                r"<start_of_turn>model\n\s*.*?\b(yes)\b.*?<eos>",
                key_word,
                re.DOTALL | re.IGNORECASE,
            )
            if match:
                choice_num = int(new_lf["label"])  # 如果匹配到"yes"，choice_num设为1
            else:
                choice_num = -1  # 如果没有匹配到"yes"，choice_num设为0
            item["weak_labels"].append(choice_num)
        # 将添加弱标记后的数据重新存储覆盖
        with open(f"./data/labelFunction/{fileName}/train.json", "w") as new_file:
            json.dump(data_sample, new_file)

        # metrics=evaluate_weak_labelers(f"./data/labelFunction/{fileName}/",'train')
        metrics = evaluate_current_lf(
            f"./data/labelFunction/{fileName}/", "train", new_lf["id"]
        )
        serializable_data = convert_to_serializable(metrics)

        print(new_lf)
        # 在LF中加入评估指标,设为列表形式
        new_lf["accuracy"] = [serializable_data["accuracy"]]
        new_lf["coverage"] = [serializable_data["coverage"]]
        originalLF.append(new_lf)

    with open(
        "./data/labelFunction/" + fileName + "/" + request_round + "/LF.json", "w"
    ) as new_file:
        json.dump(originalLF, new_file)

    saveInfor = {"allLF": originalLF, "signal": "success"}

    return jsonify(saveInfor)


@app.route("/api/update_rules", methods=["POST"])
def update_prompts():
    # 获取旧规则id,找到对其进行更新
    # 保存之后自动计算准确率和覆盖率,存入规则文件中
    update_lf = request.json["LF"]
    update_lf_id = request.json["id"]  # int型
    fileName = request.json["datasetName"]
    request_round = "Round_1"

    with open(
        "./data/labelFunction/" + fileName + "/" + request_round + "/LF.json", "r"
    ) as file:
        originalLF = json.load(file)
        # print(originalLF[update_lf_id])

        index = update_lf_id
        originalLF[index]["updateFlag"] = 1  # 更新标志位
        originalLF[index]["currentLen"] += 1
        originalLF[index]["prompt"] = update_lf["prompt"]
        originalLF[index]["promptHistory"].append(update_lf["prompt"])
        originalLF[index]["designContent"] = update_lf["designContent"]

        originalLF[index]["designContentList"].append(update_lf["designContent"])
        originalLF[index]["dataKeyList"].append(update_lf["selectedDataKey"])
        update_lf["label"] = originalLF[index]["label"]

        # 更新准确率和覆盖率
        # 应用弱标记并评估
        with open(f"./data/labelFunction/{fileName}/train.json", "r") as f1:
            data_sample = json.load(f1)
        for key, item in tqdm(data_sample.items()):
            text = item["data"]["text"]
            key_word = prompt_for_yesno(
                update_lf["prompt"], text, model=model, tokenizer=tokenizer
            )
            match = re.search(
                r"<start_of_turn>model\n\s*.*?\b(yes)\b.*?<eos>",
                key_word,
                re.DOTALL | re.IGNORECASE,
            )
            if match:
                choice_num = int(update_lf["label"])  # 如果匹配到"yes"，choice_num设为1
            else:
                choice_num = -1  # 如果没有匹配到"yes"，choice_num设为0
            item["weak_labels"][index] = choice_num
        # 将添加弱标记后的数据重新存储覆盖
        with open(f"./data/labelFunction/{fileName}/train.json", "w") as new_file:
            json.dump(data_sample, new_file)

        metrics = evaluate_current_lf(
            f"./data/labelFunction/{fileName}/", "train", update_lf_id
        )
        serializable_data = convert_to_serializable(metrics)

        # 在LF中更新准确率和覆盖率
        originalLF[index]["accuracy"].append(serializable_data["accuracy"])
        originalLF[index]["coverage"].append(serializable_data["coverage"])

    with open(
        "./data/labelFunction/" + fileName + "/" + request_round + "/LF.json", "w"
    ) as new_file:
        json.dump(originalLF, new_file)

    saveInfor = {"allLF": originalLF, "signal": "success"}
    return jsonify(saveInfor)


@app.route("/api/get_unlabel_data", methods=["POST"])
def unlabel_data():
    # 当切换数据集时,初次加载时执行该函数,返回最初的未标记数据集
    request_data = request.json["datasetValue"]
    # 发送开发集数据
    fileName = "./data/unlabel/" + request_data + ".json"
    result = {"text": [], "labels": []}
    with open(fileName, "r") as f:
        data = json.load(f)
        for index, entry in data.items():
            # label = entry.get('label')
            text = entry.get("data", {}).get("text")
            # 将数据存储到对象中，并添加到结果列表
            result["text"].append(
                {
                    "index": index,
                    # 'label': label,
                    "textLabelValue": "",  # 由用户选择来修改,此时均为空
                    "text": text,
                }
            )
    # 发送标签映射方式
    fileName2 = "./data/dataset_type.json"
    with open(fileName2, "r") as f2:
        labels = json.load(f2)
        result["labels"] = labels[request_data]["labelStr"]
        result["setType"] = labels[request_data]["type"]

        return jsonify(result)


@app.route("/api/get_different_data", methods=["POST"])
def get_different_data():
    # 当切换数据集类型(开发集/未标记集)时,执行该函数
    request_dataset = request.json["datasetValue"]
    request_dataType = request.json["dataType"]
    print(request_dataset)
    print(request_dataType)
    request_round = "Round_1"
    # 发送数据、标签映射方式
    # fileName=f'./data/{request_dataType}/{request_dataset}.json'
    fileName2 = "./data/dataset_type.json"
    result = {"text": [], "labels": [], "setType": []}

    with open(fileName2, "r") as f2:
        labelsInfo = json.load(f2)
        result["labels"] = labelsInfo[request_dataset]["labelStr"]
        result["setType"] = labelsInfo[request_dataset]["type"]

    labelToStr = result["labels"]

    if request_dataType == "unlabel":
        result["text"] = []
        with open(f"./data/unlabel/{request_dataset}.json", "r") as f1:
            data = json.load(f1)
        for index, entry in data.items():
            text = entry.get("data", {}).get("text")
            # 将数据存储到对象中，并添加到结果列表
            result["text"].append(
                {
                    "index": index,
                    "textLabelValue": "",  # 由用户选择来修改,此时均为空
                    "text": text,
                }
            )
    else:
        # 开发集为train文件
        result["text"] = []
        with open(f"./data/labelFunction/{request_dataset}/train.json", "r") as f1:
            data = json.load(f1)
        for index, entry in data.items():
            label = entry.get("label")
            weak_label = entry.get("weak_labels")
            text = entry.get("data", {}).get("text")
            # 将数据存储到对象中，并添加到结果列表
            result["text"].append(
                {
                    "index": index,
                    "weak_label": weak_label,
                    "textLabelValue": labelToStr[
                        label
                    ],  # 展示原始标签,此时前端部分应禁用
                    "text": text,
                }
            )

    return jsonify(result)


@app.route("/api/asking_for_chat", methods=["POST"])
def asking():
    request_data = request.json["data"]
    if request_data["promptForm"] == "prompt":
        # 疑问句形式
        design = request_data["design"]
        result = asking_for_prompt(
            request_data["texts"]["text"],
            design,
            request_data["texts"]["datasetType"],
            request_data["texts"]["labelStr"],
            request_data["existingLF"],
            model_name="chatgpt-4o-latest",
            if_explanation=False,
            tail="LF must be a general question. \nResponses must follow Expected format",
            api_key=api_key,
        )
        return jsonify(result["Prompt"])
        # return 'prompt'

    else:
        # 关键词形式
        result = asking_for_keywords(
            request_data["texts"]["text"],
            request_data["texts"]["datasetType"],
            request_data["texts"]["labelStr"],
            request_data["design"],
            model_name="chatgpt-4o-latest",
            if_explanation=False,
            tail="",
            api_key=api_key,
        )
        result = result.replace("[", "").replace("]", "")
        word_list = [word.strip() for word in result.split(",")]
        # print(word_list)
        return jsonify(word_list)


@app.route("/api/asking_for_dims", methods=["POST"])
def asking_dims():
    request_data = request.json["data"]
    result = asking_for_dims(
        request_data["texts"]["text"],
        request_data["texts"]["datasetType"],
        request_data["texts"]["labelStr"],
        model_name="chatgpt-4o-latest",
        if_explanation=False,
        dim_num=request_data["dimensionNum"],
        tail="LF must be a general question. \nResponses must follow Expected format",
        api_key=api_key,
    )
    resultFormative = transform_data(result)
    return jsonify(resultFormative)


@app.route("/api/draw_matrix", methods=["POST"])
def draw_matrix():
    # 读取弱标记后的开发集数据train,计算混淆矩阵,其中左对角线上的数据已被替换为对应LF的影响分数
    dataset_name = request.json["datasetName"]
    request_round = "Round_1"

    influence_score(dataset_name, request_round)
    final_result = calculate_conflicts_and_redundancies(dataset_name, request_round)
    #     final_result = np.load("conf_redun_matrix.npy")

    return jsonify(final_result)


@app.route("/api/get_influence_score", methods=["POST"])
def draw_radviz():
    dataset_name = request.json["datasetName"]
    request_round = "Round_1"
    # 不必重新计算分数,在画矩阵图时已经调用过sif函数
    with open(
        f"./data/labelFunction/{dataset_name}/{request_round}/prompt_data_sif.json", "r"
    ) as f:
        data = json.load(f)

    lf_list, label_list = sort_LF(dataset_name, request_round)

    result = {"datas": data, "sortLFs": lf_list, "sortLabels": label_list}

    return jsonify(result)


@app.route("/api/query_dataKey_dimension", methods=["POST"])
def query_dataKey():
    datasetName = request.json["datasetValue"]
    dataKey = request.json["selectedDataKey"]
    promptIndex = request.json["currentPromIndex"]
    ruleId = request.json["ruleId"]

    print(dataKey)

    original_infor = {}
    # 获取数据样本
    with open("./data/unlabel/" + datasetName + ".json", "r") as file:
        unlabelDatas = json.load(file)
        original_infor["selectedData"] = unlabelDatas[dataKey]
    # 获取维度值和提示
    with open(
        "./data/labelFunction/" + datasetName + "/Round_1/" + "LF.json", "r"
    ) as f1:
        rulesInf = json.load(f1)
        original_infor["designContent"] = rulesInf[ruleId]["designContentList"][
            promptIndex
        ]
        original_infor["dataKey"] = rulesInf[ruleId]["dataKeyList"][promptIndex]

    return jsonify(original_infor)


@app.route("/api/sort_weak_labels", methods=["POST"])
def sort_weak_labels():
    # 传入数据集名称、打开开发集（train）、传入rule的id，作为弱标签的索引；传入rule指向的标签，判断弱标签排序
    datasetName = request.json["datasetValue"]
    ruleId = request.json["ruleId"]
    ruleLabel = request.json["ruleLabel"]

    fileName2 = "./data/dataset_type.json"
    result = {"text": [], "labels": [], "setType": []}

    with open(fileName2, "r") as f2:
        labelsInfo = json.load(f2)
        result["labels"] = labelsInfo[datasetName]["labelStr"]
        result["setType"] = labelsInfo[datasetName]["type"]

    labelToStr = result["labels"]
    # 开发集为train文件
    result["text"] = []
    with open(f"./data/labelFunction/{datasetName}/train.json", "r") as file:
        weakLabels_data = json.load(file)

        sorted_data = classify_data(weakLabels_data, ruleLabel, ruleId)

        for i in range(len(sorted_data)):
            # 将数据存储到对象中，并添加到结果列表
            result["text"].append(
                {
                    "index": sorted_data[i]["index"],
                    "weak_label": sorted_data[i]["weak_labels"],
                    "textLabelValue": labelToStr[
                        sorted_data[i]["label"]
                    ],  # 展示原始标签,此时前端部分应禁用
                    "text": sorted_data[i]["data"]["text"],
                    "category": sorted_data[i]["category"],
                }
            )
    return jsonify(result)


@app.route("/api/recommend_unlabel", methods=["POST"])
def recommend_unlabel():
    # 传入数据集名称、打开开发集（train）、传入rule的id，作为弱标签的索引；传入rule指向的标签，判断弱标签排序
    datasetName = request.json["datasetValue"]
    index = request.json["dataIndex"]
    sort_order = request.json["sortOrder"]

    sorted_samples, minSim = get_sorted_samples(datasetName, index, sort_order)

    fileName2 = "./data/dataset_type.json"
    result = {"text": [], "labels": [], "setType": []}

    with open(fileName2, "r") as f2:
        labelsInfo = json.load(f2)
        result["labels"] = labelsInfo[datasetName]["labelStr"]
        result["setType"] = labelsInfo[datasetName]["type"]

    # 开发集为train文件
    result["text"] = []
    result["minSim"] = minSim

    for index, entry in sorted_samples.items():
        text = entry["data"]["text"]
        # 将数据存储到对象中，并添加到结果列表
        result["text"].append(
            {
                "index": index,
                "textLabelValue": "",  # 由用户选择来修改,此时均为空
                "text": text,
                "similarity": entry["similarity"],
            }
        )

    return jsonify(result)


@app.route("/api/project_unlabel", methods=["POST"])
def project_unlabel():

    # 传入数据集名称、打开开发集（train）、传入rule的id，作为弱标签的索引；传入rule指向的标签，判断弱标签排序
    datasetName = request.json["datasetName"]
    original_position = request.json["coordinates"]
    sim = np.load(f"./data/sim/{datasetName}.npy")
    # 提取 x 和 y 组成二维数组
    coordinates = np.array([[item["x"], item["y"]] for item in original_position])

    result = estimate_missing_points(coordinates, sim, k=3)
    print(np.max(result[:, 0]))
    print(np.max(result[:, 1]))
    # 将 NumPy 数组转换为字典的列表
    dict_list = [{"x": float(row[0]), "y": float(row[1])} for row in result]
    print(dict_list)

    return jsonify(dict_list)


@app.route("/api/delete_current_rule", methods=["POST"])
def delete_current_rule():
    delIndex = request.json["delIndex"]
    datasetName = request.json["datasetValue"]
    allLF = delete_rule(datasetName, delIndex)

    return jsonify(allLF)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)
