<!--
  StatusStoragePlus - 页面状态存储组件
  
  功能说明：
  1. 窗口切换走时，自动保存各组件的状态到本地存储
  2. 窗口切换回时，自动加载并恢复各组件的状态
  3. 窗口关闭时，自动清空保存的状态数据
  
  使用方式详见组件文档注释
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick, type Ref } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { useTagsViewStoreWithOut } from '@/store/modules/tagsView'

/**
 * 存储适配器接口（支持扩展不同的存储方式）
 */
export interface StorageAdapter {
  /** 获取存储的数据 */
  getItem(key: string): string | null
  /** 设置存储的数据 */
  setItem(key: string, value: string): void
  /** 删除存储的数据 */
  removeItem(key: string): void
}

/**
 * 默认的 localStorage 适配器
 */
const localStorageAdapter: StorageAdapter = {
  getItem: (key: string) => {
    try {
      return localStorage.getItem(key)
    } catch {
      return null
    }
  },
  setItem: (key: string, value: string) => {
    try {
      localStorage.setItem(key, value)
    } catch (err) {
      // 存储数据失败，静默处理
    }
  },
  removeItem: (key: string) => {
    try {
      localStorage.removeItem(key)
    } catch (err) {
      // 删除存储数据失败，静默处理
    }
  }
}

/**
 * 默认的 sessionStorage 适配器
 */
const sessionStorageAdapter: StorageAdapter = {
  getItem: (key: string) => {
    try {
      return sessionStorage.getItem(key)
    } catch {
      return null
    }
  },
  setItem: (key: string, value: string) => {
    try {
      sessionStorage.setItem(key, value)
    } catch (err) {
      // 存储数据失败，静默处理
    }
  },
  removeItem: (key: string) => {
    try {
      sessionStorage.removeItem(key)
    } catch (err) {
      // 删除存储数据失败，静默处理
    }
  }
}

/**
 * 深拷贝工具函数
 */
function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime()) as T
  if (obj instanceof RegExp) return new RegExp(obj) as T
  
  if (Array.isArray(obj)) {
    return obj.map(item => deepClone(item)) as T
  }
  
  const cloned = {} as T
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      cloned[key] = deepClone(obj[key])
    }
  }
  return cloned
}

/**
 * 组件引用配置（用于自动调用组件方法恢复状态）
 * 
 * 使用场景：
 * - 当状态恢复需要调用子组件的方法时（如 QueryBar.setValues）
 * - 可以自动处理组件未就绪的情况，等待组件挂载完成
 */
export interface ComponentRefConfig {
  /** 组件引用（通过 ref 获取） */
  ref: Ref<any>
  /** 恢复方法名（如 'setValues'，会在 ref.value[methodName] 上调用） */
  methodName: string
  /** 
   * 恢复时传递给方法的参数映射函数（可选）
   * 如果不提供，则直接传递完整的 state 数据
   * 
   * 示例：
   * ```ts
   * getRestoreParams: (state) => state.formData // 只传递 formData 字段
   * ```
   */
  getRestoreParams?: (state: any) => any
  /**
   * 是否等待组件准备就绪（可选，默认：true）
   * - true: 使用 nextTick 等待组件挂载完成
   * - false: 立即调用，如果组件未就绪则跳过
   */
  waitForComponentReady?: boolean
}

/**
 * 状态存储配置项
 * 
 * 每个配置项代表一个独立的状态单元，可以是一个简单值、对象或包含多个相关状态的集合。
 * 多个配置项可以组合使用，实现复杂页面的状态管理。
 */
