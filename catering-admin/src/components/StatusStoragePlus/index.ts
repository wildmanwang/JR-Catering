import StatusStoragePlus from './src/StatusStoragePlus.vue'

export { StatusStoragePlus }
export default StatusStoragePlus

// 导出类型（通过重新声明的方式）
export interface StatusStoreItem {
  /** 状态名称（用于标识不同的状态） */
  name: string
  /** 获取状态的函数，返回要保存的状态数据 */
  getState: () => any
  /** 设置状态的函数，接收保存的状态数据 */
  setState: (state: any) => void | Promise<void>
}

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

