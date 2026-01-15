<!--
  WinSheet - 窗口模板组件
  
  功能：
  - 提供标准化的窗口模板，统一处理窗口打开、切换、关闭的缓存逻辑
  - 使用 StatusStoragePlus 组件集中管理状态缓存
  - 子组件通过插槽放入，无需自己处理缓存逻辑
  
  使用方式：
  <WinSheet :window-id="'MyWindow'" :stores="stores">
    <YourComponent />
  </WinSheet>
-->
<script setup lang="ts">
import { ref, computed } from 'vue'
import { StatusStoragePlus, type StatusStoreItem } from '@/components/StatusStoragePlus'
import { ContentWrap } from '@/components/ContentWrap'

/**
 * 组件 Props 接口
 */
export interface WinSheetProps {
  /** 窗口标识（用于 StatusStoragePlus 的唯一标识，必须提供） */
  windowId: string
  /** 状态存储配置数组（传递给 StatusStoragePlus） */
  stores?: StatusStoreItem[]
  /** 状态存储的前缀（可选，默认：使用 windowId） */
  storagePrefix?: string
  /** 是否启用自动保存（默认：true） */
  autoSave?: boolean
  /** 状态恢复完成后的回调函数 */
  onRestoreComplete?: (restored: boolean) => void | Promise<void>
}

const props = withDefaults(defineProps<WinSheetProps>(), {
  stores: () => [],
  storagePrefix: undefined,
  autoSave: true
})

// ==================== StatusStoragePlus 引用 ====================
const statusStoragePlusRef = ref<InstanceType<typeof StatusStoragePlus>>()

// ==================== 计算属性 ====================
/**
 * 计算存储前缀
 * 如果提供了 storagePrefix，则使用它；否则使用 windowId 生成默认前缀
 */
const computedStoragePrefix = computed(() => {
  return props.storagePrefix || `${props.windowId}_STATE_`
})

// ==================== 暴露方法 ====================
defineExpose({
  /** 手动保存状态 */
  saveState: () => statusStoragePlusRef.value?.saveState(),
  /** 手动恢复状态 */
  restoreState: () => statusStoragePlusRef.value?.restoreState(),
  /** 手动清空状态 */
  clearState: () => statusStoragePlusRef.value?.clearState(),
  /** 获取状态恢复完成的 Promise */
  waitForRestore: () => statusStoragePlusRef.value?.waitForRestore() || Promise.resolve(false),
  /** 获取 StatusStoragePlus 组件引用 */
  getStatusStoragePlusRef: () => statusStoragePlusRef.value
})
</script>

<template>
  <ContentWrap>
    <StatusStoragePlus
      ref="statusStoragePlusRef"
      :stores="stores"
      :storage-prefix="computedStoragePrefix"
      :auto-save="autoSave"
      :on-restore-complete="onRestoreComplete"
    >
      <slot></slot>
    </StatusStoragePlus>
  </ContentWrap>
</template>

<style lang="less" scoped>
/**
 * WinSheet 容器样式
 * 确保子组件能够正确填充容器，实现全屏布局
 */
:deep(.content-wrap),
:deep(.content-wrap .el-card),
:deep(.content-wrap .el-card__body) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
  margin: 0 !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  min-height: 0 !important;
  overflow: hidden !important;
  padding: 0 !important;
}

:deep(.content-wrap > div) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  padding: 0 !important;
  margin: 0 !important;
}
</style>
