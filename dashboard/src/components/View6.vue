<template>
  <div>
    <Card class="myCard" style="height: 316px;">
      <p slot="title">Label Function Adujstment</p>
      <div id="compare_container"></div>
    </Card>
  </div>
</template>

<script>
import * as d3 from 'd3';
import axios from 'axios';
import { EventBus } from '../EventBus';
import { globalState } from '@/main.js'; // 引入全局变量
export default {
  data() {
    return {
      save_data_list: [],
      base_url: "http://127.0.0.1:5000"
    };
  },
  mounted() {
    EventBus.$on('save-parameter', this.handleSaveparameter);
  },
  beforeDestroy() {
    // 在组件销毁前解绑事件
    EventBus.$off('save-parameter', this.handleSaveparameter);
  },
  methods: {
    handleSaveparameter(saveData) {
      this.save_data_list.push(saveData);
      this.drawCompare(this.save_data_list);
    },
    drawCompare(data) {
      $('#compare_container').empty();

      console.log("view6保存结果快照视图：", data);

      const width = d3.select("#compare_container")._groups[0][0].clientWidth;
      const height = d3.select("#compare_container")._groups[0][0].clientHeight;

      const svg = d3.select('#compare_container')
        .append("svg")
        .attr('id', 'snapshotInfo')
        .attr('width', width);

      var temp_height = data.length * 130;
      let containerA = document.getElementById("snapshotInfo").setAttribute('height', d3.max([temp_height, height]) + 'px');

      const round_height = 156;
      const margin = { top: 20, right: 20, bottom: 30, left: 41 };

      const g = svg.append("g")
        .attr("id", "maingroup")
        .attr('transform', `translate(${margin.left},${margin.top})`);

      // 柱状图的比例尺
      const bar_width = 80;
      const scaleError = d3.scaleLinear()
        .domain([0, 20])
        .range([0, bar_width]);

      const scalePD = d3.scaleLinear()
        .domain([0, 20])
        .range([0, bar_width]);

      data.forEach((item, index) => {
        // 绘制饼图**********************************************
        const colorList = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854'];

        // 设置间隔
        const paddingAngle = 0.4; // 以弧度为单位

        // 创建一个弧生成器
        const arcGenerator = d3.arc();

        // 每个饼图的大小
        const pie_content = 132;
        const radius = 26;

        // 计算每个扇形的半径
        const pie = d3.pie().value(d => d.value);

        const radiusScale = d3.scaleLinear()
          .domain([0, 1])
          .range([0, radius]);

        const numArcs = 4;
        const arcAngle = (2 * Math.PI) / numArcs;


        var Piedata = pie(item.piedata);
        var g = svg.append("g")
          .attr("transform", (d, i) => `translate(${40}, ${38 + index * 0.98 * pie_content})`);

        // 背景
        g.append("g")
          .append("rect")
          .attr("x", - margin.left + 2)
          .attr("y", (d, i) => - 35 - index)
          .attr("rx", 10)
          .attr("ry", 10)
          .attr("width", 158)
          .attr("height", pie_content - 10)
          .attr("fill", 'none')
          .attr("stroke", "#BBBAD5")
          .attr("stroke-width", 2);

        Piedata.forEach((d, i) => {
          const startAngle = i * (2 * Math.PI / Piedata.length);
          const endAngle = (i + 1) * (2 * Math.PI / Piedata.length);

          //绘制每个扇区的内部虚线
          for (let j = 0; j < numArcs; j++) {
            g.append("g")
              .append("path")
              .attr("d", arcGenerator({
                startAngle: startAngle,
                endAngle: endAngle,
                innerRadius: 0,
                outerRadius: (j + 1) * radius / numArcs, // 使用相同的半径
                padAngle: paddingAngle // 根据扇形半径进行调整
              }))
              .style("fill", "none")
              .style("stroke", "#C0C0C0")
              .style("stroke-width", 1);

            // 绘制扇区
            g.append("g")
              .selectAll("path")
              .data(Piedata)
              .enter()
              .append("path")
              .attr("d", (d, i) => {
                // 不同的参数使用不同的比例尺
                return arcGenerator({
                  startAngle: i * (2 * Math.PI / Piedata.length),
                  endAngle: (i + 1) * (2 * Math.PI / Piedata.length),
                  innerRadius: 0,
                  outerRadius: radiusScale(d.value),
                  padAngle: paddingAngle
                })
              })
              .style("fill", (d, i) => colorList[i]);
          }
        })
        // 绘制饼图**********************************************


        // 每个组合的名称
        g.append("g")
          .append("text")
          .attr("x", -12)
          .attr("y", 42)
          .text(item.name)
          .attr("font-weight", "bold");

        // 文字竖线
        g.append("g")
          .append("line")
          .attr("x1", pie_content / 3 - 5)
          .attr("y1", -28)
          .attr("x2", pie_content / 3 - 5)
          .attr("y2", 44)
          .attr("fill", "none")
          .attr("stroke", '#C0C0C0')
          .attr("stroke-width", 1);

        // 右侧文字
        g.append("g")
          .selectAll("text")
          .data(Piedata)
          .join('text')
          .attr("x", (d, i) => 54)
          .attr("y", (d, i) => -20 + i * 16)
          .attr("font-size", 12)
          .text(d => d.data.name + ': ' + d.data.value);

        // 柱状图
        g.append("g")
          .append("rect")
          .attr("x", -margin.left + 70)
          .attr("y", (d, i) => 50)
          .attr("width", bar_width)
          .attr("height", 12)
          .attr("rx", 2)
          .attr("ry", 2)
          .attr("fill", "white")
          .attr("stroke", "gray")
          .attr("stroke-width", 1);

        g.append("g")
          .append("rect")
          .attr("x", -margin.left + 70)
          .attr("y", (d, i) => 67)
          .attr("width", bar_width)
          .attr("height", 12)
          .attr("rx", 2)
          .attr("ry", 2)
          .attr("fill", "white")
          .attr("stroke", "gray")
          .attr("stroke-width", 1);

        g.append("g")
          .append("rect")
          .attr("x", -margin.left + 70)
          .attr("y", (d, i) => 50)
          .attr("width", scaleError(item.error))
          .attr("height", 12)
          .attr("rx", 2)
          .attr("ry", 2)
          .attr("fill", "gray");

        g.append("g")
          .append("rect")
          .attr("x", -margin.left + 70)
          .attr("y", (d, i) => 67)
          .attr("width", scalePD(item.pd))
          .attr("height", 12)
          .attr("rx", 2)
          .attr("ry", 2)
          .attr("fill", "gray");

        g.append("g")
          .append('text')
          .attr("x", -5)
          .attr("y", 60)
          .attr("font-size", 12)
          .text('Error');

        g.append("g")
          .append('text')
          .attr("x", -30)
          .attr("y", 75)
          .attr("font-size", 12)
          .text('Sensitivity');


      })

    }
  }
};
</script>

<style>
/* 样式可以根据需求进行调整 */
div#compare_container {
  width: 165px;
  height: 394px;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>