export interface StatusStoreItem {
  /** 
   * 状态名称（用于标识不同的状态，在同一页面中必须唯一）
   * 建议使用有意义的名称，如 'formData', 'tableState', 'queryParams' 等
   */
  name: string
  /** 
   * 获取状态的函数，返回要保存的状态数据
   * 
   * 注意：
   * - 应返回纯数据，避免返回响应式对象
   * - 建议使用 toRaw 或深拷贝来获取原始值
   * - 函数应该是同步的，避免返回 Promise
   * 
   * 示例：
   * ```ts
   * getState: () => ({ 
   *   list: toRaw(dataList.value),
   *   params: toRaw(queryParams.value) 
   * })
   * ```
   */
  getState: () => any
  /** 
   * 设置状态的函数，接收保存的状态数据并恢复状态
   * 
   * 注意：
   * - 可以是同步或异步函数
   * - 在函数内部可以调用组件方法、更新 ref 值等
   * - 如果组件方法恢复已经更新了显示，仍需要在这里更新内部状态变量
   * 
   * 示例：
   * ```ts
   * setState: async (state) => {
   *   dataList.value = state.list || []
   *   queryParams.value = state.params || {}
   *   await nextTick()
   *   // 其他恢复逻辑
   * }
   * ```
   */
  setState: (state: any) => void | Promise<void>
  /** 
   * 组件引用配置（可选）
   * 
   * 如果提供，会在 setState 时自动调用组件的方法来恢复状态。
   * 这适用于需要调用子组件方法的情况，如表单组件、查询组件等。
   * 
   * 使用示例：
   * ```ts
   * componentRef: {
   *   ref: queryBarRef,
   *   methodName: 'setValues',
   *   getRestoreParams: (state) => state.formData
   * }
   * ```
   */
  componentRef?: ComponentRefConfig
  /**
   * 是否需要等待组件准备就绪（可选，默认：true）
   * 
   * 仅当 componentRef 存在时生效。
   * - true: 会在调用组件方法前等待 nextTick，确保组件已挂载
   * - false: 立即调用，适用于组件已经挂载的场景
   */
  waitForComponentReady?: boolean
}

/**
 * 组件 Props 接口
 */
export interface StatusStoragePlusProps {
  /** 
   * 状态存储配置数组
   * 
   * 每个配置项代表一个独立的状态单元。
   * 建议使用 computed 来创建，以便在响应式数据变化时更新配置。
   */
  stores: StatusStoreItem[]
  /** 
   * 状态存储的前缀（可选，默认：STATUS_STORAGE_）
   * 
   * 用于生成唯一的存储 key，避免不同页面的状态冲突。
   * 建议为每个页面设置唯一的前缀，如 'BASE_GRID_STATE_', 'IMPORT_GRID_STATE_' 等
   */
  storagePrefix?: string
  /** 
   * 状态数据的最大保存时间（毫秒，默认：24小时）
   * 
   * 超过此时间的数据会被自动清除，避免存储过期数据。
   */
  maxAge?: number
  /** 
   * 是否启用自动保存（默认：true，在路由离开时自动保存）
   * 
   * - true: 在路由切换时自动保存状态
   * - false: 需要手动调用 saveState 方法保存
   */
  autoSave?: boolean
  /** 
   * 存储适配器（可选，默认：localStorage）
   * 
   * 支持自定义存储方式，如 sessionStorage 或其他存储实现。
   * 可以通过 provideStorageAdapter 提供自定义适配器。
   */
  storageAdapter?: StorageAdapter
  /** 
   * 状态恢复完成后的回调函数（可选）
   * 
   * 当状态恢复完成时（无论是否成功），会调用此回调。
   * 可以用于在状态恢复完成后执行数据查询等操作。
   * 
   * 示例：
   * ```ts
   * onRestoreComplete: (restored: boolean) => {
   *   if (restored) {
   *     // 状态已恢复，可以开始查询数据
   *     getList()
   *   }
   * }
   * ```
   */
  onRestoreComplete?: (restored: boolean) => void | Promise<void>
}

const props = withDefaults(defineProps<StatusStoragePlusProps>(), {
  storagePrefix: 'STATUS_STORAGE_',
  maxAge: 24 * 60 * 60 * 1000, // 24小时
  autoSave: true,
  storageAdapter: undefined
})

const router = useRouter()
const tagsViewStore = useTagsViewStoreWithOut()

// 使用提供的存储适配器或默认适配器
const storage = computed<StorageAdapter>(() => {
  if (props.storageAdapter) {
    return props.storageAdapter
  }
  return localStorageAdapter
})

const PAGE_STATE_KEY = computed(() => `${props.storagePrefix}${router.currentRoute.value.fullPath}`)
const PAGE_RESTORE_FLAG_KEY = computed(() => `RESTORE_FLAG_${router.currentRoute.value.fullPath}`)

const pageReady = ref(false)
const isRestoring = ref(false)
let saveStateTimer: NodeJS.Timeout | null = null
let mountedRoutePath: string | null = null
let mountedRouteFullPath: string | null = null

