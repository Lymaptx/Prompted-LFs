<template>
<div>
    <Card class="myCard4 myCard">
        <!-- <template #extra>
            <el-button size="medium" style="border:0" @click="applyWeakLabels">Apply<i class="el-icon-upload el-icon--right"></i></el-button>
        </template> -->
        <p slot="title">LF Status</p>
        <div id="view4-container">
            <div class="oneRule" v-for="rule in allRules" :key="rule.id" :style="{ border: getBorderColor(rule.label)}">

                <span class="corner-circle top-left" @click="fixedCurrentPrompt(rule)"></span>
                <span style="position: absolute;top: 0px;right: 2px;">
                    <el-button icon="el-icon-delete-solid" size="mini" @click="deleteCurrentPrompt(rule)" style="border:0;background-color: transparent;" circle></el-button>
                </span>
                <span class="corner-circle bottom-left"></span>
                <span class="corner-circle bottom-right"></span>
                <!-- 根据是否更新标志位(updateFlag)显示左右按钮 -->
                <el-button v-if="rule.updateFlag>0" size="mini" class="updateButton leftButton" icon="el-icon-d-arrow-left" circle @click="previousPrompt(rule)" :disabled="isFirstPrompt(rule)"></el-button>
                <el-button v-if="rule.updateFlag>0" size="mini" class="updateButton rightButton" icon="el-icon-d-arrow-right" circle @click="nextPrompt(rule)" :disabled="isLastPrompt(rule)"></el-button>

                <div class="ruleLabel" :style="{ borderBottom: getBorderColor(rule.label)}">
                    <el-tag effect="dark" :type="tagType(rule.label)" style="margin-top: 12px;">{{rule.labelStr}}</el-tag>
                    <div style="width: 75%;height: 44px;">
                        <svg :id="'bars' + rule.id" width="210" height="44"></svg>
                    </div>
                </div>
                <div class="ruleContent" @click="updateThisRule(rule)">
                    <!-- 当读取规则为关键词时 -->
                    <ul v-if="rule.contentType==='keywords'">
                        <li v-for="keyword in rule.prompt">{{keyword}}</li>
                    </ul>
                    <!-- 当读取规则为一般疑问句时 -->
                    <div class="answer" v-else-if="rule.contentType==='prompt'">
                        <!-- <button>{{rule.prompt}}</button> -->
                        <button>{{ currentPrompt(rule) }}</button>
                        <div class="oneAnswer">
                            <div class="item1">
                                <p>" Yes "</p>
                                <p>" No "</p>
                            </div>
                            <div class="item2">
                                <img src="../assets/support.png">
                                <img src="../assets/support.png">
                            </div>
                            <div class="item3">
                                <button>{{rule.labelStr}}</button>
                                <button>Abstention</button>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </Card>
</div>
</template>

