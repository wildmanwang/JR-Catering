<script setup lang="ts">
import { ElButton, ComponentSize } from 'element-plus'
import { PropType, Component, computed } from 'vue'
const props = defineProps({
  stype: {
    type: String,
    required: true,
    validator: (value) => {
        const validValues = ['new', 'modify', 'delete', 'save', 'copy', 'batch', 'query', 'select', 'refresh', 'ok', 'cancel', 'import', 'export', 'print', 'setting', 'return', 'normal']
        const isValid = validValues.includes(value.toLowerCase())
        if (!isValid) {
          throw new Error(`ButtonPre组件stype属性值${value}无效，应取以下值之一：${validValues.join(',')}`)
        }
        return true
    }
  },
  size: {
    type: String as PropType<ComponentSize>,
    default: undefined
  },
  disabled: {
    type: Boolean,
    default: false
  },
  plain: {
    type: Boolean,
    default: false
  },
  text: {
    type: Boolean,
    default: false
  },
  bg: {
    type: Boolean,
    default: false
  },
  link: {
    type: Boolean,
    default: false
  },
  round: {
    type: Boolean,
    default: false
  },
  circle: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  loadingIcon: {
    type: [String, Object] as PropType<String | Component>,
    default: undefined
  },
  icon: {
    type: [String, Object] as PropType<String | Component>,
    default: undefined
  },
  autofocus: {
    type: Boolean,
    default: false
  },
  nativeType: {
    type: String as PropType<'button' | 'submit' | 'reset'>,
    default: 'button'
  },
  autoInsertSpace: {
    type: Boolean,
    default: false
  },
  darker: {
    type: Boolean,
    default: false
  },
  tag: {
    type: [String, Object] as PropType<String | Component>,
    default: 'button'
  }
})
const emits = defineEmits(['click'])
const btnMap = {
    "new": ["新增", new URL("@/assets/svgs/btn/btn-new.svg", import.meta.url).href, 'rgb(99, 161, 3)', 'rgb(255, 255, 255)', '1px solid rgb(99, 161, 3)'],
    "modify": ["修改", new URL("@/assets/svgs/btn/btn-modify.svg", import.meta.url).href, 'rgb(2, 125, 180)', 'rgb(255, 255, 255)', '1px solid rgb(2, 125, 180)'],
    "delete": ["删除", new URL("@/assets/svgs/btn/btn-delete.svg", import.meta.url).href, 'rgb(217, 0, 27)', 'rgb(255, 255, 255)', '1px solid rgb(217, 0, 27)'],
    "save": ["保存", new URL("@/assets/svgs/btn/btn-save.svg", import.meta.url).href, 'rgb(245, 154, 35)', 'rgb(255, 255, 255)', '1px solid rgb(245, 154, 35)'],
    "copy": ["复制", new URL("@/assets/svgs/btn/btn-copy.svg", import.meta.url).href, 'rgb(1, 111, 160)', 'rgb(255, 255, 255)', '1px solid rgb(1, 111, 160)'],
    "batch": ["批量", new URL("@/assets/svgs/btn/btn-batch.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "ok": ["确定", new URL("@/assets/svgs/btn/btn-ok.svg", import.meta.url).href, 'rgb(2, 125, 180)', 'rgb(255, 255, 255)', '1px solid rgb(2, 125, 180)'],
    "cancel": ["取消", new URL("@/assets/svgs/btn/btn-cancel.svg", import.meta.url).href, 'rgb(167, 167, 167)', 'rgb(255, 255, 255)', '1px solid rgb(167, 167, 167)'],
    "query": ["查询", new URL("@/assets/svgs/btn/btn-query.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "select": ["选择", new URL("@/assets/svgs/btn/btn-select.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "refresh": ["刷新", new URL("@/assets/svgs/btn/btn-refresh.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "import": ["导入", new URL("@/assets/svgs/btn/btn-import.svg", import.meta.url).href, 'rgb(1, 111, 160)', 'rgb(255, 255, 255)', '1px solid rgb(1, 111, 160)'],
    "export": ["导出", new URL("@/assets/svgs/btn/btn-export.svg", import.meta.url).href, 'rgb(1, 111, 150)', 'rgb(255, 255, 255)', '1px solid rgb(1, 111, 150)'],
    "print": ["打印", new URL("@/assets/svgs/btn/btn-print.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "setting": ["设置", new URL("@/assets/svgs/btn/btn-setting.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "return": ["返回", new URL("@/assets/svgs/btn/btn-return.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)'],
    "normal": ["", new URL("@/assets/svgs/btn/btn-normal.svg", import.meta.url).href, 'rgb(255, 255, 255)', 'rgb(67, 67, 67)', '1px solid rgb(221, 221, 221)']
}
const btnTxt = computed(() => btnMap[props.stype.toLowerCase()][0])
const btnimg = computed(() => btnMap[props.stype.toLowerCase()][1])
const btnbgclr = computed(() => btnMap[props.stype.toLowerCase()][2])
const btnclr = computed(() => btnMap[props.stype.toLowerCase()][3])
const btnbdr = computed(() => btnMap[props.stype.toLowerCase()][4])

const btnStyle = computed(() => ({
    backgroundColor: btnbgclr.value,
    color: btnclr.value,
    border: btnbdr.value
}))

</script>

<template>
  <ElButton
    class="my-button"
    v-bind="{ ...props }"
    :style="btnStyle"
    @click="() => emits('click')"
  >
    <img class="my-img" :src="btnimg" />
    <span>{{ btnTxt }}</span>
    <slot></slot>
    <slot name="loading"></slot>
  </ElButton>
</template>

<style scoped>
.my-button {
  padding: 1rem 1.2rem 1rem 0.8rem;
  align-items: center;
}
.my-img {
  width: 1.1rem;
  height: 1.1rem;
  object-fit: contain;
  margin-right: 0.3rem;
}
</style>
