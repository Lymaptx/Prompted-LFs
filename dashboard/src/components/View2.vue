<template>
<div>
    <Card class="myCard">
        <p slot="title">LF Development</p>
        <div id="view2_content">
            <div id="adjustIndex">
                <!-- 调节设计空间 -->
            </div>
            <div class="dataChoose">
                <!-- 写入一般疑问句prompt和展示当前规则 -->
                <div class="labelFunc">
                    <div>
                        <label style="font-weight: bold;">Prompt Form: </label>

                        <select v-model="selectedOption" @change="handleSelectChange()" style="border: none;margin-top: 6px;padding-left: 11px;
    padding-right: 20px;margin-left: 9px;border-bottom: 1.5px solid #8d8d8d;">
                            <option value="2">General question</option>
                            <option value="1">Keywords</option>
                        </select>
                        <el-button @click="inquirePrompts" icon="el-icon-search" size="mini" type="info" style="float: right;" plain>QUERY</el-button>

                    </div>
                    <!-- 两种类型的卡片，一种是选择句子给出关键词，然后选择关键词组成规则；一种是一般疑问句提问 -->
                    <div class="createRule" style="padding-top: 12px;">
                        <!-- 第一种形式：一般疑问句提问 -->
                        <div class="generalQuestion" v-show="!showKeywords">
                            <label style="font-weight: bold;margin-top: 5px;display: inline-block;">Dimension Number:</label>
                            <el-input-number v-model="dimensionNum" size="mini" :min="1" :max="10" label="dimension" style="float:right"></el-input-number>

                            <!-- 调整设计维度与值 -->
                            <div class="dimension">
                                <!-- <div v-for="(item, index) in designLabels" :key="index" class="oneDimension" style="margin-top: 10px;">
                                    <span class="promptText">Prompt {{ item.label }}:</span>
                                    <el-radio-group v-model="item.selectedDegree">
                                        <el-radio-button v-for="(degree, degreeIndex) in degreeLabels" :key="degreeIndex" :label="degree">
                                            {{ degree }}
                                        </el-radio-button>
                                    </el-radio-group>
                                </div> -->
                                <el-form :model="dynamicValidateForm" ref="dynamicValidateForm" class="demo-dynamic" style="margin-top: 8px;">
                                    <div class="allFormPage">
                                        <el-form-item v-for="(dimensionItem,dimensionIndex) in designLabels['dimension']" :key="dimensionIndex" :prop="dimensionItem" :label="dimensionItem+':'">
                                            <div style="display: inline-block;width:19%">
                                                <el-button size="mini" :icon="itemsFixed[dimensionItem] ? 'el-icon-lock' : 'el-icon-unlock'" circle @click="toggleFixed(dimensionItem)" plain style="margin-right:0px"></el-button>
                                                <el-button size="mini" @click.prevent="removeItem(dimensionItem)" type="info" icon="el-icon-delete" circle plain style="margin-left:0"></el-button>
                                            </div>
                                            <!-- v-model绑定复选框的选中状态-->
                                            <div style="display: flex;justify-content: space-around;">
                                                <el-checkbox v-for="(degreeItem,degreeIndex) in designLabels['degree'][dimensionItem]" :key="degreeIndex" v-model="designLabels['Prompt'][dimensionItem]" :label="degreeItem" style="margin-right:10px"></el-checkbox>
                                            </div>

                                        </el-form-item>
                                    </div>
                                    <el-button size="mini" icon="el-icon-refresh-left" type="info" @click="requery" style="margin-left: auto;
    margin-right: auto;display: block;margin-top: 10px;" plain>REQUERY</el-button>
                                </el-form>
                            </div>
                            <div class="recommendPrompt" style="margin-top: 10px;">
                                <span style="font-weight: bold;">Recommended Prompt:</span>
                                <el-input v-model="textValue" type="textarea" :rows="2" style="margin-top: 6px;">
                                </el-input>
                                <table style="margin-top: 10px;">
                                    <tr>
                                        <td><span style="font-weight: bold;">Prompt Answer:</span></td>
                                        <td>
                                            <!-- <ul class="dowebok">
                                                <li><input type="radio" name="radio" data-labelauty="Yes" class="checkInput"></li>
                                                <li><input type="radio" name="radio" data-labelauty="No" class="checkInput"></li>
                                            </ul> -->
                                            <el-button type="success" icon="el-icon-check" size="mini" plain>YES</el-button>
                                            <el-button type="danger" icon="el-icon-close" size="mini" plain>NO</el-button>
                                        </td>
                                    </tr>
                                </table>

                            </div>


                            <el-button type="info" size="mini" icon="el-icon-document-checked" @click="saveLF" style="display: block;margin:10px auto 0 auto">SAVE PROMPT</el-button>
                        </div>
                        <!-- 第二种形式：给出关键词，选择关键词组成规则 -->
                        <div class="keyWords" v-show="showKeywords">
                            <div class="row1">
                                <div class="left">
                                    <span class="promptLogo">C</span>
                                </div>
                                <div class="right">
                                    <el-slider v-model="keywordCount" :min=5 :max=20 style="margin-left: 8px;width: 82%;"></el-slider>
                                </div>
                            </div>

                            <!-- <div class="row3">
                                <div class="left">
                                    <span class="promptLogo">L</span>
                                </div>
                                <div class="right">
                                    <ul class="dowebok" id="originalLabel">
                                        <li><input type="radio" name="radio" data-labelauty="World" class="checkInput"></li>
                                        <li><input type="radio" name="radio" data-labelauty="Sports" class="checkInput"></li>
                                        <li><input type="radio" name="radio" data-labelauty="Business" class="checkInput"></li>
                                        <li><input type="radio" name="radio" data-labelauty="Sci/Tec" class="checkInput"></li>
                                    </ul>
                                </div>
                            </div> -->

                            <div class="row2">
                                <div class="left">
                                    <span class="promptLogo">K</span>
                                </div>
                                <div class="right">
                                    <ul class="dowebok" id="wordsForm"></ul>
                                </div>
                            </div>
                            <el-button class="keywordButton" type="success" :plain="true" icon="el-icon-document-checked" @click="saveLF" style="display: block;margin:0 auto 0 auto">SAVE PROMPT</el-button>

                        </div>

                    </div>

                </div>
                <!-- 所有规则的展示 -->
            </div>
        </div>
    </Card>

