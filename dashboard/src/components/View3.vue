<template>
<div>
    <Card :title="Label_confu" class="myCard">
        <template #extra>
            <el-button icon="el-icon-sort" circle size="mini" @click="changeSort"></el-button>
            <el-button size="mini" @click="encrypt">Encrypt
            </el-button>
            <el-select v-model="dataType" @change="changeDataset" size="mini">
                <el-option v-for="item in datasetOptions" :key="item.value" :label="item.label" :value="item.value">
                </el-option>
            </el-select>
        </template>
        <!-- 开发数据的取样，由左侧面板给定参数 -->
        <div class="datashow" id="datashow">
            <div class="text-left">
                <el-table ref="table" :show-header="false" :data="tableData" highlight-current-row @current-change="handleCurrentChange" :row-class-name="rowClassName" :row-style="rowStyle" style="width: 100%">
                    <el-table-column prop="index" label="INDEX" width="90">
                    </el-table-column>
                    <el-table-column prop="text" label="TEXT">
                        <template slot-scope="scope">
                            <div :class="{ 'highlight': scope.row.highlighted }">
                                {{ scope.row.text }}
                                <el-tag effect="dark" size="mini" v-for="(item, index) in scope.row.weak_label" :key="index" class="tag-item" :type="item !== -1 ? labelType[item] : 'info'" style="margin-right:2px">
                                    {{ item != -1 ? numToLabel[item] : 'ABSTENTION' }}
                                </el-tag>
                            </div>
                        </template>

                    </el-table-column>
                    <!-- prop是表格中填充的,label是显示在表头的文字;v-model是选中的打的标签值,options是[{value:,label:}]的可选项 -->
                    <el-table-column label="LABEL" width="100">
                        <template slot-scope="scope">
                            <el-select v-model="scope.row.textLabelValue" placeholder="Label" :disabled="isDevelopment(dataType)" size="mini">
                                <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value">
                                </el-option>
                            </el-select>
                        </template>
                    </el-table-column>
                </el-table>

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
import {
    globalState
} from '@/main.js'; // 引入全局变量
// 输出D3.js的版本号
import * as d3 from 'd3';

