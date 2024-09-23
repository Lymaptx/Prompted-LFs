<template>
  <div>
    <Card class="myCard" >
      <p slot="title">End Model Performance</p>
      <div id="compare_container" style="height: 280px"></div>
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
      // this.save_data_list.push(saveData);
      // this.drawCompare(this.save_data_list);
    },
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