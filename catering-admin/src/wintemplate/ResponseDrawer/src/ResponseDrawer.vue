<!--
  ResponseDrawer - 抽屉模板弹窗
  
  功能：提供标准化的抽屉弹窗模板，参考 BaseFree 布局
  特点：
  - 抽屉宽度与 BaseFree 一致
  - 顶部工具栏：左侧 PromptInfo，右侧返回按钮，中间可配置其他按钮
  - 分割线：深灰色横线，上下各 10px 间距
  - 内容区：宽度同工具栏，高度 flex，深灰色边框
-->
<script setup lang="tsx">
import { computed, ref, watch, nextTick, onMounted } from 'vue'
import { ElDrawer, ElScrollbar } from 'element-plus'
import { ButtonPlus } from '@/components/ButtonPlus'

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
  /** 关闭前的回调（返回 false 或 Promise<false> 可阻止关闭） */
  beforeClose?: (done: () => void) => void | Promise<void>
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
  if (props.beforeClose) {
    // 如果有 beforeClose，调用它
    props.beforeClose(() => {
      drawerVisible.value = false
      emit('close')
      emit('cancel')
    })
  } else {
    // 没有 beforeClose，直接关闭
    drawerVisible.value = false
    emit('close')
    emit('cancel')
  }
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

/** 内容区引用 */
const contentRef = ref<HTMLElement>()

/** 分割线引用 */
const dividerRef = ref<HTMLElement>()

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

/**
 * 计算并设置内容区高度
 * 高度 = 窗口高度 - 分割线y坐标 - 20px
 */
const calculateContentHeight = () => {
  nextTick(() => {
    if (!contentRef.value || !dividerRef.value) {
      return
    }
    
    const windowHeight = window.innerHeight
    const dividerRect = dividerRef.value.getBoundingClientRect()
    const dividerY = dividerRect.top + dividerRect.height
    const contentHeight = windowHeight - dividerY - 20
    
    if (contentHeight > 0) {
      contentRef.value.style.height = `${contentHeight}px`
    }
  })
}

// ==================== 暴露方法 ====================
defineExpose({})

// ==================== 监听和生命周期 ====================
/** 监听抽屉显示状态，当打开时强制设置 padding 和内容区高度 */
watch(drawerVisible, (visible) => {
  if (visible) {
    // 使用 nextTick 和 setTimeout 确保 DOM 完全渲染后设置
    nextTick(() => {
      forceSetDrawerBodyPadding()
      calculateContentHeight()
      // 延迟设置，确保 Element Plus 的动画完成
      setTimeout(() => {
        forceSetDrawerBodyPadding()
        calculateContentHeight()
      }, 100)
      // 再次延迟，确保动画完全完成
      setTimeout(() => {
        calculateContentHeight()
      }, 300)
    })
  }
})

onMounted(() => {
  if (drawerVisible.value) {
    forceSetDrawerBodyPadding()
    calculateContentHeight()
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
    :before-close="props.beforeClose"
    destroy-on-close
    class="response-drawer"
    @opened="() => { forceSetDrawerBodyPadding(); calculateContentHeight(); }"
  >
    <!-- 顶部工具栏 -->
    <div class="response-drawer-toolbar">
      <!-- 工具栏左侧：空（由子组件填充） -->
      <div class="toolbar-left">
        <slot name="toolbar-left"></slot>
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
    <div ref="dividerRef" class="response-drawer-divider"></div>

    <!-- 内容区 -->
    <div ref="contentRef" class="response-drawer-content">
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
  width: 800px;
  max-width: 800px;
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
  width: 800px;
  max-width: 800px;
  margin: 0;
  padding: 0;
  border: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative; /* 为绝对定位的子元素提供定位上下文 */

  .content-scrollbar {
    position: absolute; /* 绝对定位，确保占据整个内容区 */
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    overflow: hidden;

    :deep(.el-scrollbar__wrap) {
      overflow-x: hidden;
      overflow-y: auto; /* 确保纵向滚动 */
      height: 100%; /* 确保滚动容器高度正确 */
    }

    :deep(.el-scrollbar__view) {
      /* 让内容自然高度，不需要设置 height */
    }

    .content-inner {
      padding: 10px 0 0 20px;
      box-sizing: border-box;
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
  :deep(.el-drawer) {
    overflow: hidden !important; /* 防止整个 drawer 滚动 */
    display: flex !important;
    flex-direction: column !important;
  }
  
  :deep(.el-drawer__container) {
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100vh !important; /* 确保容器高度为视口高度 */
  }

  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 15px 20px;
    border-bottom: 1px solid var(--el-border-color);
    flex-shrink: 0; /* 防止 header 被压缩 */
  }

  :deep(.el-drawer__body) {
    padding: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    flex: 1 !important; /* 占据剩余空间 */
    min-height: 0 !important; /* 允许缩小 */
    box-sizing: border-box;
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