export default {
    data() {
        return {
            itemSize: 50, // 每个项的高度
            tableData: null,
            currentRow: null,
            numToLabel: null, //数字映射出的文字，数组格式
            // numToLabel: ['negitive', 'postive', 'big'],
            labelType: ['', 'success', "danger", 'warning'],
            labelFilters: null,
            datasetType: null,
            datasetName: null,
            options: [], //当前数据集的标签集
            datasetOptions: [{
                value: 'development',
                label: 'Development Data'
            }, {
                value: 'unlabel',
                label: 'Unlabeled Data'
            }],
            dataType: 'Unlabeled Data',
            Label_confu: 'Data Samples', 
            flag_recommand: 0, 
            add_flag: 0, 
            chuan: '',
            activeIndex: null, // 用于追踪当前激活的元素索引
            recommand_sentences: [],
            sortOrder: 0, //默认相似性从高到低推荐
            minSim: null, //与选中文本最小的相似度
            base_url: "http://127.0.0.1:5001"
        };
    },
    mounted() {
        EventBus.$on('eventA', (datasetValue) => {
            // 用=>才可以使用this指向，function不行
            this.InitializeDataSamples(datasetValue)
        })
        EventBus.$on('eventK', (dataKey) => {
            // 用=>才可以使用this指向，function不行
            this.filterDataSample(dataKey)
        })
        EventBus.$on('eventS', (selectedData) => {
            // 用=>才可以使用this指向，function不行
            this.showUpdateRuleSample(selectedData)
        })
    },
    methods: {
        InitializeDataSamples(datasetValue) {
            this.tableData = null
            this.datasetName = datasetValue
            // 在选择数据集后，填充未标记数据集的原始句子+数据集类型
            axios.post(this.base_url + '/api/get_unlabel_data', {
                    datasetValue
                })
                .then(response => {
                    this.tableData = response.data['text'].slice(0, 500)
                    this.numToLabel = response.data['labels']
                    this.datasetType = response.data['setType']
                    // 根据映射创建labelFilters，格式[{ text: '家', value: '家' }, { text: '公司', value: '公司' }]
                    this.options = this.numToLabel.map(label => ({
                        // text: label,
                        value: label,
                        label: label
                    }));
                })
                .catch(error => {
                    console.error('Error fetching data samples:', error);
                });
        },
        changeDataset() {
            // 切换开发集、未标记数据集
            let datasetValue = this.datasetName
            let dataType = this.dataType
            this.tableData = null
            axios.post(this.base_url + '/api/get_different_data', {
                    datasetValue,
                    dataType
                })
                .then(response => {
                    this.tableData = response.data['text'].slice(0, 500)
                    // 下面几项 在相同数据集中都是不变的
                    // this.numToLabel = response.data['labels']
                    // this.datasetType = response.data['setType']
                    // 根据映射创建labelFilters，格式[{ text: '家', value: '家' }, { text: '公司', value: '公司' }]
                    // this.options = this.numToLabel.map(label => ({
                    //     // text: label,
                    //     value: label,
                    //     label: label
                    // }));
                    // console.log(this.options)
                })
                .catch(error => {
                    console.error('Error fetching data samples:', error);
                });
        },
        isDevelopment(dataType) {
            if (dataType == 'development') {
                return true
            } else {
                return false
            }
        },
        labelColor(label) {
            let labelColors = ['primary', 'success', 'warning', 'danger']
            let index = this.labelFilters.findIndex(item => item.value === label);
            return labelColors[index]
        },
        setCurrent(row) {
            this.$refs.singleTable.setCurrentRow(row);
        },
        changeSort() {
            // 切换排序方式：从高到低、从低到高
            this.sortOrder = 1 - this.sortOrder
            this.sortDatas()
        },
        handleCurrentChange(val) {
            // 点击某行返回该文本内容，将，该文本、数据集对应的文本任务类型、标签、数据集传给view2
            this.currentRow = val;
            console.log("view3表格点击的当前行")
            console.log(val)

            let transmitData = {
                dataKey: this.currentRow['index'],
                text: this.currentRow['text'],
                datasetType: this.datasetType,
                labelStr: this.currentRow['textLabelValue'],
                label: this.numToLabel.findIndex(item => item === this.currentRow['textLabelValue']),
                datasetName: this.datasetName
            }
            // console.log("表格选中的值:")
            // console.log(transmitData)
            EventBus.$emit('eventB', transmitData)
        },
        sortDatas() {
            // 更新该表格数据，替换为推荐样本，发送给后端索引（仅限当前读取的是无标签数据）
            if (this.dataType == 'unlabel' || this.dataType == 'Unlabeled Data') {
                let datasetValue = this.datasetName
                let dataIndex = +this.currentRow['index']
                let sortOrder = this.sortOrder

                this.tableData = null

                axios.post(this.base_url + '/api/recommend_unlabel', {
                        datasetValue,
                        dataIndex,
                        sortOrder
                    })
                    .then(response => {
                        this.$message('Reconmmend successfully!');
                        this.tableData = response.data['text'].slice(0, 100)
                        this.minSim = response.data['minSim']
                    })
                    .catch(error => {
                        console.error('Error fetching data samples:', error);
                    });
            }
        },

        // filterTag(value, row) {
        //     return this.numToLabel[row.labelStr] === value;
        // },
        getBackgroundColor(index) {
            if (this.flag_recommand == 1) {
                // 仅对推荐句子的相似度进行颜色底纹的映射
                const score = new Array();
                for (var j = 0; j < this.similarity.length; j++) {
                    score.push(this.similarity[j])
                }
                // const colorScale = d3.scaleSequential(d3.interpolateBlues) // 使用蓝色到绿色的插值函数
                //     .domain([Math.min(...score), Math.max(...score)]); // 定义数据范围
                const max = Math.max(...score); // 找到数组中的最大值
                const secondMax = Math.max(...score.filter(num => num !== max))
                // 定义自定义颜色数组
                const customColors = ['#f6fbff', '#c2daed'];
                const colorScale = d3.scaleSequential()
                    .interpolator(d3.interpolateRgb)
                    .domain([Math.min(...score), secondMax])
                    .range(customColors);
                // 将数据映射到颜色
                const colors = score.map(d => colorScale(d));
                if (index != 0) {
                    return colors[index]
                } else {
                    return `#d7edd5`
                }

            } else {
                // 为了取消掉不是推荐数据的颜色设置
                return `#ffffff`
            }
        },
        filterDataSample(dataKey) {
            // 过滤出由radviz图指定的该数据，并将其置顶
            const index = this.tableData.findIndex(row => row.index === dataKey);
            if (index === -1) return;

            const row = this.tableData.splice(index, 1)[0];

            this.tableData.unshift(row);
            this.$nextTick(() => {
                const table = this.$refs.table;
                if (table) {
                    table.doLayout();
                }
            });
        },
        showUpdateRuleSample(selectedData) {
            // 在迭代LF时，view4点击某个LF，该数据表格处顶部显示view4传过来的当时创建LF的数据样本的依据
            // 同时该视图中的development数据更换顺序，使用后端传来的冲突+错过+正确标签+正确错过的样本顺序
            // console.log("view3中")
            // console.log(selectedData)
            const newRow = {
                'index': selectedData['index'],
                'text': selectedData['data']['text'],
                'textLabelValue': this.numToLabel[selectedData['label']],
                'highlighted': true,
                'category': 'new', // Set category to 'new' 
            }
            this.tableData = null
            // 先置空再重新存放
            let datasetValue = this.datasetName
            let ruleId = selectedData['ruleId']
            let ruleLabel = selectedData['ruleLabel']

            axios.post(this.base_url + '/api/sort_weak_labels', {
                    datasetValue,
                    ruleId,
                    ruleLabel
                })
                .then(response => {
                    this.tableData = response.data['text']
                    this.numToLabel = response.data['labels']
                    this.datasetType = response.data['setType']
                    // 根据映射创建labelFilters，格式[{ text: '家', value: '家' }, { text: '公司', value: '公司' }]
                    this.options = this.numToLabel.map(label => ({
                        // text: label,
                        value: label,
                        label: label
                    }));
                    this.tableData.unshift(newRow);
                    //刷新列表
                    this.$nextTick(() => {
                        this.$refs.table.doLayout(); // Trigger layout recalculation
                    });

                    // 将右上角按钮改变值
                    this.dataType = 'development'

                })
                .catch(error => {
                    console.error('Error fetching data samples:', error);
                });

        },
        rowStyle({
            row
        }) {
            if (this.dataType === 'unlabel' || this.dataType === 'Unlabeled Data') {
                return {
                    backgroundColor: this.getBackgroundColor(row.similarity),
                };
            }
            return {};
        },
        rowClassName({
            row
        }) {
            if (row.category === 'new') {
                return 'row-new';
            }
            if (row.category === 'wrong') {
                return 'row-wrong';
            } else if (row.category === 'miss') {
                return 'row-miss';
            } else if (row.category === 'same') {
                return 'row-same';
            } else
                return '';
        },
        getBackgroundColor(similarity) {
            let minSim = this.minSim
            // 从高到低进行推荐
            const colorScale = d3.scaleLinear()
                .domain([minSim, (minSim + 1) / 2, 1])
                .range(['#e6f3d2', 'white', '#fae1ee']);

            return colorScale(similarity)

        }

    }
};
</script>