</div>
</template>

<script>
import axios from 'axios';
import * as d3 from 'd3';
import * as echarts from 'echarts';

import {
    EventBus
} from '../EventBus';
import {
    globalState
} from '@/main.js'; // 引入全局变量

export default {
    data() {
        return {
            radio1: 'New York',
            heatmap_data: [],
            Label_confu: 'Sample', //左侧数据标题
            flag_text_all: 0, //标志位，为0代表右侧暂空
            Label_confu_left: '',
            Label_confu_right: '',
            base_url: "http://127.0.0.1:5001",
            chooseLabel: '', //在更新规则时,prompts处选中的标签
            showKeywords: false,
            selectedOption: '2', //展示一般疑问句形式
            // 设计维度部分的滑块
            designLabels: {
                'dimension': ['Accurary', 'Coverage'],
                'degree': {
                    'Accurary': ['less', 'medium', 'more'],
                    'Coverage': ['less', 'medium', 'more']
                },
                "Prompt": {
                    "Accurary": ["more"],
                    "Coverage": ["medium"],
                    "LF": ""
                }
            },
            dynamicValidateForm: {
                accuracy: ''
            },
            itemsFixed: {
                'Accurary': false,
                "Coverage": false
            },
            clickTextData: null,
            textValue: '',
            keywordCount: 12,
            keywordsList: null,
            allRules: [],
            dimensionNum: 3,
            updateOrSaveNew: 0, //标志位，确认是迭代旧规则还是存储新规则，默认是存储
            id: null,
            dataKey: null,
            datasetName: null
        };
    },
    mounted() {
        EventBus.$on('eventB', (transmitData) => {
            // 用=>才可以使用this指向，function不行
            this.transmitClickText(transmitData)
        })
        EventBus.$on('eventT', (array) => {
            // 更新迭代就规则时触发该函数，更新之前卡片的维度状态信息
            // 用=>才可以使用this指向，function不行
            this.designLabels = null
            this.showUpdateDesign(array)
        })
        EventBus.$on('eventR', (allRules) => {
            this.allRules = allRules
        })
        this.checkboxBeauty(); //放在最后去美化
    },
    beforeDestroy() {
        // 在组件销毁前解绑事件
        // EventBus.$off('heatmapClick', this.handleHeatmapClick);
    },
    methods: {
        checkboxBeauty: function () {
            $('.checkInput').labelauty();
        },
        checkboxBeauty2: function () {
            $('.checkInput2').labelauty();
        },
        handleSelectChange() {
            this.showKeywords = event.target.value === '1'
        },
        transmitClickText(transmitData) {
            this.clickTextData = transmitData
        },
        showUpdateDesign(array) {
            // 迭代rule时，设计维度恢复之前的历史状态
            this.textValue = array['0']['Prompt']['LF']
            this.designLabels = array['0']
            this.id = array['1']
            this.dataKey = array['2']

            this.datasetName = array['3']
            this.updateOrSaveNew = 1
        },
        inquirePrompts() {
            if (this.showKeywords == false) {
                // 一般疑问句形式:只需返回点击文本、数据集类型、该文本标签、维度个数        
                let data = {
                    "promptForm": "prompt",
                    "texts": this.clickTextData,
                    "dimensionNum": this.dimensionNum
                }
                // console.log("维度中传来的值:")
                // console.log(data)
                // 先遍历fixed,如果有true的维度则保留,false的删掉(判断不为空时)
                const updatedItemsFixed = Object.fromEntries(
                    Object.entries(this.itemsFixed).filter(([key, value]) => value === true)
                );

                this.itemsFixed = updatedItemsFixed
                // 此时仅有fixed的属性,根据itemsFixed去更新designLabels
                let existingKeys = Object.keys(this.itemsFixed);

                // 更新 designLabels.dimension和designLabels.degree
                this.designLabels.dimension = this.designLabels.dimension.filter(key => existingKeys.includes(key));
                this.designLabels.degree = Object.fromEntries(
                    Object.entries(this.designLabels.degree).filter(([key]) => existingKeys.includes(key))
                );

                // 获得所选句子，一并传送给后端询问，并将返回的提示输入到textarea中
                axios.post(this.base_url + '/api/asking_for_dims', {
                        data
                    })
                    .then(response => {
                        // 获取数据后保存到文本域,更新推荐的Prompt部分
                        // console.log(this.designLabels)
                        // console.log(response.data)
                        this.$message('Query successfully!');

                        this.designLabels['Prompt'] = response.data['Prompt']
                        this.textValue = response.data['Prompt']['LF']

                        // 此时itemsFixed中仅有fixed的属性,更新ItemsFixed对象,添加之前不存在的新属性
                        response.data['dimension'].forEach(oneDimension => {
                            if (this.itemsFixed[oneDimension] == undefined) {
                                // 新添加的维度,仅当在fixed字典中不存在时初始值才设为false
                                this.itemsFixed[oneDimension] = false
                            }
                        })

                        // 此时designLabels的dimension中仅有fixed的属性,根据传来的值进行更新,添加之前不存在的新属性
                        response.data['dimension'].forEach(oneDimension => {
                            if (!this.designLabels.dimension.includes(oneDimension)) {
                                // 新推荐的之前不存在的维度,直接添加
                                this.designLabels.dimension.push(oneDimension)
                                this.designLabels.degree[oneDimension] = response.data['degree'][oneDimension]
                            } else {
                                // 之前存在的维度,直接把对应的程度值合并
                                let unionDegree = response.data['degree'][oneDimension].concat(this.designLabels.degree[oneDimension])
                                let newDegree = [...new Set(unionDegree)]
                                this.designLabels.degree[oneDimension] = newDegree
                            }
                        })
                    })
                    .catch(error => {
                        console.error('Error fetching general prompt:', error);
                        this.$message('Query failed!');
                    });
            } else {
                // 关键词形式
                let data = {
                    "promptForm": "keywords",
                    "design": this.keywordCount,
                    "texts": this.clickTextData,
                    "existingLF": ''
                }
                axios.post(this.base_url + '/api/asking_for_chat', {
                        data
                    })
                    .then(response => {
                        this.$message('Query successfully!');
                        // 成功获取数据后，保存到keyword list中
                        this.keywordsList = response.data
                        this.fillWordForm(this.keywordsList)
                    })
                    .catch(error => {
                        console.error('Error fetching keywords:', error);
                    });
                // 显示提交按钮
                const buttons = document.querySelectorAll('.keywordButton');
                buttons.forEach(button => {
                    button.style.display = 'block';
                });

            }
        },
        requery() {
            // 重新提交设计维度和所选句子，点击query按钮，得到后端返回的提示并填充(空值的维度不返回)
            if (this.showKeywords == false) {
                // 一般疑问句形式
                // let designContent = this.designLabels.map(item => ({
                //     [item.label.toLowerCase()]: item.selectedDegree
                // })).reduce((acc, obj) => Object.assign(acc, obj), {})
                let designContent = {};
                this.designLabels.dimension.forEach(dimensionItem => {
                    const selectedValues = this.designLabels.Prompt[dimensionItem] || [];
                    if (selectedValues.length > 0) {
                        designContent[dimensionItem] = selectedValues;
                    }
                });

                let data = {
                    "promptForm": "prompt",
                    "design": designContent,
                    "texts": this.clickTextData,
                    "existingLF": ''
                }
                console.log("维度----")
                console.log(data)
                // 获得所选句子，一并传送给后端询问，并将返回的提示输入到textarea中
                axios.post(this.base_url + '/api/asking_for_chat', {
                        data
                    })
                    .then(response => {
                        // 成功获取数据后，保存到文本域中
                        this.textValue = response.data
                        this.$message('Requery successfully!');
                    })
                    .catch(error => {
                        console.error('Error fetching general prompt:', error);
                        this.$message('Requery failed!');
                    });
            }
        },
        saveLF() {
            // 获取当前所有选中填充项，整理格式后将规则传给后端，///并更新数据样本框
            // 第一种情况（一般疑问句）：获取所有具有类名 "checkInput" 的复选框元素，checked的第一个是yes/no
            // 将设计属性也一并传送过去
            if (!this.showKeywords) {
                if (this.updateOrSaveNew == 0) {
                    var checkboxes = document.querySelectorAll('.checkInput');
                    var selectedCheckboxes = [];
                    checkboxes.forEach(function (checkbox) {
                        if (checkbox.checked) {
                            selectedCheckboxes.push(checkbox);
                        }
                    });

                    let LF = {
                        selectedDataKey: this.clickTextData['dataKey'],
                        labelStr: this.clickTextData['labelStr'],
                        label: this.clickTextData['label'],
                        contentType: 'prompt',
                        prompt: this.textValue,
                        answer: 'Yes',
                        designContent: this.designLabels //对象格式
                    }
                    // console.log("save-保存---不是更新")
                    // console.log(LF)
                    // 先前端添加新规则,保存后以便直接绘制,然后等后端返回时重新添加柱状图即可
                    // 初始化allRules，此时是空的
                    this.allRules.push(LF)

                    EventBus.$emit('eventC', this.allRules)
                    this.$message('Save successfully! Wait for evaluation please.');

                    let datasetName = this.clickTextData['datasetName']
                    axios.post(this.base_url + '/api/save_rules', {
                            LF,
                            datasetName
                        })
                        .then(response => {
                            if (response.data['signal'] == 'success') {
                                this.$message('Evaluate successfully!');
                                this.allRules = response.data['allLF']

                                // 绘制柱状图
                                EventBus.$emit('eventZ', this.allRules)

                            } else {
                                this.$message('Evaluate failed!');
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching saveLF:', error);
                        });
                } else {
                    // 迭代旧规则时
                    let id = this.id
                    let datasetName = this.datasetName
                    // console.log("传过来的view2")
                    // console.log(this.dataKey)
                    let newDataKey
                    if (this.clickTextData != null) {
                        console.log("test3222---")
                        console.log(this.clickTextData)
                        newDataKey = this.clickTextData['dataKey']
                    } else
                        newDataKey = this.dataKey;
                    // console.log(this.dataKey)

                    this.designLabels['Prompt']['LF'] = this.textValue
                    console.log("更新后的设计面板具体：")
                    console.log(this.designLabels)

                    let LF = {
                        selectedDataKey: newDataKey, //判断是否存在
                        prompt: this.textValue,
                        designContent: this.designLabels //对象格式(不对，Prompt LF部分没更新)
                    }
                    axios.post(this.base_url + '/api/update_rules', {
                            LF,
                            id,
                            datasetName
                        })
                        .then(response => {
                            if (response.data['signal'] == 'success') {
                                this.$message('Update successfully!');
                                this.allRules = response.data['allLF']
                                EventBus.$emit('eventZ', this.allRules)

                            } else {
                                this.$message('Evaluate failed!');
                            }
                            this.updateOrSaveNew = 0 //归位
                        })
                        .catch(error => {
                            console.error('Error fetching saveLF:', error);
                        });
                    this.updateOrSaveNew = 0 //修正标志位为迭代旧规则标志
                }

            } else {
                // 第二种情况（关键词）：checkInput1选中词语
                var checkboxes = document.querySelectorAll('.checkInput');
                var selectedCheckboxes = [];
                checkboxes.forEach(function (checkbox) {
                    if (checkbox.checked) {
                        selectedCheckboxes.push(checkbox);
                    }
                });
                var checkboxes2 = document.querySelectorAll('.checkInput2');
                var selectedCheckboxes2 = [];
                checkboxes2.forEach(function (checkbox) {
                    if (checkbox.checked) {
                        selectedCheckboxes2.push(checkbox.labels[0].innerText);
                    }
                });
                let LF = {
                    selectedDataKey: this.clickTextData['dataKey'],
                    labelStr: this.clickTextData['labelStr'],
                    label: this.clickTextData['label'],
                    contentType: 'keywords',
                    prompt: selectedCheckboxes2,
                    designContent:''
                }
                // console.log("/*/*/*/")
                // console.log(this.clickTextData)
                // console.log(LF)
                let datasetName = this.clickTextData['datasetName']
                axios.post(this.base_url + '/api/save_rules', {
                        LF,
                        datasetName
                    })
                    .then(response => {
                        if (response.data['signal'] == 'success') {
                            this.$message('Save successfully!');
                            this.allRules = response.data['allLF']
                            EventBus.$emit('eventC', this.allRules)

                        } else {
                            this.$message('Save failed!');
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching saveLF:', error);
                    });
            }
        },
        fillWordForm(keyword_list) {
            // 将关键词填入新的radio中
            const form = d3.selectAll("#wordsForm");
            form.selectAll("li").remove(); //每一次添加前全部清空li
            keyword_list.forEach(function (option, i) {
                form.append("li")
                    .append("input")
                    .attr("type", "checkbox")
                    .attr("name", "checkbox")
                    .attr("data-labelauty", option)
                    .attr("class", "checkInput2")
            });
            this.checkboxBeauty2() //新生成的去美化
        },
        removeItem(item) {
            if (!this.itemsFixed[item]) {
                this.designLabels['dimension'] = this.designLabels['dimension'].filter(i => i !== item)
                // 更新 degree
                if (this.designLabels['degree'][item]) {
                    delete this.designLabels['degree'][item]
                }
                // 更新 Prompt
                if (this.designLabels['Prompt'][item]) {
                    delete this.designLabels['Prompt'][item];
                }
            }
        },
        toggleFixed(item) {
            // console.log(item)
            this.itemsFixed[item] = !this.itemsFixed[item];
            // if (this.itemsFixed[item]) {
            //     // fixed时
            //     typeValue = 'success'
            //     iconValue = 'el-icon-lock'
            // } else {
            //     typeValue = 'primary'
            //     iconValue = 'el-icon-unlock'
            // }
            // console.log(this.itemsFixed)
        }
    }
}
</script>

<style>
.generalQuestion {
    .el-slider {
        .el-slider__input {
            margin-top: 0;
        }

        .el-slider__runway {
            height: 25px;
            margin-top: 0;
            margin-bottom: 0 !important;
            background-color: #FFFFFF;
            border: 1px solid #DCDFE6;

            .el-slider__bar {
                height: 24px;
            }

            .el-slider__button-wrapper {
                top: 0;
                height: 24px;

                .el-slider__button {
                    width: 4px;
                    height: 24px;
                    border-radius: 0;
                    background: #FFFFFF;
                    border: solid 2px #0068A5;
                }
            }

            .el-slider__stop {
                width: 1px;
                height: 24px;
                border-radius: 0;
                background-color: #DCDFE6;
            }

            .el-slider__marks-text {
                color: #717171;
                margin-top: 0;
                transform: translateX(-115%);
            }
        }
    }
}

#view2_content {
    /* width: 1685px; */
    width: 100%;
    height: 735px;
}

#confusion {
    width: 100%;
    height: 366px;
}

