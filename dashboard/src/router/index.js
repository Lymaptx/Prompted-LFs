import Vue from 'vue';
import Router from 'vue-router';

// 导入六个不同的视图组件
import View1 from '@/components/View1.vue';
import View2 from '@/components/View2.vue';
import View3 from '@/components/View3.vue';
import View4 from '@/components/View4.vue';
import View5 from '@/components/View5.vue';
import View6 from '@/components/View6.vue';

Vue.use(Router);

export default new Router({
  routes: [
    {
      path: '/',
      components: {
        // 上半部分视图
        top1: View1,
        top2: View2,
        top3: View3,
        // 下半部分视图
        bottom: View4,
        bottom2: View5,
        bottom3: View6,
      },
    },
  ],
});