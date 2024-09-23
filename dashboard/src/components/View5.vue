<template>
<div>
    <Card class="myCard myCard5">
        <template #extra>
            <el-button size="mini" @click="drawMatrix">Update Status<i class="el-icon-upload el-icon--right"></i></el-button>
        </template>

        <p slot="title">LF Relation & Data Relation</p>
        <div class="matrix">
            <svg id="matrix" width="300" height="400"></svg>
        </div>
        <div class="radviz">
            <svg id="radviz" width="600" height="600"></svg>
        </div>

    </Card>
</div>
</template>

<script>
import axios from 'axios';
import * as d3 from 'd3';
import {
    EventBus
} from '../EventBus.js';
export default {
    data() {
        return {
            datasetValue: null,
            radvizIndex1: null,
            radvizIndex2: null,
            base_url: "http://127.0.0.1:5001"
        };
    },
    mounted() {
        EventBus.$on('eventD', (datasetValue) => {
            // 用=>才可以使用this指向,function不行
            this.datasetValue = datasetValue
        })
        // this.drawMatrix()
    },
    methods: {
        convexArray(lf1, lf2) {
            let selectedlf1Nodes = []
            let selectedlf2Nodes = []
            var color000 = 'none';
            // 获取当前的节点
            d3.selectAll(".data-point")
                .attr('stroke', d => {
                    console.log(d.weak_labels)
                    if (d.weak_labels[lf1] != -1) {
                        selectedlf1Nodes.push([d.x, d.y]);
                        color000 = `#8d4581`
                    }
                    if (d.weak_labels[lf2] != -1) {
                        selectedlf2Nodes.push([d.x, d.y]);
                        color000 = `#CFCE5B`
                    }
                    if (d.weak_labels[lf2] != -1 && d.weak_labels[lf1] != -1) {
                        // 同时标记的话就高亮
                        color000 = `black`
                    }
                    return color000
                })
                .attr("stroke-width", d => {

                    if (d.weak_labels[lf1] != -1) {
                        return 2
                    }
                    if (d.weak_labels[lf2] != -1) {
                        return 2
                    }
                    if (d.weak_labels[lf2] != -1 && d.weak_labels[lf1] != -1) {
                        // 同时标记的话就高亮
                        return 3
                    }
                })
            // console.log(selectedlf1Nodes)
            // console.log(selectedlf2Nodes)

            // 画凸包
            d3.selectAll(".onehull").remove();

            this.drawConvex(selectedlf1Nodes, ['rgba(141, 69, 129,0.3)', '#8d4581'])
            this.drawConvex(selectedlf2Nodes, ['rgba(207, 206, 91, 0.3)', '#CFCE5B'])

        },
        drawMatrix() {
            let datasetName = this.datasetValue
            axios.post(this.base_url + '/api/draw_matrix', {
                    datasetName
                })
                .then(response => {
                    this.$message('Compute Influence Scores successfully!');
                    let matrix_all = response.data
                    const svg = d3.select("#matrix")
                    // 去除对角线元素,并且去除最后一行
                    const matrix = matrix_all
                        .slice(0, -1) // 去除最后一行
                        .map((row, rowIndex) => {
                            // 过滤掉对角线元素
                            return row.filter((_, colIndex) => colIndex !== rowIndex);
                        });

                    const n = matrix.length + 1;
                    const margin = {
                        top: 0,
                        right: 0,
                        bottom: 50,
                        left: 0
                    };
                    const width = 450 - margin.left - margin.right;
                    const height = 550 - margin.top - margin.bottom;

                    // 清除之前的内容
                    svg.selectAll("*").remove();
                    var tooltip = d3.select("body").append("div")
                        .attr("class", "tooltip")
                        .style("opacity", 0);

                    // 设置SVG的宽高
                    svg.attr('width', width + margin.left + margin.right)
                        .attr('height', height + margin.top + margin.bottom);

                    const g = svg.append('g')

                    // 创建一个组元素用于放置矩阵
                    const matrixGroup = svg.append("g")
                        .attr("transform", `translate(${margin.left},${margin.top} )`); // 平移到正确位置

                    var that = this;
                    // 计算格子大小
                    let cellSize;
                    // if (n > 3) {
                    cellSize = Math.min(width / n / Math.SQRT2 / 1, height / n / Math.SQRT2);
                    // } else {
                    // cellSize = Math.min(width / n / Math.SQRT2 / 2, height / n / Math.SQRT2 / 3);
                    // }

                    // 1. 获取矩阵的最大值和最小值,排除对角线
                    const maxValue = d3.max(matrix, (row, i) => d3.max(row.filter((_, j) => i !== j))); // 排除对角线上的最大值
                    const minValue = d3.min(matrix, (row, i) => d3.min(row.filter((_, j) => i !== j))); // 排除对角线上的最小值

                    const padding = cellSize * 0.05; // 矩形之间的间隔
                    // const padding = 0; // 矩形之间的间隔

                    const cellRadius = 0; // 矩形圆角的半径

                    // 2. 构建颜色比例尺
                    // 冗余颜色比例尺 (白色到橙色)
                    const colorScale = d3.scaleLinear()
                        .domain([0, maxValue])
                        .range(['white', '#06D3C5']);

                    // 冲突颜色比例尺 (蓝色到白色)
                    const colorScale2 = d3.scaleLinear()
                        .domain([minValue, 0]) // 负值
                        .range(['#bea6a0', 'white']);

                    // 3. 绘制上三角矩阵并应用颜色比例尺
                    matrixGroup.selectAll("rect")
                        .data(matrix.flat())
                        .enter()
                        .append("rect")
                        .attr("x", (d, i) => {
                            const row = Math.floor(i / matrix.length);
                            const col = i % matrix.length;
                            return col >= row ? col * cellSize + 2 : null; // 仅绘制上三角
                        })
                        .attr("y", (d, i) => {
                            const row = Math.floor(i / matrix.length);
                            const col = i % matrix.length;
                            return col >= row ? row * cellSize + 2 : null; // 仅绘制上三角
                        })
                        .attr("width", cellSize - padding)
                        .attr("height", cellSize - padding)
                        .attr("rx", cellRadius) // 圆角半径
                        .attr("ry", cellRadius) // 圆角半径
                        .style("fill", (d, i) => {
                            const row = Math.floor(i / matrix.length);
                            const col = i % matrix.length;
                            // 仅为上三角元素着色（排除对角线）
                            if (col >= row) {
                                if (d > 0) {
                                    return colorScale(d); // 冗余值使用橙色比例尺
                                } else {
                                    return colorScale2(d); // 冲突值使用蓝色比例尺
                                }
                            }
                            return "none"; // 不绘制下三角或对角线
                        })
                        .style("stroke", (d, i) => {
                            const row = Math.floor(i / matrix.length);
                            const col = i % matrix.length;
                            // // 仅为上三角元素着色（排除对角线）
                            if (col >= row) {
                                return `#56423d`;
                            } else {
                                return 'none';
                            }
                        })
                        .style("stroke-dasharray", "8,3")
                        .style("stroke-width", 1.5)
                        .on("mouseover", function (event, d) {
                            // 获取当前点击元素的索引
                            const rects = matrixGroup.selectAll("rect").nodes();
                            const index = rects.indexOf(this);
                            // 计算行和列
                            const row = Math.floor(index / matrix.length);
                            const col = index % matrix.length + 1;
                            const LfsName = '.LF' + row;
                            const LfsName2 = '.LF' + col;

                            const Lfs = d3.select(LfsName).attr("fill", "red");
                            const Lfs2 = d3.select(LfsName2).attr("fill", "red");

                            tooltip.transition()
                                .duration(200)
                                .style("opacity", .9);
                            tooltip.html(`Related LFs: LF${row} and LF${col}<br/>Data Count: ${d}<br/>`)
                                .style("left", (event.pageX + 10) + "px")
                                .style("top", (event.pageY - 28) + "px");

                        })
                        .on("mousemove", function (event) {
                            tooltip.style("left", (event.pageX + 10) + "px")
                                .style("top", (event.pageY - 28) + "px");
                        })
                        .on("mouseout", function (d) {
                            const rects = matrixGroup.selectAll("rect").nodes();
                            const index = rects.indexOf(this);
                            // 计算行和列
                            const row = Math.floor(index / matrix.length);
                            const col = index % matrix.length + 1;
                            const LfsName = '.LF' + row;
                            const LfsName2 = '.LF' + col;

                            const Lfs = d3.select(LfsName).attr("fill", "black");
                            const Lfs2 = d3.select(LfsName2).attr("fill", "black");

                            tooltip.transition()
                                .duration(100)
                                .style("opacity", 0);
                        })
                        .on("click", function (event, d) {
                            // 获取当前点击元素的索引
                            const rects = matrixGroup.selectAll("rect").nodes();
                            const index = rects.indexOf(this);
                            // 先把之前加粗文字样式清空
                            g_path.selectAll("text").style("font-weight", "normal");
                            // 计算行和列
                            const row = Math.floor(index / matrix.length);
                            const col = index % matrix.length;

                            const LfsName = '.LF' + row;
                            const LfsName2 = '.LF' + (col + 1);

                            const Lfs = d3.select(LfsName).attr("fill", "red")
                                .style("font-weight", "bold");
                            const Lfs2 = d3.select(LfsName2).attr("fill", "red")
                                .style("font-weight", "bold");
                            // const value = matrix[row][col]
                            // console.log(`行: ${row}, 列: ${col+1}, 值: ${value}`);
                            //找到点击时触发的LF的索引
                            that.radvizIndex1 = row;
                            that.radvizIndex2 = col + 1;
                            // console.log(this.radvizIndex1, this.radvizIndex2);
                            // 画凸包并高亮
                            that.convexArray(that.radvizIndex1, that.radvizIndex2); //LF0,LF1
                        });

                    // 2.创建一个 g 容器
                    // 创建一个 g 容器
                    const g_path = svg.append("g")
                        .attr("transform", `translate(${margin.left},${margin.top})`); // 平移到正确位置

                    // 计算单元大小和梯形参数
                    var juxing_length = 80; // 对角线长度

                    // 准备梯形数据
                    const trapezoidData = d3.range(n).map(i => {
                        let x_start = margin.left - cellSize + i * cellSize;
                        let y_start = margin.top + i * cellSize;

                        // 计算5个点的坐标
                        const x1 = x_start; // 左上角起点
                        const y1 = y_start;

                        const x2 = x1 + cellSize; // 向右移动一个cellSize单位
                        const y2 = y1;

                        const x3 = x2; // 垂直向下移动一个cellSize单位
                        const y3 = y2 + cellSize;

                        const x4 = x3 - juxing_length * Math.cos(Math.PI / 4); // 计算x4
                        const y4 = y3 + juxing_length * Math.sin(Math.PI / 4); // 计算y4

                        const x5 = x4 - cellSize * Math.sqrt(2) * Math.cos(Math.PI / 4); // 计算x5
                        const y5 = y4 - cellSize * Math.sqrt(2) * Math.sin(Math.PI / 4); // 计算y5

                        // 返回每个梯形的路径数据
                        return {
                            pathData: [
                                [x1, y1],
                                [x2, y2],
                                [x3, y3],
                                [x4, y4],
                                [x5, y5],
                                [x1, y1]
                            ]
                        };
                    });

                    // 3 填充左边部分
                    const diagonalValues = matrix_all.map((row, i) => row[i]); // 获取对角线上的值

                    // 构建归一化比例尺,用于对角线值的归一化处理
                    const fillScale = d3.scaleLinear()
                        .domain([d3.min(diagonalValues), d3.max(diagonalValues)]) // 使用对角线值的最小值和最大值
                        .range([0, 1]); // 将值映射到 [0, 1] 范围
                    // 应用到 g_path 中的每个梯形
                    g_path.selectAll("path")
                        .data(trapezoidData)
                        .enter()
                        .append('path')
                        .attr('d', d => {
                            const path = d3.path();
                            d.pathData.forEach(([x, y], i) => {
                                if (i === 0) {
                                    path.moveTo(x - margin.left, y - margin.top); // 修正起点为 (0,0)
                                } else {
                                    path.lineTo(x - margin.left, y - margin.top); // 修正所有点的坐标
                                }
                            });
                            path.closePath();
                            return path.toString();
                        })
                        .attr('stroke', 'none')
                        .attr('fill', (d, i) => {
                            const diagonalIndex = Math.min(i, diagonalValues.length - 1); // 确保索引不超出
                            const fillRatio = fillScale(diagonalValues[diagonalIndex]); // 获取填充比例

                            // 创建部分填充的路径

                            const partialPath = d3.path();
                            const [x1, y1] = d.pathData[0]; // 右上角
                            const [x2, y2] = d.pathData[1]; // 右下角
                            const [x3, y3] = d.pathData[2]; // 左下角
                            const [x4, y4] = d.pathData[3]; // 左上角
                            const [x5, y5] = d.pathData[4]; // 左上角

                            const labelHeight = y4 - y3;
                            const padding_h = labelHeight * 0.2;
                            const transform_ratio = 0.4
                            // 根据填充比例决定如何填充
                            // if (fillRatio < 1) {
                            // 仅部分填充三角形部分
                            const xPartial4 = x3 - cellSize * transform_ratio * Math.cos(Math.PI / 4) - juxing_length * fillRatio * Math.cos(Math.PI / 4);
                            const yPartial4 = y3 - cellSize * transform_ratio * Math.sin(Math.PI / 4) + juxing_length * fillRatio * Math.cos(Math.PI / 4);

                            const xPartial5 = x1 + cellSize * transform_ratio * Math.cos(Math.PI / 4) - juxing_length * fillRatio * Math.cos(Math.PI / 4);
                            const yPartial5 = y1 + cellSize * transform_ratio * Math.sin(Math.PI / 4) + juxing_length * fillRatio * Math.cos(Math.PI / 4);

                            // // 三角形
                            partialPath.moveTo(x1 + cellSize * transform_ratio * Math.cos(Math.PI / 4), y1 + cellSize * transform_ratio * Math.sin(Math.PI / 4)); // 从右上角开始
                            partialPath.lineTo(x2 - cellSize * transform_ratio * Math.cos(Math.PI / 4), y2 + cellSize * transform_ratio * Math.sin(Math.PI / 4)); // 右下角
                            partialPath.lineTo(x3 - cellSize * transform_ratio * Math.cos(Math.PI / 4), y3 - cellSize * transform_ratio * Math.sin(Math.PI / 4)); // 填充到三角形的部分
                            partialPath.closePath();
                            // const x5 = x4 - cellSize * Math.sqrt(2) * Math.cos(Math.PI / 4); // 计算x5
                            // const y5 = y4 - cellSize * Math.sqrt(2) * Math.sin(Math.PI / 4);

                            // 正方形
                            partialPath.moveTo(x1 + cellSize * transform_ratio * Math.cos(Math.PI / 4), y1 + cellSize * transform_ratio * Math.sin(Math.PI / 4)); // 从右上角开始
                            partialPath.lineTo(x3 - cellSize * transform_ratio * Math.cos(Math.PI / 4), y3 - cellSize * transform_ratio * Math.sin(Math.PI / 4)); // 右下角
                            partialPath.lineTo(xPartial4, yPartial4); // 左下
                            partialPath.lineTo(xPartial5, yPartial5); // 左上
                            partialPath.closePath();
                            // }
                            // } else {
                            //     // 完全填充整个梯形
                            //     partialPath.moveTo(x1, y1); // 右上角
                            //     partialPath.lineTo(x2, y2); // 右下角
                            //     partialPath.lineTo(x3, y3); // 左下角
                            //     partialPath.lineTo(x4, y4); // 左上角
                            //     partialPath.lineTo(x5, y5); // 左上角
                            //     partialPath.lineTo(x1, y1); // 回到右上角
                            //     partialPath.closePath();
                            // }

                            // 返回部分或完整填充的路径
                            const partialFillPath = partialPath.toString();

                            // 追加部分填充的路径
                            g_path.append("path")
                                .attr("d", partialFillPath)
                                .attr("fill", "#c0c0c0")
                                // .attr("stroke","black")
                                .attr("transform", `translate(${-margin.left},${-margin.top} )`)

                            return "none"; // 避免重复填充
                        })
                        .attr('stroke-width', 1);

                    // 4.添加文字
                    // 创建 glyph 容器
                    var a = []
                    g_path.selectAll("g")
                        .data(trapezoidData)
                        .enter()
                        .append("g")
                        .each(function (d, i) {
                            const g = d3.select(this);

                            // 获取四个顶点
                            const [x1, y1] = d.pathData[0]; // 右上角
                            const [x2, y2] = d.pathData[2]; // 右下角
                            const [x3, y3] = d.pathData[3]; // 左下角
                            const [x4, y4] = d.pathData[4]; // 左上角
                            // console.log(y4, y3)
                            // const labelHeight = y4 - y3;
                            // const padding_h = labelHeight * 0.2;

                            // 创建路径
                            g.append("path")
                                .attr('d', () => {
                                    const newPath = d3.path();
                                    newPath.moveTo(x1, y1);
                                    newPath.lineTo(x2, y2);
                                    newPath.lineTo(x3, y3);
                                    newPath.lineTo(x4, y4);
                                    newPath.closePath();
                                    return newPath.toString();
                                })
                                // .attr('stroke', 'red')
                                .attr('fill', 'transparent') // 透明背景填充
                                .attr("transform", `translate(${-margin.left},${-margin.top})`);

                            // 计算路径的中心点,放置文字
                            const centerX = (x1 + x2 + x3 + x4) / 4; // 计算中心点x
                            const centerY = (y1 + y2 + y3 + y4) / 4; // 计算中心点y
                            // 添加文字到路径的中心

                            const rectWidth = 40;
                            const rectHeight = 20;
                            // 给文字添加外边框
                            g.append("rect")
                                .attr("x", centerX - margin.left - rectWidth / 2)
                                .attr("y", centerY - margin.top - rectHeight / 2)
                                .attr("width", rectWidth)
                                .attr("height", rectHeight)
                                .attr("rx", 3)
                                .attr("ry", 3)
                                .attr("transform", d => {
                                    var b = `rotate(${-45}, ${centerX - margin.left}, ${centerY - margin.top})`;
                                    return b
                                })
                                .attr("fill", "none") // 矩形填充颜色
                                .attr("stroke", "black") // 边框颜色
                                .attr("stroke-width", 1); // 边框宽度

                            g.append("text")
                                .attr("class", "textLabel")
                                .attr("x", centerX - margin.left) // 将文字放置在路径的中心
                                .attr("y", centerY - margin.top)
                                .attr("dy", ".35em") // 垂直方向微调,让文字居中
                                .attr("text-anchor", "middle") // 文字水平居中
                                .attr("transform", d => {
                                    var b = `rotate(${-45}, ${centerX - margin.left}, ${centerY - margin.top})`;
                                    a.push(b);
                                    return b
                                }) // 逆向旋转文字,使其水平
                                .text(`LF${i}`) // 生成 "LF+0" 到 "LF+n-1" 的标签
                                .attr("class", `LF${i}`)
                                .attr("fill", "black") // 文字颜色
                                .style("font-size", "16px"); // 文字大小
                        });

                    let translateX, translateY, rotateAngle;

                    // 根据 n 的大小来动态设置旋转和平移的值
                    if (n <= 3) {
                        translateX = 280; // 对于小的 n 值,使用较小的平移
                        translateY = -100;
                        rotateAngle = 45; // 可以保持旋转角度不变
                    } else {
                        translateX = 250; // 对于较大的 n 值,使用较大的平移
                        translateY = -60;
                        rotateAngle = 45; // 同样的旋转角度
                    }

                    // 最后进行旋转和平移变换
                    matrixGroup.attr('transform', `rotate(${rotateAngle}) translate(${translateX}, ${translateY})`);
                    g_path.attr('transform', `rotate(${rotateAngle}) translate(${translateX}, ${translateY})`);
                    // g_path.attr('transform', `translate(${translateX}, ${translateY})`);
                    // 获取四个顶点

                    g_path.selectAll("text").attr("transform", (d, i) => {
                        // return a[i] + ` translate(${-cellSize*1.1},0)`
                        return a[i] + ` translate(${-cellSize*0.5-juxing_length*0.5},0)`
                    })

                    g_path.selectAll("rect").attr("transform", (d, i) => {
                        // return a[i] + ` translate(${-cellSize*1.1},0)`
                        return a[i] + ` translate(${-cellSize*0.5-juxing_length*0.5},0)`
                    })
                    // console.log(matrixGroup.node().getBBox()); // 获取 g_matrix 的边界框
                    // console.log(g_path.node().getBBox()); // 获取 g_path 的边界框

                    this.drawRadviz()

                })
                .catch(error => {
                    console.error('Error fetching data samples:', error);
                });
        },
        drawRadviz() {
            let datasetName = this.datasetValue
            d3.select('#radviz').selectAll('*').remove()
            const legendData = [{
                    shape: d3.symbolSquare,
                    label: "Unlabeled"
                },
                {
                    shape: d3.symbolCircle,
                    label: "Redundancy"
                },
                {
                    shape: d3.symbolTriangle,
                    label: "Conflict"
                }
            ];
            const svg = d3.select('#radviz');
            // 定义符号生成器
            const symbol = d3.symbol()
                .size(50); 
            // 绘制图例
            legendData.forEach((d, i) => {
                symbol.type(d.shape);
                svg.append("path")
                    .attr("d", symbol())
                    .attr("transform", `translate(510, ${520 + i * 30})`) // 调整位置
                    .attr("fill", "black"); // 设置符号颜色

                svg.append("text")
                    .attr("x", 520) // 文本起始 x 位置
                    .attr("y", 520 + i * 30) // 文本 y 位置
                    .text(d.label)
                    .attr("dominant-baseline", "middle") // 垂直居中
                    .attr("font-size", "12px"); // 设置字体大小
            });
            axios.post(this.base_url + '/api/get_influence_score', {
                    datasetName
                })
                .then(response => {
                    let data = response.data['datas']
                    let sortLF = response.data['sortLFs']
                    let sortLabels = response.data['sortLabels']

                    // 定义画布尺寸
                    const width = 600;
                    const height = 600;
                    const radius = Math.min(width, height) / 2 - 50;

                    // 创建SVG元素
                    const svg = d3.select("#radviz")
                        .attr("width", width)
                        .attr("height", height)
                        .append("g")
                        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

                    // 定义角度比例尺
                    const angle = d3.scaleLinear()
                        .domain([0, Object.keys(data[0].promptsif).length])
                        .range([0, 2 * Math.PI]);

                    // 定义圆的半径比例尺
                    const radiusScale = d3.scaleLinear()
                        .domain([0, d3.max(data, d => d3.max(Object.values(d.promptsif)))]).nice()
                        .range([0, radius]);

                    // 定义四个特征位置
                    const features = sortLF;
                    // features=['LF0','LF3','LF4','LF1','LF2','LF5']
                    // console.log("排序++++")
                    // console.log(features)
                    const points = features.map((feature, i) => {
                        return {
                            angle: angle(i),
                            label: feature,
                            radius: radius, // 标签距离圆心的距离
                            labelStr: sortLabels[i] //规则指向的标签
                        };
                    });

                    const piece = features.length
                    const colors = ['#76a9cb', '#e26f51', "#f56c6c", '#e6a23c']

                    const radiusArc = 1
                    const arcGenerator = d3.arc()
                        .innerRadius(radius - radiusArc) // 弧的内半径
                        .outerRadius(radius + radiusArc) // 弧的外半径
                        .startAngle(d => d.angle) // 起始角度
                        .endAngle(d => d.angle + 0.9 * 2 * Math.PI / piece); // 结束角度（调整弧的宽度）
                    // .startAngle(d => d.angle) // 起始角度
                    // .endAngle(d => d.angle + Math.PI / piece); // 结束角度（调整弧的宽度）

                    svg.selectAll(".feature-arc")
                        .data(points)
                        .enter().append("path")
                        .attr("class", "feature-arc")
                        .attr("d", arcGenerator)
                        .attr("transform", `translate(0, 0)`) // 平移到圆心
                        .attr("fill", d => {
                            return colors[d.labelStr]
                        }) // 弧的颜色
                    // .style("stroke", "black"); // 去掉边框

                    svg.selectAll(".feature-point")
                        .data(points)
                        .enter().append("circle")
                        .attr("class", "feature-point")
                        // .attr("cx", d => d.radius * Math.cos(d.angle - Math.PI / 2 + Math.PI / piece))
                        // .attr("cy", d => d.radius * Math.sin(d.angle - Math.PI / 2 + Math.PI / piece))
                        // .attr("cx", (d, i) => {
                        //     console.log(i);
                        //     console.log((d.angle + 0.9 * Math.PI / piece) / (2 * Math.PI) * 360);
                        //     return d.radius * Math.sin(d.angle + 0.9 * Math.PI / piece)
                        // })
                        .attr("cx", (d, i) => {
                            var xx = d.radius * Math.sin(d.angle + 0.9 * Math.PI / piece)
                            return xx
                        })
                        .attr("cy", (d, i) => {
                            var yy = d.radius * Math.cos(d.angle + 0.9 * Math.PI / piece);
                            return -yy
                        })

                        // .attr("cy", d => d.radius * Math.cos(d.angle + 0.9 * Math.PI / piece))
                        .attr("r", 5) // 模拟的边缘圆
                        .attr("stroke", d => {
                            return colors[d.labelStr]
                        })
                        .attr("stroke-width", 3)
                        .attr("fill", "white");

                    // 添加特征标签:LF1 LF2...
                    svg.selectAll(".label")
                        .data(points)
                        .enter().append("text")
                        .attr("x", (d, i) => {
                            if (d.angle + 0.9 * Math.PI / piece <= Math.PI) {
                                var xx = (d.radius + 25) * Math.sin(d.angle + 0.9 * Math.PI / piece);
                                return xx
                            } else {
                                var xx = (d.radius + 35) * Math.sin(d.angle + 0.9 * Math.PI / piece);
                                return xx
                            }

                            // return d.radius * Math.sin(d.angle + 0.9 * Math.PI / piece)
                        }).attr("y", (d, i) => {
                            if (d.angle + 0.9 * Math.PI / piece <= Math.Pi) {
                                var yy = (d.radius + 25) * Math.cos(d.angle + 0.9 * Math.PI / piece);
                                return -yy
                            } else {
                                var yy = (d.radius + 35) * Math.cos(d.angle + 0.9 * Math.PI / piece);
                                return -yy
                            }

                            // }
                        })
                        // .attr("x", d => (d.radius) * Math.sin(d.angle + 0.9 * Math.PI / piece))
                        // .attr("y", d => (d.radius) * Math.cos(d.angle + 0.9 * Math.PI / piece))
                        .attr("dy", "0.35em")
                        .attr("class", "label")
                        .text(d => d.label);

                    var tooltip = d3.select("body").append("div")
                        .attr("class", "tooltip")
                        .style("opacity", 0);

                    var drag = d3.drag()
                        .on("start", (event, d) => {
                            if (!event.active) simulation.alphaTarget(0.3).restart();
                            d.fx = d.x;
                            d.fy = d.y;
                        })
                        .on("drag", (event, d) => {
                            d.fx = event.x;
                            d.fy = event.y;
                        })
                        .on("end", (event, d) => {
                            if (!event.active) simulation.alphaTarget(0);
                            d.fx = null;
                            d.fy = null;
                        });

                    const max = data.reduce((maxValue, obj) => {
                        const values = Object.values(obj.promptsif);
                        const localMax = Math.max(...values);
                        return Math.max(maxValue, localMax);
                    }, -Infinity);

                    // console.log(max)

                    const scale = d3.scaleLinear()
                        .domain([0, max]) // 输入范围
                        .range([0, 1]);

                    // const emptyPosition = []
                    const dataPoints = data.map(d => {
                        let x = 0; // 数据点的x坐标
                        let y = 0; // 数据点的y坐标
                        let featureValues = d.promptsif; // 数据点的特征值
                        let conflictFlag = d.conflictFlag;
                        let label = d.label;
                        let dataKey = d.dataKey;
                        let weak_labels = d.weak_labels;
                        let promptsif = d.promptsif
                        let x_s = 0
                        let y_s = 0
                        let featureValueSum = 0
                        // 遍历特征点，根据特征值计算数据点的位置
                        points.forEach(featurePoint => {
                            // console.log(featurePoint);
                            const featureValue = featureValues[featurePoint.label]; // 获取特征值
                            const featureAngle = featurePoint.angle; // 特征点的角度
                            const featureRadius = featurePoint.radius; // 特征点的半径
                            ``
                            // 根据RadViz的计算公式计算数据点的位置
                            const dx = Math.sin(featureAngle + 0.9 * Math.PI / piece);
                            const dy = -Math.cos(featureAngle + 0.9 * Math.PI / piece);
                            // x_s += scale(featureValue)
                            // y_s += scale(featureValue)
                            // 更新数据点的x和y坐标
                            x += dx * featureValue;
                            y += dy * featureValue;
                            featureValueSum += featureValue;

                            // console.log("------")
                            // console.log(x, y, dx, dy, featureValue, featureValueSum)
                        });
                        x = featureValueSum == 0 ? 0 : x / featureValueSum * radius * 0.9;
                        y = featureValueSum == 0 ? 0 : y / featureValueSum * radius * 0.9;
                        // console.log(x, y, featureValueSum)
                        // console.log("+++++")
                        // x_s = x / x_s
                        // y_s = y / y_s
                        // emptyPosition.push([x, y])

                        return {
                            x,
                            y,
                            // x_s,
                            // y_s,
                            conflictFlag,
                            label,
                            dataKey,
                            weak_labels,
                            promptsif
                        }; // 返回数据点的x和y坐标
                    });

                    function getFeaturePosition(key) {
                        const point = points.find(p => p.label === key);
                        if (!point) return {
                            cx: 0,
                            cy: 0
                        }; // 如果找不到对应的点,返回原点
                        // .attr("x2", (points, i) => {
                        //     var xx = points[i].radius * Math.sin(points[i].angle + 0.9 * Math.PI / piece);
                        //     console.log("点点滴啊");
                        //     console.log(xx);
                        //     console.log(points);
                        //     return xx
                        // })
                        // .attr("y2", (points, i) => {
                        //     var yy = points[i].radius * Math.cos(points[i].angle + 0.9 * Math.PI / piece);
                        //     return -yy
                        // })

                        const anglePerFeature = 2 * Math.PI / features.length;
                        // console.log(cx,cy);
                        // console.log(point.radius, point.angle);
                        const cx = point.radius * Math.sin(point.angle + 0.9 * Math.PI / piece);
                        const cy = -point.radius * Math.cos(point.angle + 0.9 * Math.PI / piece);

                        return {
                            cx,
                            cy
                        };
                    }

                    const linkGroup = svg.append("g").attr("class", "link-group");

                    const symbolSize = 80

                    svg.selectAll(".data-point")
                        .data(dataPoints)
                        .enter().append("path")
                        .attr("class", "data-point")
                        .style("z-index", "10000")
                        .attr("d", d => {
                            // 根据 conflictFlag 属性选择形状
                            if (d.conflictFlag === 0) {
                                // 圆形
                                return d3.symbol().type(d3.symbolCircle).size(symbolSize)();
                            } else if (d.conflictFlag === -1) {
                                // 正方形
                                return d3.symbol().type(d3.symbolSquare).size(symbolSize)();
                            } else if (d.conflictFlag === 1) {
                                // 三角形
                                return d3.symbol().type(d3.symbolTriangle).size(symbolSize)();
                            }
                        })
                        .attr("transform", function (d) {
                            return `translate(${d.x}, ${d.y})`; // 设置位置
                        })
                        .attr("fill", d => colors[d.label]) // 使用颜色数组
                        .on("mouseover", function (event, d) {
                            tooltip.transition()
                                .duration(200)
                                .style("opacity", .9);
                            tooltip.html(`Label: ${d.label}<br/>Key:${d.dataKey}<br/>Weak labels:${d.weak_labels}`)
                                .style("left", (event.pageX + 10) + "px")
                                .style("top", (event.pageY - 28) + "px");
                            // 绘制连接线
                            const links = linkGroup.selectAll(".link")
                                .data(Object.keys(d.promptsif).filter(key => d.promptsif[key] > 0))
                                .enter().append("line")
                                .attr("class", "link")
                                .attr("x1", d.x)
                                .attr("y1", d.y)
                                .attr("x2", d => getFeaturePosition(d).cx)
                                .attr("y2", d => getFeaturePosition(d).cy)
                                .attr("stroke-width", 4)
                                .attr("opacity", 0.6)
                                .attr("stroke", "#A3A3A3"); //"#e6a23c"
                        })
                        .on("mousemove", function (event) {
                            // 更新tooltip位置
                            tooltip.style("left", (event.pageX + 10) + "px")
                                .style("top", (event.pageY - 28) + "px");
                        })
                        .on("mouseout", function (d) {
                            // 隐藏tooltip
                            tooltip.transition()
                                .duration(100)
                                .style("opacity", 0);
                            linkGroup.selectAll(".link").remove();
                        })
                        .on("click", function (event, d) {
                            // 将key值传回给view3,在数据中搜寻该数据并将其置顶
                            // console.log(`Clicked data point key: ${d.dataKey}`);
                            let dataKey = d.dataKey;
                            EventBus.$emit('eventK', dataKey)
                        });

                    var that = this
                    const simulation = d3.forceSimulation(dataPoints)
                        .force("x", d3.forceX(d => d.x).strength(0.1))
                        .force("y", d3.forceY(d => d.y).strength(0.1))
                        .force("collide", d3.forceCollide().radius(5))
                        .alphaDecay(0.1)
                        .on("tick", () => {
                            // 更新图形的位置
                            svg.selectAll(".data-point")
                                .data(dataPoints)
                                .attr("transform", d => `translate(${d.x}, ${d.y})`)
                        })
                    // .on("end", function () {
                    //     // 清空 coordinates 数组
                    //     let coordinates = [];
                    //     svg.selectAll(".data-point").each(function (d) {
                    //         let oneData = {
                    //             "dataKey": d.dataKey,
                    //             "x": d.x,
                    //             "y": d.y
                    //         };
                    //         coordinates.push(oneData);
                    //     });
                    //     // 确保 coordinates 已经完整填充
                    //     // console.log(coordinates);
                    //     // if (coordinates.length > 0) {
                    //     //     // 将位置数据发送给后端进行无标签数据的投影
                    //     //     axios.post(that.base_url + '/api/project_unlabel', {
                    //     //             datasetName,
                    //     //             coordinates
                    //     //         })
                    //     //         .then(response => {
                    //     //             let unlabelProject = response.data;
                    //     //             // console.log("Request successful");
                    //     //             const resultArray = unlabelProject.map(item => [item.x, item.y]);
                    //     //             // 定义圆心和半径
                    //     //             const centerX = 0;
                    //     //             const centerY = 0;

                    //     //             const radius = 250;
                    //     //             const points = resultArray

                    //     //             // console.log(resultArray)

                    //     //             // 创建一个核密度估计器
                    //     //             const density = d3.contourDensity()
                    //     //                 .x(d => d[0]) // X 坐标
                    //     //                 .y(d => d[1]) // Y 坐标
                    //     //                 .size([2 * radius, 2 * radius]) // SVG 的尺寸
                    //     //                 .bandwidth(30) // KDE 的带宽
                    //     //                 .thresholds(100)
                    //     //                 .cellSize(1)
                    //     //                 (points);

                    //     //             // console.log(density)
                    //     //             // 创建一个颜色映射器
                    //     //             const color3 = d3.scaleSequential(d3.interpolateBlues)
                    //     //                 .domain([0, d3.max(density, d => d.value)]);

                    //     //             // density.thresholds(d3.range(0, d3.max(density, d => d.value), 0.0005)) // 定义等高线的阈值
                    //     //             // 在 SVG 中绘制密度图，并将其限制在圆形区域内
                    //     //             svg.append("defs")
                    //     //                 .append("clipPath")
                    //     //                 .attr("id", "circle-clip")
                    //     //                 .append("circle")
                    //     //                 .attr("cx", centerX)
                    //     //                 .attr("cy", centerY)
                    //     //                 .attr("r", radius);

                    //     //             // svg.append("g")
                    //     //             //     .attr("clip-path", "url(#circle-clip)")
                    //     //             //     .selectAll("path")
                    //     //             //     .data(density)
                    //     //             //     .enter().append("path")
                    //     //             //     .attr("d", d3.geoPath())
                    //     //             //     .attr("fill", d => {
                    //     //             //         console.log(d.value);
                    //     //             //         console.log(color3(d.value))
                    //     //             //         return color3(d.value);
                    //     //             //     });

                    //     //             // // 绘制圆形边界
                    //     //             // svg.append("circle")
                    //     //             //     .attr("cx", centerX)
                    //     //             //     .attr("cy", centerY)
                    //     //             //     .attr("r", radius)
                    //     //             //     .attr("class", "circle-border")
                    //     //             // Add dots
                    //     //             // svg.append('g')
                    //     //             //     .selectAll("dot")
                    //     //             //     .data(unlabelProject)
                    //     //             //     .enter()
                    //     //             //     .append("circle")
                    //     //             //     .attr("cx", function (d) {
                    //     //             //         return d.x;
                    //     //             //     })
                    //     //             //     .attr("cy", function (d) {
                    //     //             //         return d.y;
                    //     //             //     })
                    //     //             //     .attr("r", 1.5)
                    //     //             //     .style("fill", "#69b3a2")

                    //     //         })
                    //     //         .catch(error => {
                    //     //             console.error("Request failed:", error);
                    //     //         });
                    //     // }

                    // });
                    simulation.alpha(1).restart();
                })

                .catch(error => {
                    console.error('Error fetching data samples:', error);
                });

        },

        drawConvex(tubao_pos_data, color) {
            // 传入坐标的数组
            if (tubao_pos_data.length > 2) {
                var hull = d3.polygonHull(tubao_pos_data);
                // 创建绘制凸包的路径
                var path = d3.line()
                    .x(function (d) {
                        return d[0];
                    })
                    .y(function (d) {
                        return d[1];
                    })
                    .curve(d3.curveLinearClosed); // 闭合路径

                // 绘制凸包的路径
                const svg = d3.select("#radviz")
                    .insert("path", ":first-child") // 将路径插入到第一个子元素之前
                    .datum(hull) // 凸包数据
                    .attr("d", path) // 绘制路径
                    .style("fill", color[0])
                    .style("stroke", color[1]) // 边框颜色
                    .style("stroke-dasharray", "15,15") // 虚线样式，5像素实线，5像素空白
                    .style("stroke-width", 3) // 边框宽度
                    .style("fill-opacity", 0.7)
                    .attr("transform", "translate(300,300)")
                    .attr("class", "onehull")
            } else {
                // 绘制直线连接两个点
                const svg = d3.select("#radviz").append("line")
                    .attr("x1", tubao_pos_data[0][0])
                    .attr("y1", tubao_pos_data[0][1])
                    .attr("x2", tubao_pos_data[1][0])
                    .attr("y2", tubao_pos_data[1][1])
                    .attr("stroke", "#50aee8")
                    .attr("stroke-width", 3)
                    .attr("transform", "translate(300,300)")
                    .attr("class", "onehull");
            }
        }

    }
};
</script>

<style>
/* 样式可以根据需求进行调整 */
.myCard5 .ivu-card-body {
    height: 756px;
}

.circle-border {
    fill: none;
    /* stroke: black; */
    /* stroke-width: 2px; */
}

.tooltip {
    position: absolute;
    z-index: 10;
    padding: 10px;
    background: rgb(255, 255, 255);
    border: 1px solid;
    border-radius: 5px;
    border-radius: 5px;
    pointer-events: none;
}

.matrix {
    display: inline-block;
    width: 450px;
    height: 100%;
    vertical-align: top;
}

.radviz {
    display: inline-block;
    vertical-align: top;
}

.node {
    fill: steelblue;
    stroke: #fff;
    stroke-width: 1.5px;
}

.sample {
    fill: red;
    stroke: #fff;
    stroke-width: 1.5px;
}
</style>