<style>
.ivu-card-body {
    overflow: auto;
    overflow-x: hidden;
}

.row-background {
    transition: background-color 0.3s ease;
}

.datashow {
    width: 100%;
    /* height: 170px; */
}

.highlight {
    color: #d90000;
    font-weight: bold;
}

.row-wrong {
    background-color: #fbecec !important;
}

.row-miss {
    background-color: #fffddd !important;
}

.row-same {
    background-color: #edfdf0 !important;
}

.row-new {
    background-color: #DCDFE6 !important;
}

.el-table .el-table__cell {
    padding: 2px 0;
}

.text-left,
.text-right {
    height: 100%;
    /* overflow: auto;
    overflow-x: hidden; */
    transition: width 0.5s ease;
}

.datashow::-webkit-scrollbar {
    -webkit-appearance: none;
    width: 6px;
    /* height: 6px; */
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 0;
}

::-webkit-scrollbar-thumb {
    cursor: pointer;
    border-radius: 5px;
    background: rgba(0, 0, 0, 0.15);
    transition: color 0.2s ease;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.3);
}

.datashow {
    height: 216px;
}

.ivu-card-extra {
    position: absolute;
    right: 2px;
    top: 1.5px;
}

.button-add {
    color: #747474;
    font-size: 15px;
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

.one_text {
    cursor: pointer;
    display: block;
    width: 100%;
    height: auto;
    margin-bottom: 5px;
    border-radius: 8px;
    padding: 14px;
    /* -webkit-box-shadow: inset 0 0 4px 0 rgba(84, 167, 255, 0.3), 0 0 2px 0 rgba(0, 0, 0, 0.2); */
}

.one_text:hover {
    background-color: #dcecdbd9 !important;

}

.one_text.active {
    background-color: #d7edd5 !important;
}

.el-tag--dark.el-tag--info {
    background-color: #b3b3b3;
    border-color: #b3b3b3;
    color: #fff;
}
</style>