<script>
import * as d3 from 'd3';
import * as echarts from 'echarts';
import axios from 'axios';
import {
    EventBus
} from '../EventBus';
import {
    globalState
} from '@/main.js'; // 引入全局变量
export default {
    data() {
        return {
            isVisibility: true, 
            allRules: [],
            datasetName: '',
            currenIndex: 0, //查询迭代记录时候的索引,默认为prompt索引最高值
            base_url: "http://127.0.0.1:5001"
        };
    },
    computed: {

    },
    watch: {
        // 在没有规则时可能会出现绘制柱状图的问题
        allRules: {
            handler(newRules) {
                this.$nextTick(() => {
                    newRules.forEach(rule => {
                        this.drawBars(rule);
                    });
                });
            },
            deep: true
        }
    },
    mounted() {
        EventBus.$on('eventD', (datasetValue) => {
            // 用=>才可以使用this指向，function不行
            this.showInitialRules(datasetValue)
        })
        EventBus.$on('eventC', (allRules) => {
            // 前端更新了规则集合，此时后端还没返回准确率等，不需要画图
            // 用=>才可以使用this指向，function不行
            this.allRules = allRules;
            // console.log("eventc中，前端存储之后返回的全部LF，非后端")
            // console.log(this.allRules)
        })
        EventBus.$on('eventZ', (allRules) => {
            this.allRules = allRules
            this.$nextTick(() => {
                this.allRules.forEach(rule => {
                    this.drawBars(rule);
                });
            })
        })
        this.allRules.forEach(rule => {
            this.drawBars(rule);
        });

    },
    methods: {
        showInitialRules(datasetValue) {
            this.datasetName = datasetValue
            axios.post(this.base_url + '/api/show_initial_rules', {
                    datasetValue
                })
                .then(response => {
                    this.allRules = response.data
                    // 并将值传入view2中初始化
                    EventBus.$emit('eventR', this.allRules)
                    this.$nextTick(() => {
                        this.allRules.forEach(rule => {
                            this.drawBars(rule);
                        });
                    })
                })
                .catch(error => {
                    console.error('Error fetching rules:', error);
                });
        },
        getBorderColor(label) {
            // 根据标签映射边框颜色
            const labelToColorMap = ['#76a9cb', '#e26f51', "#f56c6c", '#e6a23c']
            return `1px solid ${labelToColorMap[label]}`
        },
        updateThisRule(rule) {
            // 点击更新该条规则，textarea处是该提示？维度填满，执行的是query函数，重新申请维度和提示，且保存按钮改为更新按钮，在完成更新后再重新更改为保存
            // 先点击，然后view3中找到数据样本置顶；view2中重新填充该规则设计时用到的维度、值和提示；同时save按钮改为更新，点击函数也随之改变。
            // 需要两个索引，一个是当前规则卡片的id，一个是该提示在当前历史记录中的次序currentProIndex
            // 发送请求，获取之前创建该规则时选中的Unlabel数据样本
            // console.log("---view4")
            // console.log(rule)
            const ruleId = rule.id //当前rule的id
            let currentPromIndex = rule.promptHistory.indexOf(rule.prompt) //当前点击rule在同一个列表中的顺序,可以借此获取view2 view3中数据
            let datasetValue = this.datasetName
            // console.log(currentPromIndex)
            

            let selectedDataKey = rule.dataKeyList[currentPromIndex] //最终是字符串型  数据样本的key
            axios.post(this.base_url + '/api/query_dataKey_dimension', {
                    datasetValue,
                    selectedDataKey,
                    ruleId,
                    currentPromIndex
                })
                .then(response => {
                    // 查询数据样本发送给view3并置顶，将其索引一并发送到view3，并展示在表格最顶部
                    // console.log(response.data)
                    this.$message('Filter history successfully!');

                    let unlabelSelectedData = response.data['selectedData']
                    unlabelSelectedData['index'] = selectedDataKey
                    unlabelSelectedData['ruleId'] = ruleId
                    unlabelSelectedData['ruleLabel'] = rule.label

                    // console.log(unlabelSelectedData)
                    EventBus.$emit('eventS', unlabelSelectedData)

                    let designContent = response.data['designContent']
                    let dataKey = response.data['dataKey']
                    let array = {
                        '0': designContent,
                        '1': ruleId,
                        '2': dataKey,
                        '3': this.datasetName
                    }
                    // console.log("view4--666")
                    // console.log(array)
                    EventBus.$emit('eventT', array)

                })
                .catch(error => {
                    console.error('Error fetching rules:', error);
                });

        },
        drawBars(rule) {
            // 清空现有内容
            let currentLF = this.allRules.find(item => item.id === rule.id)
            let elementId = 'bars' + rule.id
            const svg = d3.select(`#${elementId}`);

            // console.log("bars---")
            // console.log("bars里面的当前规则")
            // console.log(rule)

            let index;
            if (rule.contentType == 'prompt') {
                index = rule['promptHistory'].indexOf(rule['prompt']);
            } else {
                index = 0
            }

            const highlightStyle = {
                boxShadow: '0 2px 4px rgba(0, 0, 0, .12), 0 0 6px rgba(0, 0, 0, .04)',
                stroke: '#000', // 高亮边框颜色
                strokeWidth: '1px' // 高亮边框宽度
            };

            const width = svg.attr('width');
            // console.log(width)
            const height = svg.attr('height');
            const margin = {
                top: 12,
                right: 0,
                bottom: 0,
                left: 0
            };

            const innerWidth = width - margin.left - margin.right;
            const innerHeight = height - margin.top - margin.bottom;

            const xLabels = ['accuracy', 'coverage'];
            const groupedData = currentLF.accuracy.map((val, i) => ({
                index: i,
                accuracy: currentLF.accuracy[i],
                coverage: currentLF.coverage[i]
            }));

            const xScale = d3.scaleBand()
                .domain(groupedData.map((_, i) => i))
                .range([0, innerWidth])
                .padding(0.1);

            const yScale = d3.scaleLinear()
                .domain([0, 1])
                .nice()
                .range([innerHeight, 0]);

            svg.selectAll('*').remove();

            const g = svg.append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);

            const maxBarWidth = 6;
            const barPadding = 5; // Add space between bars within the same group

            // Create a tooltip div
            const tooltip = d3.select('body').append('div')
                .attr('class', 'tooltip')
                .style('position', 'absolute')
                .style('background-color', 'white')
                .style('border', '1px solid #ddd')
                .style('padding', '5px')
                .style('border-radius', '3px')
                .style('pointer-events', 'none')
                .style('opacity', 0);

            // 绘制柱状图
            groupedData.forEach((d, i) => {
                const groupX = xScale(i); // x position of the group

                g.selectAll(`.bar-${i}`)
                    .data(xLabels.map(label => ({
                        label,
                        value: d[label]
                    })))
                    .enter().append('rect')
                    .attr('class', `bar-${i}`)
                    .attr('x', (data, j) => groupX + j * (Math.min(xScale.bandwidth() / xLabels.length, maxBarWidth + barPadding)))
                    .attr('y', d => yScale(d.value))
                    .attr('width', Math.min(xScale.bandwidth() / xLabels.length, maxBarWidth))
                    .attr('height', d => height - yScale(d.value))
                    .attr('fill', d => d.label === 'accuracy' ? '#dcdfe6' : '#909399')
                    .attr('stroke', d => i === index ? highlightStyle.stroke : null)
                    .attr('stroke-width', d => i === index ? highlightStyle.strokeWidth : null)
                    .style("box-shadow", d => i === index ? highlightStyle.boxShadow : null)
                    // .attr('fill', d => i === index? highlightStyle.fill : d.label === 'accuracy' ? '#dcdfe6' : '#909399')
                    .on('mouseover', (event, d) => {
                        tooltip.transition()
                            .duration(200)
                            .style('opacity', .9);
                        tooltip.html(`${d.label === 'accuracy' ? 'accuracy' : 'recovery'}: ${d.value}`)
                            .style('left', (event.pageX + 5) + 'px')
                            .style('top', (event.pageY - 28) + 'px');
                    })
                    .on('mouseout', () => {
                        tooltip.transition()
                            .duration(500)
                            .style('opacity', 0);
                    });
            });
            // const lastIndex = groupedData.length - 1;
            // const lastGroup = groupedData[lastIndex];
            // const maxLastBarHeight = Math.max(lastGroup.accuracy, lastGroup.coverage);
            // const maxLastBarY = yScale(maxLastBarHeight);

            // // Add a horizontal line at the maximum height of the last pair of bars
            // g.append('line')
            //     .attr('x1', xScale(lastIndex))
            //     .attr('x2', xScale(lastIndex) + xScale.bandwidth())
            //     .attr('y1', maxLastBarY)
            //     .attr('y2', maxLastBarY)
            //     .attr('stroke', 'red') // Color of the line
            //     .attr('stroke-width', 1) // Thickness of the line
            //     .attr('stroke-dasharray', '4,4'); // Dashes

        },
        currentPrompt(rule) {
            return rule.prompt;
        },
        previousPrompt(rule) {
            const index = rule.promptHistory.indexOf(rule.prompt);
            if (index > 0) {
                rule.prompt = rule.promptHistory[index - 1];
            }
        },
        nextPrompt(rule) {
            const index = rule.promptHistory.indexOf(rule.prompt);
            if (index < rule.promptHistory.length - 1) {
                rule.prompt = rule.promptHistory[index + 1];

            }
        },
        isFirstPrompt(rule) {
            // 检查当前 prompt 是否为 promptHistory 的第一个,第一个禁用上一个按钮
            return rule.promptHistory.indexOf(rule.prompt) === 0;
        },
        isLastPrompt(rule) {
            // 检查当前 prompt 是否为 promptHistory 的最后一个,最后一个禁用下一个按钮
            return rule.promptHistory.indexOf(rule.prompt) === rule.promptHistory.length - 1;
        },
        tagType(label) {
            // 与view3共用相同lael-type映射,传入标签,返回tag type
            switch (label) {
                case 0:
                    return ''
                case 1:
                    return 'success'
                case 2:
                    return 'info'
                case 3:
                    return 'danger'
            }

        },
        deleteCurrentPrompt(rule) {
            // 页面上删除当前规则，并在后端删除该Lf文件内的该记录，该记录后面的id也都需要更改，weak_labels中也需要删除该位置的弱标签
            this.allRules.splice(rule.id, 1)

            this.$message('Background is being deleted...');
            let delIndex = rule.id
            let datasetValue = this.datasetName
            // 先给前端赋假值，再去发送请求给后端
            axios.post(this.base_url + '/api/delete_current_rule', {
                    datasetValue,
                    delIndex
                })
                .then(response => {
                    this.$message('Delete this rule successfully!');
                    this.allRules = response.data
                    console.log("删除之后:")
                    console.log(this.allRules)

                })
                .catch(error => {
                    console.error('Error delete rule:', error);
                });
        },

    },
    fixedCurrentPrompt(rule) {
        let currentLF = this.allRules.find(item => item.id === rule.id)
        let index = rule['promptHistory'].indexOf(rule['prompt']);

        // 找到了当前规则的Id和当前选中索引项
        console.log(currentLF,index)

    }
};
</script>