/**
 * 保存页面状态到存储
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
        // 保存状态失败，静默处理
      }
    }
    
    const statePayload = {
      state,
      timestamp: Date.now(),
      fullPath: router.currentRoute.value.fullPath
    }
    
    storage.value.setItem(PAGE_STATE_KEY.value, JSON.stringify(statePayload))
  } catch (err) {
    // 保存页面状态失败，静默处理
  }
}

/**
 * 从存储恢复页面状态
 */
const restorePageState = async (): Promise<boolean> => {
  try {
    const savedState = storage.value.getItem(PAGE_STATE_KEY.value)
    
    if (!savedState) {
      return false
    }
    
    const statePayload = JSON.parse(savedState)
    
    // 检查时间戳是否过期
    const now = Date.now()
    const elapsed = now - statePayload.timestamp
    
    if (elapsed > props.maxAge) {
      storage.value.removeItem(PAGE_STATE_KEY.value)
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
          const stateData = state[store.name]
          
          // 如果有组件引用配置，先尝试通过组件方法恢复
          if (store.componentRef) {
            const { ref, methodName, getRestoreParams } = store.componentRef
            const shouldWait = store.waitForComponentReady !== false // 默认等待
            
            if (shouldWait) {
              await nextTick()
              // 如果组件仍未就绪，再等待一次
              if (!ref.value) {
                await nextTick()
              }
            }
            
            if (ref.value && typeof ref.value[methodName] === 'function') {
              try {
                // 如果有参数映射函数，使用它来转换参数
                const params = getRestoreParams ? getRestoreParams(stateData) : stateData
                await ref.value[methodName](params)
              } catch (err) {
                // 通过组件方法恢复状态失败，静默处理
              }
            }
            
            // 无论组件方法是否成功，都调用 setState（用于更新内部状态变量）
            // 例如：QueryBar.setValues 恢复了显示，但仍需要更新 formDisplayParams 等内部变量
            await store.setState(stateData)
          } else {
            // 没有组件引用配置，直接调用 setState
            await store.setState(stateData)
          }
        }
      } catch (err) {
        // 恢复状态失败，静默处理
      }
    }
    
    // 等待状态更新完成
    await nextTick()
    isRestoring.value = false
    
    return true
  } catch (err) {
    // 恢复页面状态失败，静默处理
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
    const savedState = storage.value.getItem(keyToRemove)
    
    if (savedState) {
      const state = JSON.parse(savedState)
      
      if (state.fullPath === pathToCheck) {
        storage.value.removeItem(keyToRemove)
      }
    }
    
    // 同时清除恢复标记（使用 sessionStorage）
    const flagKey = fullPath ? `RESTORE_FLAG_${fullPath}` : PAGE_RESTORE_FLAG_KEY.value
    try {
      sessionStorageAdapter.removeItem(flagKey)
    } catch (err) {
      // 删除恢复标记失败，静默处理
    }
  } catch (err) {
    // 清空页面状态失败，静默处理
  }
}

/**
 * 路由守卫：离开页面前保存状态
 */
