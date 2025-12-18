<!--
  StatusStoragePlus - 页面状态存储组件
  
  功能：
  1. 窗口切换走时，保存窗口的各组件的状态
  2. 窗口切换回时，加载窗口的各组件的状态
  3. 窗口关闭时，清空窗口的各组件状态的数据
  
  使用示例：
  StatusStoragePlus 组件包裹页面内容，通过 stores 属性配置要保存的状态
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { useTagsViewStoreWithOut } from '@/store/modules/tagsView'

/**
 * 状态存储配置项
 */
export interface StatusStoreItem {
  /** 状态名称（用于标识不同的状态） */
  name: string
  /** 获取状态的函数，返回要保存的状态数据 */
  getState: () => any
  /** 设置状态的函数，接收保存的状态数据 */
  setState: (state: any) => void | Promise<void>
}

/**
 * 组件 Props 接口
 */
export interface StatusStoragePlusProps {
  /** 状态存储配置数组 */
  stores: StatusStoreItem[]
  /** 状态存储的前缀（可选，默认：STATUS_STORAGE_） */
  storagePrefix?: string
  /** 状态数据的最大保存时间（毫秒，默认：24小时） */
  maxAge?: number
  /** 是否启用自动保存（默认：true，在路由离开时自动保存） */
  autoSave?: boolean
  /** 自动保存的防抖延迟（毫秒，默认：500ms，仅在路由离开时保存，不使用防抖） */
  autoSaveDelay?: number
}

const props = withDefaults(defineProps<StatusStoragePlusProps>(), {
  storagePrefix: 'STATUS_STORAGE_',
  maxAge: 24 * 60 * 60 * 1000, // 24小时
  autoSave: true,
  autoSaveDelay: 500
})

const router = useRouter()
const tagsViewStore = useTagsViewStoreWithOut()

const PAGE_STATE_KEY = computed(() => `${props.storagePrefix}${router.currentRoute.value.fullPath}`)
const PAGE_RESTORE_FLAG_KEY = computed(() => `RESTORE_FLAG_${router.currentRoute.value.fullPath}`)

const pageReady = ref(false)
const isRestoring = ref(false)
let saveStateTimer: NodeJS.Timeout | null = null
let mountedRoutePath: string | null = null
let mountedRouteFullPath: string | null = null

/**
 * 深拷贝数据
 */
const deepClone = (obj: any): any => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (Array.isArray(obj)) {
    return obj.map(item => deepClone(item))
  }
  const cloned: any = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key])
    }
  }
  return cloned
}

/**
 * 保存页面状态到 localStorage
 */
const savePageState = async () => {
  if (!pageReady.value || isRestoring.value) return
  if (props.stores.length === 0) return
  
  try {
    const state: Record<string, any> = {}
    
    // 收集所有配置的状态
    for (const store of props.stores) {
      try {
        const stateData = store.getState()
        state[store.name] = deepClone(stateData)
      } catch (err) {
        console.error(`保存状态 ${store.name} 失败：`, err)
      }
    }
    
    const statePayload = {
      state,
      timestamp: Date.now(),
      fullPath: router.currentRoute.value.fullPath
    }
    
    localStorage.setItem(PAGE_STATE_KEY.value, JSON.stringify(statePayload))
  } catch (err) {
    console.error('保存页面状态失败：', err)
  }
}

/**
 * 从 localStorage 恢复页面状态
 */
const restorePageState = async (): Promise<boolean> => {
  try {
    const savedState = localStorage.getItem(PAGE_STATE_KEY.value)
    if (!savedState) {
      return false
    }
    
    const statePayload = JSON.parse(savedState)
    
    // 检查时间戳是否过期
    const now = Date.now()
    const elapsed = now - statePayload.timestamp
    if (elapsed > props.maxAge) {
      localStorage.removeItem(PAGE_STATE_KEY.value)
      return false
    }
    
    // 验证 fullPath 是否匹配
    if (statePayload.fullPath !== router.currentRoute.value.fullPath) {
      return false
    }
    
    isRestoring.value = true
    
    // 恢复所有配置的状态
    const state = statePayload.state || {}
    for (const store of props.stores) {
      try {
        if (state[store.name] !== undefined) {
          await store.setState(state[store.name])
        }
      } catch (err) {
        console.error(`恢复状态 ${store.name} 失败：`, err)
      }
    }
    
    // 等待状态更新完成
    await nextTick()
    isRestoring.value = false
    
    return true
  } catch (err) {
    console.error('恢复页面状态失败：', err)
    isRestoring.value = false
    return false
  }
}

/**
 * 清空页面状态
 */
