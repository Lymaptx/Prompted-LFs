<template>
<div>
    <!--上半部分 -->
    <Row>
        <i-col class="mycol" span="5">
            <view1></view1>
        </i-col>

        <i-col class="mycol" span="19">
            <view3></view3>
        </i-col>

    </Row>
    <!-- 下半部分 -->
    <!-- 上半部分 -->
    <Row>
        <i-col class="mycol" span="5">
            <view2></view2>
        </i-col>
        <i-col class="mycol" span="5">
            <view4></view4>
            
        </i-col>
        <i-col class="mycol" span="14">
            <view5></view5>
        </i-col>
    </Row>

</div>
</template>

<script>
import view1 from './components/View1.vue'
import view2 from './components/View2.vue'
import view3 from './components/View3.vue'
import view4 from './components/View4.vue'
import view5 from './components/View5.vue'
import view6 from './components/View6.vue'
import view7 from './components/View7.vue'

export default {
    name: 'App',
    components: {
        view1,
        view2,
        view3,
        view4,
        view5,
        view6,
        view7
    }
}
</script>

<style>
.top {
    display: flex;
    justify-content: space-between;
}

.bottom {
    display: flex;
    justify-content: space-between;
}

.myCard {
    height: auto;
    margin: 3px;
}

.ivu-card-bordered {
    border: 2px solid #dcdee2;
    border-color: #e8eaec;
}

.ivu-card-head p {
    text-align: left;
    font-size: 18px;
    color: white;
}

.ivu-card-body {
    padding: 10px;
}

.ivu-card-head {
    line-height: 3;
    padding: 0px 16px;
    height: 32px;
    background-color: #606060;
}

.ivu-input-small {
    height: 20px;
}

.ivu-collapse-content>.ivu-collapse-content-box {
    padding-bottom: 0px;
}

.ivu-collapse-content {
    padding: 0px 8px;
}

body {
    line-height: 1.5;
}

::-webkit-scrollbar {
    -webkit-appearance: none;
    width: 6px;
    height: 6px;
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
</style>
