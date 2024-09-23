<template>
<div>
    <Card class="myCard">
        <p slot="title">Data Summary</p>
        <div id="chart_container">
            <!-- 数据信息总览 -->
            <span class="title">Dataset Name: </span>
            <el-select v-model="datasetValue" @change="handleChange" placeholder="CHOOSE DATASET" size="small">
                <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value">
                </el-option>
            </el-select>
            </br>
            </br>
            <span class="title">Legend Information: </span>
            </br>
            <div class="leftContent" style="margin-left:5%;">
                <div class="oneColumn">
                    <div class="piece" style="width:50%;float:left;text-align: left;background-color:#76a9cb">
                        <p>{{numToLabel[0]}}</p>
                    </div>
                    <div class="piece" style="width:50%;float:right;text-align: right;background-color:#e26f51">
                        <p>{{numToLabel[1]}}</p>
                    </div>
                </div>
                <div class="oneColumn">
                    <div class="piece" style="width:50%;float:left;text-align: left;background-color:#dcdfe6">
                        <p>Accuracy</p>
                    </div>
                    <div class="piece" style="width:50%;float:right;text-align: right;background-color:#909399">
                        <p>Coverage</p>
                    </div>
                </div>
                <div class="oneColumn" style="background: linear-gradient(90deg,#BEA6A0 0%,#FFFFFF 50%,#06D3C5 100%)">
                    <div class="piece" style="width:50%;float:left;text-align: left;">
                        <p>Conflict</p>
                    </div>
                    <div class="piece" style="width:50%;float:right;text-align: right;">
                        <p>Redundancy</p>
                    </div>
                </div>
                <div class="oneColumn" style="background: linear-gradient(90deg,#e6f3d2 0%,#FFFFFF 50%,#fae1ee 100%)">
                    <div class="piece" style="width:100%;text-align: center;">
                        <p>Similarity</p>
                    </div>

                </div>
            </div>
            <div class="rightContent" style="margin-right:5%;">
                <div class="oneColumn" style="background-color:#dcdfe6">
                    <div class="piece" style="width:100%;text-align: center;">
                        <p>Currently Selected</p>
                    </div>
                </div>
                <div class="oneColumn" style="background-color: #fbecec">
                    <div class="piece" style="width:100%;text-align: center;">
                        <p>Mislabeling</p>
                    </div>
                </div>
                <div class="oneColumn" style="background-color: #fffddd">
                    <div class="piece" style="width:100%;text-align: center;">
                        <p>Missed Labeling</p>
                    </div>
                </div>
                <div class="oneColumn" style="background-color:#f0f8f1">
                    <div class="piece" style="width:100%;text-align: center;">
                        <p>Properly Labeling</p>
                    </div>
                </div>

            </div>

        </div>
    </Card>
</div>
</template>

<script>
import axios from 'axios';
import {
    EventBus
} from '../EventBus.js';
import {
    selectedIndex
} from '../store';
// 输出D3.js的版本号
import * as d3 from 'd3';
export default {
    data() {
        return {
            options: [{
                value: 'imdb',
                label: 'IMDB'
            }, {
                value: 'sms',
                label: 'SMS'
            }, {
                value: 'youtube',
                label: 'YOUTUBE'
            }],
            datasetValue: '',
            numToLabel: [],
            base_url: "http://10.106.146.34:5001"
        };
    },
    mounted() {
        // // 发送请求获取数据
    },
    methods: {
        handleChange() {
            // 请求该数据集信息
            // 将值传给view3，由view3发送请求去后端获取数据集信息展示开发集
            EventBus.$emit('eventA', this.datasetValue)
            // 传给view4，显示该数据集的初始LF
            EventBus.$emit('eventD', this.datasetValue)
            const datasetValue=this.datasetValue
            // 在选择数据集后，填充未标记数据集的原始句子+数据集类型
            axios.post(this.base_url + '/api/get_unlabel_data', {
                    datasetValue
                })
                .then(response => {
                    this.numToLabel = response.data['labels']
                    // 显示Legend
                    d3.select(".leftContent").style("display", "block");
                    d3.select(".rightContent").style("display", "block")
                })
                .catch(error => {
                    console.error('Error fetching dataset:', error);
                });

        },
    }
};
</script>

<style>
div#chart_container {
    height: 216px;
    width: 100%;
}

.leftContent,
.rightContent {
    display: none;
}

svg#chartInfo {
    /* height: 680px; */
    width: 100%;
}

.highlighted {
    stroke: #ff0000;
    /* You can adjust the stroke color for highlighting */
    stroke-width: 2;
    /* You can adjust the stroke width for highlighting */
    fill: #ff0000;
    /* You can adjust the fill color for highlighting */
}

.scatters {
    fill: lightsteelblue;
    stroke: steelblue;
    stroke-width: 2;
}

.title {
    font-size: 1.0rem;
    color: rgb(151, 151, 151);
    font-family: "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "\5FAE\8F6F\96C5\9ED1", Arial, sans-serif;
    padding-left: 0.2rem;
    font-weight: bold;
}

.title_info {
    font-size: 1.0rem;
    color: black;
    font-family: 'Times New Roman', Times, serif;
    padding-left: 0.2rem;
    font-weight: 400;

}

.info_left {
    width: 100%;
}

.leftContent {
    width: 42%;
    height: 80px;
    float: left;
}

.rightContent {
    width: 42%;
    height: 80px;
    float: right;
}

.oneColumn {
    height: 20px;
    width: 100%;
    margin-top: 11px;
    border: 1px solid grey;
    border-radius: 3px;
}

.oneColumn p {
    font-size: 12px;
    font-weight: bold;
    color: #515a6e;
    font-family: SourceHanSansSC-regular;
}
</style>