const clearPageState = (stateKey?: string, fullPath?: string) => {
  const keyToRemove = stateKey || PAGE_STATE_KEY.value
  const pathToCheck = fullPath || router.currentRoute.value.fullPath
  
  try {
    const savedState = localStorage.getItem(keyToRemove)
    if (savedState) {
      const state = JSON.parse(savedState)
      if (state.fullPath === pathToCheck) {
        localStorage.removeItem(keyToRemove)
      }
    }
    
    // 同时清除恢复标记
    const flagKey = fullPath ? `RESTORE_FLAG_${fullPath}` : PAGE_RESTORE_FLAG_KEY.value
    try {
      sessionStorage.removeItem(flagKey)
    } catch (err) {
      // 静默处理
    }
  } catch (err) {
    console.error('清空页面状态失败：', err)
  }
}

/**
 * 路由守卫：离开页面前保存状态
 */
onBeforeRouteLeave((_to, _from, next) => {
  // 检查是否是关闭页签的操作
  const isClosing = !tagsViewStore.getVisitedViews.some(
    view => view.fullPath === _from.fullPath || view.path === _from.path
  )
  
  if (isClosing) {
    // 页签关闭由 onBeforeUnmount 处理，这里直接允许
    next()
    return
  }
  
  // 如果启用了自动保存，在路由跳转（切换窗口）时保存状态并设置恢复标记
  if (props.autoSave) {
    if (saveStateTimer) {
      clearTimeout(saveStateTimer)
      saveStateTimer = null
    }
    savePageState()
    
    // 设置恢复标记，表示该路由有保存的状态，可以恢复
    try {
      sessionStorage.setItem(PAGE_RESTORE_FLAG_KEY.value, '1')
    } catch (err) {
      console.error('设置恢复标记失败：', err)
    }
  }
  
  next()
})

// ==================== 监听路由变化，恢复状态 ====================
// 注意：这个 watch 主要用于检测路由切换回当前页面的情况
// 但在没有 keep-alive 的情况下，组件会重新创建，所以主要逻辑在 onMounted 中
watch(
  () => router.currentRoute.value.fullPath,
  async (newFullPath, oldFullPath) => {
    // 首次挂载时不处理（会由 onMounted 处理）
    if (!pageReady.value) return
    
    // 如果路由没有变化，不处理
    if (newFullPath === oldFullPath) return
    
    // 检查是否是切换到当前路由（这种情况在有 keep-alive 时才会发生）
    if (newFullPath === router.currentRoute.value.fullPath && oldFullPath !== newFullPath) {
      // 切换到当前路由，恢复状态
      await restorePageState()
    }
  }
)

// ==================== 生命周期 ====================
onMounted(async () => {
  mountedRoutePath = router.currentRoute.value.path
  mountedRouteFullPath = router.currentRoute.value.fullPath
  
  // 检查是否是首次打开还是切换回来
  // 通过检查 sessionStorage 中的恢复标记来判断
  let shouldRestore = false
  try {
    const restoreFlag = sessionStorage.getItem(PAGE_RESTORE_FLAG_KEY.value)
    if (restoreFlag === '1') {
      // 有恢复标记，说明是切换回来，应该恢复状态
      shouldRestore = true
      // 清除标记，避免下次误判
      sessionStorage.removeItem(PAGE_RESTORE_FLAG_KEY.value)
    }
  } catch (err) {
    console.error('检查恢复标记失败：', err)
  }
  
  await nextTick()
  pageReady.value = true
  
  // 只有切换回来时才恢复状态，首次打开不恢复
  if (shouldRestore) {
    await restorePageState()
  }
})

onBeforeUnmount(() => {
  if (saveStateTimer) {
    clearTimeout(saveStateTimer)
    saveStateTimer = null
  }
  
  // 检查窗口是否真正关闭
  const checkAndClear = () => {
    const fullPathToCheck = mountedRouteFullPath || router.currentRoute.value.fullPath
    const visitedViews = tagsViewStore.getVisitedViews
    const pathToCheck = mountedRoutePath || router.currentRoute.value.path
    const isStillOpen = visitedViews.some(view => view.path === pathToCheck)
    
    if (!isStillOpen) {
      const stateKey = `${props.storagePrefix}${fullPathToCheck}`
      clearPageState(stateKey, fullPathToCheck)
      return true
    } else {
      return false
    }
  }
  
  // 延迟检查，确保页签状态已更新
  nextTick(() => {
    setTimeout(() => {
      if (checkAndClear()) return
      
      setTimeout(() => {
        checkAndClear()
      }, 150)
    }, 50)
  })
})

// ==================== 暴露方法 ====================
defineExpose({
  /** 手动保存状态 */
  saveState: savePageState,
  /** 手动恢复状态 */
  restoreState: restorePageState,
  /** 手动清空状态 */
  clearState: () => clearPageState()
})
</script>

<template>
  <div class="status-storage-plus">
    <slot></slot>
  </div>
</template>

<style lang="less" scoped>
.status-storage-plus {
  width: 100%;
  height: 100%;
}
</style>