onBeforeRouteLeave((_to, _from, next) => {
  // 检查是否是关闭页签的操作
  // 注意：此时页签可能还没有从 visitedViews 中移除，所以需要检查目标路由
  // 如果目标路由是关闭操作（不在 visitedViews 中，且不是新打开的路由），则可能是关闭
  const visitedViews = tagsViewStore.getVisitedViews
  const isFromInVisitedViews = visitedViews.some(
    view => view.fullPath === _from.fullPath || view.path === _from.path
  )
  
  // 如果当前路由不在 visitedViews 中，说明可能是关闭操作
  // 但为了安全起见，我们仍然保存状态（以防判断错误）
  // 真正的清空逻辑在 onBeforeUnmount 中处理
  const isLikelyClosing = !isFromInVisitedViews
  
  // 如果启用了自动保存，在路由跳转（切换窗口）时保存状态
  // 注意：即使是关闭，也先保存，然后在 onBeforeUnmount 中清空
  if (props.autoSave) {
    if (saveStateTimer) {
      clearTimeout(saveStateTimer)
      saveStateTimer = null
    }
    savePageState()
    
    // 只有在窗口切换时（不是关闭）才设置恢复标记
    // 窗口关闭时，onBeforeUnmount 会清空缓存和恢复标记
    if (!isLikelyClosing) {
      // 设置恢复标记，表示该路由有保存的状态，可以恢复（使用 sessionStorage）
      try {
        sessionStorageAdapter.setItem(PAGE_RESTORE_FLAG_KEY.value, '1')
      } catch (err) {
        // 设置恢复标记失败，静默处理
      }
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
  
  // 严格区分窗口打开、窗口切换和页面刷新场景
  // 1. 窗口打开：没有恢复标记，且没有匹配的缓存 -> 不恢复状态，清空可能存在的缓存
  // 2. 窗口切换：有恢复标记，且当前路由已在 visitedViews 中 -> 恢复状态
  // 3. 页面刷新：没有恢复标记，但有匹配的缓存数据 -> 恢复状态（刷新场景）
  let shouldRestore = false
  
  try {
    // 等待 nextTick，确保 tagsViewStore 已更新
    await nextTick()
    
    // 检查是否有恢复标记（这是判断窗口切换的主要依据）
    const restoreFlag = sessionStorageAdapter.getItem(PAGE_RESTORE_FLAG_KEY.value)
    const hasRestoreFlag = restoreFlag === '1'
    
    if (hasRestoreFlag) {
      // 有恢复标记，进一步验证是否是窗口切换场景
      // 检查当前路由是否已经在 visitedViews 中（确保不是首次打开但误设置了标记）
      const visitedViews = tagsViewStore.getVisitedViews
      const isInVisitedViews = visitedViews.some(
        view => view.fullPath === mountedRouteFullPath || view.path === mountedRoutePath
      )
      
      if (isInVisitedViews) {
        // 窗口切换场景：恢复状态
        shouldRestore = true
        // 清除标记，避免下次误判
        sessionStorageAdapter.removeItem(PAGE_RESTORE_FLAG_KEY.value)
      } else {
        // 有恢复标记但不在 visitedViews 中，可能是异常情况，清空缓存和标记
        clearPageState()
        sessionStorageAdapter.removeItem(PAGE_RESTORE_FLAG_KEY.value)
      }
    } else {
      // 没有恢复标记，检查是否是页面刷新场景
      // 页面刷新时：没有恢复标记，但有匹配的缓存数据
      const savedState = storage.value.getItem(PAGE_STATE_KEY.value)
      if (savedState) {
        try {
          const statePayload = JSON.parse(savedState)
          // 检查缓存的路由是否匹配当前路由
          if (statePayload.fullPath === mountedRouteFullPath) {
            // 检查时间戳是否过期
            const now = Date.now()
            const elapsed = now - statePayload.timestamp
            if (elapsed <= props.maxAge) {
              // 页面刷新场景：有匹配的缓存数据，恢复状态
              shouldRestore = true
            } else {
              // 缓存已过期，清空
              clearPageState()
            }
          } else {
            // 路由不匹配，清空缓存
            clearPageState()
          }
        } catch {
          // 解析失败，清空缓存
          clearPageState()
        }
      } else {
        // 窗口打开场景：没有恢复标记，也没有缓存数据，清空可能存在的缓存
        clearPageState()
      }
    }
  } catch (err) {
    // 出错时，为了安全起见，不恢复状态，清空缓存
    clearPageState()
    // 清除可能存在的恢复标记
    try {
      sessionStorageAdapter.removeItem(PAGE_RESTORE_FLAG_KEY.value)
    } catch {
      // 静默处理
    }
  }
  
  await nextTick()
  pageReady.value = true
  
  // 只有切换回来时才恢复状态，首次打开不恢复
  let restored = false
  if (shouldRestore) {
    restored = await restorePageState()
  }
  
  // 调用恢复完成回调（无论是否恢复，都通知调用方）
  if (props.onRestoreComplete) {
    try {
      await props.onRestoreComplete(restored)
    } catch (err) {
      // 恢复完成回调执行失败，静默处理
    }
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
  clearState: () => clearPageState(),
  /** 获取当前是否正在恢复状态 */
  isRestoring: () => isRestoring.value,
  /** 获取状态恢复完成的 Promise（用于等待状态恢复完成） */
  waitForRestore: async (): Promise<boolean> => {
    // 如果已经在恢复中，等待恢复完成
    if (isRestoring.value) {
      // 轮询等待恢复完成
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          if (!isRestoring.value) {
            clearInterval(checkInterval)
            resolve(true)
          }
        }, 10)
        // 超时保护（最多等待 5 秒）
        setTimeout(() => {
          clearInterval(checkInterval)
          resolve(false)
        }, 5000)
      })
    }
    // 如果不在恢复中，检查是否有保存的状态
    const savedState = storage.value.getItem(PAGE_STATE_KEY.value)
    return !!savedState
  }
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