<style>
#view4-container {
    width: 100%;
    /* height: 100%; */
    font-size: 0;
    /* display: flex;
    flex-direction: row;
    justify-content: space-around; */
    /* visibility: hidden; */
}

/* .visibles {
    visibility: visible;
} */

.oneRule {
    vertical-align: top;
    font-size: 10px;
    position: relative;
    margin-right: auto;
    margin-left: auto;
    margin-top: 20px;
    width: 88%;
    /* aspect-ratio: 1.6 / 1; */
    /* height: calc(19vw / 1.8); */
    border-radius: 3px;
    background-color: rgba(255, 255, 255, 1);
    color: rgba(16, 16, 16, 1);
    box-shadow: 0px 1px 4px 0px rgba(0, 0, 0, 0.49);
    /* border: 1px solid rgb(199, 199, 205); */
}

.ruleLabel {
    width: 85%;
    height: 64px;
    /* border-bottom: 1px solid rgb(199, 199, 205); */
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
}

.ruleLabel p {
    font-size: 1.0rem;
    padding-top: 0.8rem;
    font-family: SourceHanSansSC-regular;
}

.ruleContent {
    width: 85%;
    padding-bottom: 18px;
    margin-left: auto;
    margin-right: auto;
}

.ruleContent ul {
    list-style: none;
    padding: 0;
    margin: 0;
    overflow: hidden;
}

