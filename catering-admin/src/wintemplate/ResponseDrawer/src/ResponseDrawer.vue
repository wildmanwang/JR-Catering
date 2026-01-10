<!--
  ResponseDrawer - 抽屉模板弹窗
  
  功能：提供标准化的抽屉弹窗模板，参考 BaseFree 布局
  特点：
  - 抽屉宽度与 BaseFree 一致
  - 顶部工具栏：左侧 PrompInfo，右侧返回按钮，中间可配置其他按钮
  - 分割线：深灰色横线，上下各 10px 间距
  - 内容区：宽度同工具栏，高度 flex，深灰色边框
-->
<script setup lang="tsx">
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import { ElDrawer, ElScrollbar } from 'element-plus'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PrompInfo } from '@/components/PrompInfo'

defineOptions({
  name: 'ResponseDrawer'
})

// ==================== 类型定义 ====================
/**
 * 工具栏按钮配置
 */
export interface ToolbarButton {
  /** 按钮类型（ButtonPlus 的 stype） */
  stype: string
  /** 按钮文本（可选，如果提供则覆盖 stype 默认文本） */
  label?: string
  /** 按钮加载状态 */
  loading?: boolean
  /** 是否显示 */
  show?: boolean
  /** 点击事件处理函数 */
  onClick?: () => void | Promise<void>
}

/**
 * 组件 Props
 */
interface Props {
  /** 抽屉显示状态 */
  modelValue: boolean
  /** 抽屉标题 */
  title?: string
  /** 抽屉宽度（默认与 BaseFree 一致） */
  width?: string | number
  /** 点击遮罩是否关闭 */
  closeOnClickModal?: boolean
  /** 工具栏按钮配置（返回按钮左侧的其他按钮） */
  toolbarButtons?: ToolbarButton[]
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  width: 'max(700px, calc(100vw - 600px))',
  closeOnClickModal: true,
  toolbarButtons: () => []
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'close': []
  'cancel': []
}>()

// ==================== 计算属性 ====================
/** 抽屉显示状态 */
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  }
})

/** 抽屉宽度 */
const drawerWidth = computed(() => {
  if (typeof props.width === 'string' && props.width.includes('calc')) {
    return props.width
  }
  return props.width
})

/** 过滤后的工具栏按钮（只显示 show !== false 的按钮） */
const visibleToolbarButtons = computed(() => {
  return props.toolbarButtons.filter(btn => btn.show !== false)
})

// ==================== 事件处理 ====================
/**
 * 处理返回按钮点击
 */
const handleReturn = () => {
  drawerVisible.value = false
  emit('close')
  emit('cancel')
}

/**
 * 处理工具栏按钮点击
 */
const handleToolbarButtonClick = async (btn: ToolbarButton) => {
  if (btn.onClick) {
    await btn.onClick()
  }
}

// ==================== 强制设置 el-drawer__body 的 padding ====================
/** ElDrawer 组件引用 */
const drawerRef = ref<InstanceType<typeof ElDrawer>>()

/**
 * 强制设置 el-drawer__body 的 padding 为 0
 * 通过查找所有 .el-drawer__body，然后检查其内部是否有 response-drawer-toolbar 类
 */
const forceSetDrawerBodyPadding = () => {
  nextTick(() => {
    const allDrawerBodies = document.querySelectorAll('.el-drawer__body')
    for (const body of Array.from(allDrawerBodies)) {
      const bodyEl = body as HTMLElement
      // 检查 el-drawer__body 内部是否包含我们的工具栏组件
      if (bodyEl.querySelector('.response-drawer-toolbar')) {
        setPaddingZero(bodyEl)
        break
      }
    }
  })
}

/**
 * 设置元素的 padding 为 0
 */
const setPaddingZero = (element: HTMLElement) => {
  if (element) {
    element.style.setProperty('padding', '0', 'important')
  }
}

// ==================== 暴露方法 ====================
/** PrompInfo 组件引用 */
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()

defineExpose({
  /** 显示信息提示 */
  showInfo: (type?: 'info' | 'warn' | 'error' | null, message?: string | null) => {
    if (!type || !message) {
      prompInfoRef.value?.ready()
      return
    }
    if (type === 'info') {
      prompInfoRef.value?.info(message)
    } else if (type === 'warn') {
      prompInfoRef.value?.warn(message)
    } else if (type === 'error') {
      prompInfoRef.value?.err(message)
    }
  },
  /** 获取 PrompInfo 组件引用 */
  getPrompInfoRef: () => prompInfoRef.value
})

