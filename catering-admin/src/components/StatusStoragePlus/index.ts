import StatusStoragePlus from './src/StatusStoragePlus.vue'
import type { Ref } from 'vue'

export { StatusStoragePlus }
export default StatusStoragePlus

// 导出类型和接口（通过重新声明的方式，避免从 .vue 文件直接导出类型的问题）

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
 * 组件引用配置（用于自动调用组件方法恢复状态）
 */
export interface ComponentRefConfig {
  /** 组件引用（通过 ref 获取） */
  ref: Ref<any>
  /** 恢复方法名（如 'setValues'，会在 ref.value[methodName] 上调用） */
  methodName: string
  /** 恢复时传递给方法的参数映射函数（可选，如果不提供则直接传递 state） */
  getRestoreParams?: (state: any) => any
  /** 是否等待组件准备就绪（可选，默认：true） */
  waitForComponentReady?: boolean
}

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
  /** 组件引用配置（可选） */
  componentRef?: ComponentRefConfig
  /** 是否需要等待组件准备就绪（可选，默认：true） */
  waitForComponentReady?: boolean
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
  /** 存储适配器（可选，默认：localStorage） */
  storageAdapter?: StorageAdapter
}