.ruleContent ul li {
    font-family: SourceHanSansSC-regular;
    display: inline-block;
    background-color: #DCDFE6;
    color: rgb(0, 0, 0);
    border: 1px solid white;
    font-size: 0.75rem;
    padding: 0.3rem 0.2rem;
    margin-right: 0.8rem;
    margin-bottom: 0.5rem;
    border-radius: 4px;
    white-space: nowrap;
}

.ruleContent button {
    text-align: left;
    pointer-events: none;
    /* margin-top: 0.2rem; */
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
    font-family: SourceHanSansSC-regular;
    background-color: #DCDFE6;
    border: 0px;
    border-radius: 4px;
    color: rgb(24, 24, 24);
}

.oneAnswer {
    display: flex;
    font-family: SourceHanSansSC-regular;
    font-size: 0.75rem;
}

.item1 p {
    margin-top: 0.6rem;
    margin-left: 0.5rem;
}

.item2 img {
    display: block;
    width: 1.3rem;
    margin-top: 0.5rem;
    margin-left: 0.6rem;
}

.item3 {
    width: 6rem;
}

.item3 button {
    pointer-events: none;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    padding: 0.05rem 0.6rem;
    font-family: SourceHanSansSC-regular;
    font-weight: 100;
    background-color: transparent;
    border: 1px solid rgba(187, 187, 187, 1);
    border-radius: 4px;
    color: black;
    display: block;
    margin-right: auto;
    margin-left: auto;
}

.corner-circle {
    position: absolute;
    width: 6px;
    height: 6px;
    border: 1px solid rgb(171, 171, 171);
    background-color: #ffffff;
    border-radius: 50%;
}

.top-left {
    top: 8px;
    left: 8px;
    /* 距离左侧5px */
}

.top-right {
    top: 8px;
    right: 8px;
}

.bottom-left {
    bottom: 8px;
    left: 8px;
}

.bottom-right {
    bottom: 8px;
    /* 距离底部5px */
    right: 8px;
    /* 距离右侧5px */
}

.updateButton {
    position: absolute;
    border: 0;
    background: transparent;
    bottom: 46%;
}

.leftButton {
    left: 0px;
}

.rightButton {
    right: 0px;
}

/* .info-box {
    fill: #f5f5f5;
}

.custom-text {
    letter-spacing: 2px;
    word-spacing: 5px;
    text-shadow: 2px 2px 2px rgba(0, 0, 0, 0.5);
    text-transform: uppercase;
} */

.myCard4 .ivu-card-body {
    height: 755px;
    overflow: auto;
    overflow-x: hidden;
    padding: 0px;
}

/* labels:keywords */
/* .el-tag + .el-tag {
    margin-left: 10px;
  }
  .button-new-tag {
    margin-left: 10px;
    height: 32px;
    line-height: 30px;
    padding-top: 0;
    padding-bottom: 0;
  }
  .input-new-tag {
    width: 90px;
    margin-left: 10px;
    vertical-align: bottom;
  } */

.el-tag--dark {
    background-color: #76a9cb;
    border-color: #76a9cb;
    color: #fff;
}

.el-tag--dark.el-tag--success {
    background-color: #e26f51;
    border-color: #e26f51;
    color: #fff;
}
</style>