// ==================== 监听和生命周期 ====================
/** 监听抽屉显示状态，当打开时强制设置 padding */
watch(drawerVisible, (visible) => {
  if (visible) {
    // 使用 nextTick 和 setTimeout 确保 DOM 完全渲染后设置
    nextTick(() => {
      forceSetDrawerBodyPadding()
      // 延迟设置，确保 Element Plus 的动画完成
      setTimeout(() => {
        forceSetDrawerBodyPadding()
      }, 100)
    })
  }
})

onMounted(() => {
  if (drawerVisible.value) {
    forceSetDrawerBodyPadding()
  }
})
</script>

<template>
  <ElDrawer
    ref="drawerRef"
    v-model="drawerVisible"
    :size="drawerWidth"
    direction="rtl"
    :close-on-click-modal="props.closeOnClickModal"
    :with-header="true"
    :title="props.title || ''"
    destroy-on-close
    class="response-drawer"
    @opened="forceSetDrawerBodyPadding"
  >
    <!-- 顶部工具栏 -->
    <div class="response-drawer-toolbar">
      <!-- 工具栏左侧：PrompInfo 组件 -->
      <div class="toolbar-left">
        <PrompInfo ref="prompInfoRef" />
      </div>

      <!-- 工具栏右侧：其他按钮 + 返回按钮 -->
      <div class="toolbar-right">
        <!-- 可配置的其他功能按钮 -->
        <template v-for="(btn, index) in visibleToolbarButtons" :key="index">
          <ButtonPlus
            :stype="btn.stype"
            :loading="btn.loading"
            @click="handleToolbarButtonClick(btn)"
          >
            <template v-if="btn.label">{{ btn.label }}</template>
          </ButtonPlus>
        </template>

        <!-- 返回按钮 -->
        <ButtonPlus stype="return" @click="handleReturn" />
      </div>
    </div>

    <!-- 分割线：直接放在抽屉下一级，贯穿左右 -->
    <div class="response-drawer-divider"></div>

    <!-- 内容区 -->
    <div class="response-drawer-content">
      <ElScrollbar class="content-scrollbar">
        <div class="content-inner">
          <!-- 默认插槽：内容区内容 -->
          <slot></slot>
        </div>
      </ElScrollbar>
    </div>
  </ElDrawer>
</template>

<style lang="less" scoped>
/* 顶部工具栏 */
.response-drawer-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 760px;
  max-width: 760px;
  margin: 0;
  padding: 0;
  padding-top: 0;
  padding-bottom: 0;
  min-height: 60px;
  flex-shrink: 0;

  .toolbar-left {
    flex: 1;
    min-width: 0;
    display: flex;
  }

  .toolbar-right {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
}

/* 分割线：直接放在抽屉下一级，贯穿左右 */
.response-drawer-divider {
  width: 100%;
  height: 1px;
  background-color: #d3d4d6; /* 深灰色 */
  margin: 0 0 0 0;
  flex-shrink: 0;
}

/* 内容区 */
.response-drawer-content {
  flex: 1;
  min-height: 0;
  width: 760px;
  max-width: 760px;
  margin: 0;
  padding: 0 20px 20px 20px;
  border: 1px solid #d3d4d6; /* 深灰色边框 */
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .content-scrollbar {
    flex: 1;
    min-height: 0;

    :deep(.el-scrollbar__wrap) {
      overflow-x: hidden;
    }

    .content-inner {
      padding: 20px 0;
      min-height: 100%;
    }
  }
}

</style>

<style lang="less">
/* 抽屉宽度样式（与 BaseFree 一致，使用非 scoped 样式确保生效） */
:deep(.response-drawer) {
  .el-drawer {
    width: max(700px, calc(100vw - 600px)) !important;
    right: 0 !important;
    left: auto !important;
  }
}

/* 抽屉样式（参考 BaseFree 的实现方式） */
.response-drawer {
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 15px 20px;
    border-bottom: 1px solid var(--el-border-color);
  }

  :deep(.el-drawer__body) {
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
  }

  :deep(.el-drawer__body > .response-drawer-divider) {
    width: 100% !important;
    position: relative;
    left: 0;
    right: 0;
    margin-left: 0;
    margin-right: 0;
  }
}

</style>