span#inputVariable {
    margin-left: 10px;
}

/* .labelFunc Input {
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 5px;
    background-color: #f8f8f8;
    box-shadow: 0 2px 13px rgba(0, 0, 0, 0.3);
    transition: box-shadow 0.3s ease;
    margin-left: 1%;
}

.labelFunc Input:hover {
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
} */

.promptLogo {
    display: inline-block;
    width: 30px;
    height: 30px;
    padding-left: 8px;
    border: 1px solid #cbcbcb;
    border-radius: 15px;
    background-color: #c6e3c3;
    color: #3c3c3c;
    font-weight: 900;
    padding-top: 2px;
    font-size: 15px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.dowebok {
    list-style-type: none;
    display: inline-block;
    margin-left: 3px;
}

.dowebok li {
    display: inline-block;
    margin-left: 12px;
    margin-bottom: 12px;
}

input.labelauty+label {
    font: 12px "Microsoft Yahei";
}

/* 新建的radio样式 */
/* Prevent text and blocks selection */
input.labelauty+label ::selection {
    background-color: rgba(255, 255, 255, 0);
}

input.labelauty+label ::-moz-selection {
    background-color: rgba(255, 255, 255, 0);
}

/* Hide original checkboxes. They are ugly! */
input.labelauty {
    display: none !important;
}

/*
 * Let's style the input
 * Feel free to work with it as you wish!
 */
input.labelauty+label {
    display: table;
    font-size: 11px;
    padding: 10px;
    /* background-color: #efefef;
    color: #b3b3b3; */
    background-color: #ebebeb;
    color: #5e5e5e;
    cursor: pointer;

    border-radius: 3px 3px 3px 3px;
    -moz-border-radius: 3px 3px 3px 3px;
    -webkit-border-radius: 3px 3px 3px 3px;

    transition: background-color 0.25s;
    -moz-transition: background-color 0.25s;
    -webkit-transition: background-color 0.25s;
    -o-transition: background-color 0.25s;
}

/* Stylish text inside label */

input.labelauty+label>span.labelauty-unchecked,
input.labelauty+label>span.labelauty-checked {
    display: inline-block;
    line-height: 16px;
    vertical-align: bottom;
}

/* Stylish icons inside label */

input.labelauty+label>span.labelauty-unchecked-image,
input.labelauty+label>span.labelauty-checked-image {
    display: inline-block;
    width: 16px;
    height: 16px;
    vertical-align: bottom;
    background-repeat: no-repeat;
    background-position: left center;

    transition: background-image 0.5s linear;
    -moz-transition: background-image 0.5s linear;
    -webkit-transition: background-image 0.5s linear;
    -o-transition: background-image 0.5s linear;
}

/* When there's a label, add a little margin to the left */
input.labelauty+label>span.labelauty-unchecked-image+span.labelauty-unchecked,
input.labelauty+label>span.labelauty-checked-image+span.labelauty-checked {
    margin-left: 7px;
}

/* When not Checked */
input.labelauty:not(:checked):not([disabled])+label:hover {
    background-color: #e2e2e2;
    color: #000000;
}

input.labelauty:not(:checked)+label>span.labelauty-checked-image {
    display: none;
}

input.labelauty:not(:checked)+label>span.labelauty-checked {
    display: none;
}

/* When Checked */
input.labelauty:checked+label {
    background-color: #3498db !important;
    color: #ffffff;
}

input.labelauty:checked:not([disabled])+label:hover {
    background-color: #72c5fd;
}

input.labelauty:checked+label>span.labelauty-unchecked-image {
    display: none;
}

input.labelauty:checked+label>span.labelauty-unchecked {
    display: none;
}

input.labelauty:checked+label>span.labelauty-checked {
    display: inline-block;
}

input.labelauty.no-label:checked+label>span.labelauty-checked {
    display: block;
}

/* When Disabled */
input.labelauty[disabled]+label {
    opacity: 0.5;
}

input.labelauty+label>span.labelauty-unchecked-image {
    background-image: url(../assets/input-unchecked.png );
}

input.labelauty+label>span.labelauty-checked-image {
    background-image: url(../assets/input-checked.png );
}

/* 规则框的左右两侧内容 */
.leftlogo {
    width: 11%;
    height: 100%;
    flex: 0;
    padding-left: 4px;
    float: left;
}

.rightinput {
    float: right;
    width: 80%;
    flex: 1;
    padding-left: 12px;
}

.labelFunc .ivu-card-body .generalQuestion {
    display: flex;
}

.promptLogo:nth-of-type(2) {
    margin-top: 26px;
    margin-bottom: 26px;
}

.promptLogo:nth-of-type(1) {
    margin-top: 6px;
}

.generalQuestion .dowebok:nth-of-type(1) {
    margin-top: 15px;
    margin-bottom: 15px;
}

.labelFunc .ivu-card-extra {
    position: absolute;
    right: 2px;
    top: 4px;
}

/* Rules */
.onerule {
    cursor: pointer;
}

.rulesCard {
    margin-top: 6px;
    height: 180px;
}

.ruleShow {
    overflow: auto;
    overflow-x: hidden;
}

.rulesCard .ivu-card-body {
    height: 131px;
    overflow: auto;
    overflow-x: hidden;
}

.row1,
.row2,
.row3 {
    display: flex;
    width: 100%;
    margin-top: 16px;
}

.left {
    flex: 0;
}

.right {
    flex: 1;
}

.labelFunc .ivu-card-body {
    height: 184px;
    overflow: auto;
}

#updateRule {
    display: none;
}

#confirmRule {
    display: none;
}

.sameLabelDiv {
    background-color: rgba(194, 218, 237, 0.8);
}

.clicked {
    background-color: #c6e3c3;
}

.button-change,
.button-upload {
    border: none;
    padding: 0px;
    margin-right: 249px;
    margin-top: 8px;
    background: transparent;
}

.button-change {
    margin-right: 249px;
}

.button-upload {
    margin-right: 278px;
}

.button-change img {
    width: 18px;
}

.button-upload img {
    width: 20px;
}

.button-change:hover {
    outline: none;
    border: none;
    background-color: transparent;
    color: transparent;
}

.button-change:focus {
    outline: none;
    border: none;
    background-color: transparent;
    color: transparent;
}

.button-change:active {
    outline: none;
    border: none;
    background-color: transparent;
    color: transparent;
}

/* .oneDimension label {
    width: 20%;
} */

.el-radio-button__inner {
    padding: 10px 18px;
}

.keywordButton {
    display: none;
}

.el-form-item__label {
    width: 18%;
    display: inline-block;
    text-align: right;
}

.el-form-item:not(:nth-last-child(1)) {
    margin-bottom: 2px;
    border-bottom: 1px solid #e7e7e7;
}

.el-form-item:nth-last-child(1) {
    margin-bottom: 0px;
}

.el-input-number--mini {
    width: 92px;
}

.el-input-number__increase {
    width: 27px;
}

.el-button--mini,
.el-button--mini.is-round {
    padding: 7px 15px;
}

.el-form-item__label {
    width: 80%;
    text-align: left;
    font-weight: bold;
    display: inline-block;
}

.allFormPage {
    margin-right: 5px;
    background-color:rgba(237,237,237,0.16);
    border: 2px solid #e1e1e1;
    padding-left: 7px;
    padding-right: 7px;
    margin-left: 5px;
}
</style>
