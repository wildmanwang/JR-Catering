<!--
  ImportGrid - Excel 风格的通用数据导入/批量维护组件
  
  功能：工具栏、数据持久化、保存逻辑、提示信息
  使用：通过 columns 配置列，通过 saveConfig 配置保存逻辑
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useTagsViewStoreWithOut } from '@/store/modules/tagsView'
import { ElMessageBox } from 'element-plus'
import TablePlus from '@/components/TablePlus'
import type { TablePlusColumn } from '@/components/TablePlus'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PrompInfo } from '@/components/PrompInfo'
import { StatusStoragePlus, type StatusStoreItem } from '@/components/StatusStoragePlus'
import { formatDataItem } from '@/utils/dsOptions'
import { processImageFields, cleanImageArray, ImageQuerySuffix } from '@/utils/imageList'

/**
 * 列配置接口（扩展 TablePlusColumn）
 */
export interface ImportGridColumn extends TablePlusColumn {
  /** 字段初始值（用于新增行时） */
  value?: any
  /** 选项数据获取接口（用于自动获取该字段的选项数据） */
  optionsApi?: () => Promise<{ data?: any[]; code?: number; [key: string]: any }> // 返回格式：{ data: [...] } 或直接返回数组
  /** 选项数据的 id 字段名（用于简化配置） */
  optionsIdField?: string // 例如：'id' 或 'value'
  /** 选项数据的 label 格式配置（用于简化配置，使用 dsOptions.ts 的格式） */
  optionsLabelFormat?: Array<['field' | 'value', string]> // 例如：[['field', 'label']] 或 [['field', 'name_unique']]
}

/**
 * 工具栏按钮配置接口
 */
export interface ToolbarButton {
  /** 按钮类型：'add' | 'save' | 'refresh' | 'custom' */
  type: 'add' | 'save' | 'refresh' | 'custom'
  /** 按钮文本（custom 类型时必填） */
  label?: string
  /** 按钮样式类型（custom 类型时使用） */
  stype?: string
  /** 点击回调函数 */
  onClick?: () => void | Promise<void>
  /** 是否显示 loading 状态 */
  loading?: boolean
  /** 是否右对齐（custom 类型时使用） */
  alignRight?: boolean
  /** 其他 ButtonPlus 属性 */
  [key: string]: any
}

/**
 * 保存配置接口
 */
export interface SaveConfig {
  /** 必填字段配置 */
  requiredFields?: Array<{ field: string; label: string }>
  /** 新增数据的 API 函数（如果提供，将自动处理新增逻辑） */
  addApi?: (data: any) => Promise<{ code: number; data?: any; msg?: string }>
  /** 更新数据的 API 函数（如果提供，将自动处理更新逻辑） */
  updateApi?: (data: any) => Promise<{ code: number; data?: any; msg?: string }>
  /** 获取详情的 API 函数（如果提供，将自动处理获取详情逻辑） */
  getDetailApi?: (id: any) => Promise<{ code: number; data?: any; msg?: string }>
  /** 保存单条数据的回调函数（新增或修改）- 如果提供了 addApi 和 updateApi，则不需要此回调 */
  onSave?: (data: { row: any; index: number; isNew: boolean }) => Promise<{ success: boolean; data?: any; id?: any; message?: string }>
  /** 获取详情数据的回调函数（保存后重新获取完整数据）- 如果提供了 getDetailApi，则不需要此回调 */
  onGetDetail?: (id: any) => Promise<any>
  /** 进度回调函数 */
  onProgress?: (message: string) => void
  /** 错误回调函数 */
  onError?: (message: string) => void
  /** 成功回调函数 */
  onSuccess?: (message: string) => void
  /** 警告回调函数 */
  onWarn?: (message: string) => void
  /** 数据修改检测函数（可选，默认会比较所有字段） */
  isDataModified?: (currentRow: any, originalRow: any) => boolean
  /** 数据预处理函数（在保存前对数据进行处理，如添加 status=0 等） */
  preprocessData?: (data: any, isNew: boolean) => any
  /** 数据后处理函数（保存后更新表格数据时的处理） */
  postprocessData?: (detail: any, currentRow: any) => any
}

/**
 * 组件 Props 接口
 */
export interface ImportGridProps {
  /** 列配置数组 */
  columns: ImportGridColumn[]
  /** 数据存储的 sessionStorage key（用于在页面间传递数据） */
  storageKey: string
  /** 创建默认行数据的函数（用于新增行） */
  createDefaultRow?: () => any
  /** 数据转换函数（将父窗口传入的数据转换为表格所需格式） */
  mapRowData?: (row: any) => any
  /** 保存配置（如果提供，则启用内置的保存功能） */
  saveConfig?: SaveConfig
  /** 是否显示工具栏（默认 true） */
  showToolbar?: boolean
  /** 工具栏按钮配置（如果提供，则使用自定义按钮；否则默认只显示保存按钮） */
  toolbarButtons?: ToolbarButton[]
  /** 新增行后的回调函数 */
  onRowAdded?: (row: any, index: number) => void
  /** 新增行后的提示消息（默认：'已新增 1 行'） */
  addRowMessage?: string
  /** 窗口标识（用于 StatusStoragePlus 的唯一标识，使用方需要赋值） */
  windowId?: string
}

const props = withDefaults(defineProps<ImportGridProps>(), {
  createDefaultRow: () => ({}),
  mapRowData: (row: any) => row,
  showToolbar: true,
  addRowMessage: '已新增 1 行',
  windowId: ''
})

const emit = defineEmits<{
  (e: 'dataLoaded', data: any[]): void
  (e: 'dataChanged', data: any[]): void
  (e: 'rowAdded', row: any, index: number): void
}>()

// ==================== 工具函数 ====================
/**
 * 深拷贝对象的字段值（数组和对象）
 */
const deepCloneValue = (value: any): any => {
  if (Array.isArray(value)) {
    return [...value]
  } else if (typeof value === 'object' && value !== null) {
    return { ...value }
  }
  return value
}

/**
 * 深拷贝对象的所有字段
 */
const deepCloneObject = (obj: any): any => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (Array.isArray(obj)) {
    return obj.map(item => deepCloneObject(item))
  }
  const cloned: any = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepCloneObject(obj[key])
    }
  }
  return cloned
}

// 注意：cleanImageArray 已从 @/utils/imageList 导入

/**
 * 获取默认行数据
 */
const getDefaultRow = (): any => {
  const defaultRowFromColumns: any = {}
  
  props.columns.forEach(column => {
    if (column.value !== undefined) {
      defaultRowFromColumns[column.field] = deepCloneValue(column.value)
    } else if (column.type === 'image') {
      defaultRowFromColumns[column.field] = []
    } else if (column.type === 'text' && column.required) {
      defaultRowFromColumns[column.field] = ''
    }
  })
  
  const defaultRowFromProp = props.createDefaultRow()
  return { ...defaultRowFromProp, ...defaultRowFromColumns }
}

// ==================== 状态管理 ====================
const router = useRouter()
const tagsViewStore = useTagsViewStoreWithOut()

const pageReady = ref(false)
const isRestoring = ref(false)

const dataList = ref<any[]>([])
const originalData = ref<any[]>([])

// StatusStoragePlus 组件引用
const statusStoragePlusRef = ref<InstanceType<typeof StatusStoragePlus>>()

// ==================== 选项数据管理 ====================
/** 存储各字段的选项数据（字段名 -> 选项数组） */
const fieldOptionsData = ref<Record<string, any[]>>({})

/**
 * 根据格式配置生成 label 文本（使用 dsOptions.ts）
 * @param dataSet - 数据集
 * @param uniqueId - 唯一标识
 * @param format - 格式配置
 * @returns 拼接后的 label 文本
 */
const generateLabelByFormat = (dataSet: any[], uniqueId: number | string, format: Array<['field' | 'value', string]>): string => {
  return formatDataItem(dataSet, uniqueId, format)
}

/**
 * 初始化选项数据（从列配置中收集 optionsApi 并获取数据）
 */
const initFieldOptions = async () => {
  // 收集所有需要获取选项数据的列
  const optionsApiMap = new Map<string, { api: () => Promise<any>; col: ImportGridColumn }>()
  
  props.columns.forEach((col) => {
    if (col.optionsApi && col.field) {
      optionsApiMap.set(col.field, {
        api: col.optionsApi,
        col
      })
    }
  })
  
  // 并行获取所有选项数据
  const promises = Array.from(optionsApiMap.entries()).map(async ([field, { api, col }]) => {
    try {
      const res = await api()
      let rawOptions: any[] = []
      
      // 处理响应数据
      if (Array.isArray(res)) {
        rawOptions = res
      } else if (res?.data && Array.isArray(res.data)) {
        rawOptions = res.data
      } else {
        console.warn(`字段 ${field} 的选项数据格式不正确：`, res)
        rawOptions = []
      }
      
      // 根据配置转换数据
      let transformedOptions: any[] = []
      if (col.optionsIdField && col.optionsLabelFormat && col.optionsLabelFormat.length > 0) {
        // 使用 dsOptions.ts 格式转换
        transformedOptions = rawOptions.map((item: any) => {
          const id = item[col.optionsIdField!]
          const label = generateLabelByFormat(rawOptions, id, col.optionsLabelFormat!)
          return {
            label,
            value: id,
            ...item // 保留原始数据
          }
        })
      } else {
        // 默认转换：尝试自动识别格式
        if (rawOptions.length > 0) {
          if (rawOptions[0].hasOwnProperty('label') && rawOptions[0].hasOwnProperty('value')) {
            // 已经是标准格式
            transformedOptions = rawOptions
          } else if (rawOptions[0].hasOwnProperty('id') && rawOptions[0].hasOwnProperty('name_unique')) {
            // 常见格式：{ id, name_unique, ... }
            transformedOptions = rawOptions.map((item: any) => ({
              label: item.name_unique,
              value: item.id,
              ...item
            }))
          } else {
            // 尝试其他格式
            transformedOptions = rawOptions.map((item: any) => ({
              label: item.label || item.name_unique || item.name || String(item.id || item.value),
              value: item.value !== undefined ? item.value : item.id,
              ...item
            }))
          }
        }
      }
      
      fieldOptionsData.value[field] = transformedOptions
    } catch (err) {
      console.error(`获取字段 ${field} 的选项数据失败：`, err)
      fieldOptionsData.value[field] = []
    }
  })
  
  await Promise.all(promises)
}

/**
 * 处理后的列配置（自动填充选项数据）
 */
const processedColumns = computed(() => {
  return props.columns.map((col) => {
    // 如果列配置了 optionsApi，但没有配置 options，则使用自动获取的数据
    if (col.optionsApi && !col.options && fieldOptionsData.value[col.field] && fieldOptionsData.value[col.field].length > 0) {
      return {
        ...col,
        options: fieldOptionsData.value[col.field]
      }
    }
    return col
  })
})

// 深拷贝数据
const deepCloneData = (data: any[]): any[] => {
  return JSON.parse(JSON.stringify(data))
}

// 标记是否已经恢复了状态（用于在 onMounted 中判断是否需要显示空表）
const hasRestoredState = ref(false)

// 配置状态存储（StatusStoragePlus 组件使用）
const stateStores = computed<StatusStoreItem[]>(() => [
  {
    name: 'importGrid',
    getState: () => ({
      data: deepCloneData(dataList.value),
      originalData: deepCloneData(originalData.value)
    }),
    setState: async (state: any) => {
      isRestoring.value = true
      hasRestoredState.value = true
      
      // 恢复数据
      if (state.data) {
        dataList.value = deepCloneData(state.data)
      }
      // 恢复 originalData（保存状态时已经保存了原始数据）
      if (state.originalData) {
        originalData.value = deepCloneData(state.originalData)
      }
      
      // 等待 ImagePlus 等子组件完成数据初始化
      // 使用双重 nextTick 确保所有子组件（包括 ImagePlus）都已完成数据更新
      await nextTick()
      await nextTick()
      
      // 注意：这里不能重新设置 originalData，因为我们要保持恢复的原始数据
      // 这样才能正确检测到用户修改的数据
      // 如果子组件（如 ImagePlus）对数据进行了规范化，我们需要同步更新 originalData 中对应的格式
      // 但是只同步格式变化，不改变数据的值，以确保能正确检测到未保存的修改
      
      // 同步 originalData 和 dataList 的长度（处理删除行的情况）
      if (originalData.value.length > dataList.value.length) {
        originalData.value = originalData.value.slice(0, dataList.value.length)
      }
      
      isRestoring.value = false
      
      // 触发数据加载事件
      emit('dataLoaded', dataList.value)
      if (prompInfoRef.value) {
        prompInfoRef.value.info('已恢复上次编辑的数据')
      }
    }
  }
])
const currentRowIndex = ref<number | null>(null)
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()
const saveLoading = ref(false)
const refreshLoading = ref(false)
const tablePlusRef = ref<InstanceType<typeof TablePlus>>()

// ==================== 窗口关闭提醒（页签守卫） ====================
/**
 * 页签关闭前检查函数
 * 返回 Promise<boolean>，true 表示允许关闭，false 表示阻止关闭
 */
const beforeCloseHandler = async (): Promise<boolean> => {
  // 如果没有配置 saveConfig，不需要检查
  if (!props.saveConfig) {
    return true
  }
  
  // 检查是否有未保存的修改
  if (!hasUnsavedChanges()) {
    // 没有未保存的修改，允许关闭
    return true
  }
  
  // 有未保存的修改，弹出确认对话框
  try {
    await ElMessageBox.confirm('数据未保存，确定要退出吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    // 用户确认退出，允许关闭
    return true
  } catch {
    // 用户取消退出，阻止关闭
    return false
  }
}


// 注意：已移除 handleBeforeUnload 监听
// 原因：
// 1. 页面刷新时，状态已由 StatusStoragePlus 自动保存到 localStorage，刷新后可以恢复
// 2. 关闭浏览器标签页时，状态会在组件卸载时自动保存，下次打开可以恢复
// 3. 应用内的页签关闭已由 beforeCloseHandler 处理，有友好的自定义提示
// 4. 浏览器系统对话框体验较差，且现代浏览器不允许自定义消息内容
// 如果需要阻止刷新/关闭标签页，可以取消下面的注释，但建议保留当前实现
// const handleBeforeUnload = (event: BeforeUnloadEvent) => {
//   if (props.saveConfig && hasUnsavedChanges()) {
//     event.preventDefault()
//     event.returnValue = ''
//     return ''
//   }
// }

// ==================== 数据修改检测 ====================
/**
 * 检查记录是否是空白记录（所有字段都是默认值或空值）
 * @param row 要检查的记录
 * @returns 是否是空白记录
 */
const isEmptyRow = (row: any): boolean => {
  const defaultRow = getDefaultRow()
  const fieldsToCompare = props.columns.map(col => col.field)
  
  for (const field of fieldsToCompare) {
    const column = props.columns.find(col => col.field === field)
    const currentValue = row[field]
    const defaultValue = defaultRow[field]
    
    if (column?.type === 'image') {
      // 图片字段：空数组或未定义才认为是空白
      const currentImages = currentValue || []
      if (currentImages.length > 0) {
        // 检查是否有实际图片（字符串格式，不是待上传的数组格式）
        const hasRealImages = currentImages.some((item: any) => typeof item === 'string')
        if (hasRealImages) {
          return false // 有实际图片，不是空白
        }
        // 如果有待上传的图片（数组格式），也认为不是空白
        const hasPendingUploads = currentImages.some((item: any) => 
          typeof item === 'object' && item !== null && Array.isArray(item)
        )
        if (hasPendingUploads) {
          return false // 有待上传的图片，不是空白
        }
      }
    } else {
      // 其他字段：与默认值比较
      // 如果当前值与默认值不同，说明有修改
      if (currentValue !== defaultValue) {
        // 处理空值的情况：null/undefined/'' 都视为空值
        const currentIsEmpty = (currentValue === null || currentValue === undefined || currentValue === '')
        const defaultIsEmpty = (defaultValue === null || defaultValue === undefined || defaultValue === '')
        
        // 如果都是空值，认为相同，继续检查下一个字段
        if (currentIsEmpty && defaultIsEmpty) {
          continue
        }
        
        // 否则认为有实际内容，不是空白
        return false
      }
    }
  }
  
  return true // 所有字段都是默认值或空值，是空白记录
}

/**
 * 获取需要保存的数据列表
 * @returns 需要保存的数据数组，包含 row、index、isNew、originalRow 信息
 */
const getDataToSave = (): Array<{ row: any; index: number; isNew: boolean; originalRow: any }> => {
  if (!props.saveConfig) {
    return []
  }
  
  const isModifiedFunc = props.saveConfig.isDataModified || defaultIsDataModified
  const dataToSave: Array<{ row: any; index: number; isNew: boolean; originalRow: any }> = []
  
  for (let i = 0; i < dataList.value.length; i++) {
    const row = dataList.value[i]
    const originalRow = originalData.value[i]
    const isNew = !row.id || row.id <= 0
    
    if (isNew) {
      // 新增记录：只有非空白记录才需要保存
      if (!isEmptyRow(row)) {
        dataToSave.push({ row, index: i, isNew: true, originalRow: null })
      }
    } else if (isModifiedFunc(row, originalRow)) {
      // 已存在的记录：只有被修改过的才需要保存
      dataToSave.push({ row, index: i, isNew: false, originalRow })
    }
  }
  
  return dataToSave
}

/**
 * 检查是否有未保存的数据修改
 */
const hasUnsavedChanges = (): boolean => {
  return getDataToSave().length > 0
}

/**
 * 默认的数据修改检测函数
 */
const defaultIsDataModified = (currentRow: any, originalRow: any): boolean => {
  if (!originalRow) {
    // 新增记录：与默认值比较，而不是直接返回 true
    // 如果与默认值相同，说明是空白记录，未修改
    return !isEmptyRow(currentRow)
  }
  
  // 获取所有列字段
  const fieldsToCompare = props.columns.map(col => col.field)
  
  for (const field of fieldsToCompare) {
    const column = props.columns.find(col => col.field === field)
    
    if (column?.type === 'image') {
      // 图片字段需要特殊比较
      const currentImages = currentRow[field] || []
      const originalImages = originalRow[field] || []
      
      // 检查是否有新上传的图片（对象格式）
      const hasNewUploads = currentImages.some((item: any) => 
        typeof item === 'object' && item !== null && Array.isArray(item)
      )
      
      // 如果有新上传的图片，说明有变化
      if (hasNewUploads) {
        return true
      }
      
      // 过滤掉删除标记的图片，只比较有效图片
      const currentValidImages = currentImages.filter((item: any) => 
        typeof item === 'string' && !item.includes(`?${ImageQuerySuffix.DELETE}`)
      )
      const originalValidImages = originalImages.filter((item: any) => 
        typeof item === 'string' && !item.includes(`?${ImageQuerySuffix.DELETE}`)
      )
      
      // 如果长度不同，肯定有变化
      if (currentValidImages.length !== originalValidImages.length) {
        return true
      }
      
      // 比较每个元素（包括顺序和标记），因为排序变化也应该被检测到
      // 保存后 originalData 应该已经是规范化后的格式，可以直接比较
      for (let i = 0; i < currentValidImages.length; i++) {
        if (currentValidImages[i] !== originalValidImages[i]) {
          return true
        }
      }
    } else {
      if (currentRow[field] !== originalRow[field]) {
        return true
      }
    }
  }
  
  return false
}

// ==================== 保存逻辑 ====================
/**
 * 使用 API 接口保存数据
 */
const saveWithApi = async (row: any, isNew: boolean): Promise<{ success: boolean; data?: any; id?: any; message?: string }> => {
  const config = props.saveConfig!
  
  let res
  if (isNew) {
    if (!config.addApi) {
      throw new Error('addApi is required for new records')
    }
    res = await config.addApi(row)
  } else {
    if (!config.updateApi) {
      throw new Error('updateApi is required for updating records')
    }
    res = await config.updateApi(row)
  }
  
  if (res.code !== 200) {
    return { success: false, message: res.msg || '保存失败' }
  }
  
  const id = res.data?.id || (res.data && typeof res.data === 'object' && 'id' in res.data ? res.data.id : null)
  return { success: true, data: res.data, id }
}

/**
 * 使用 API 接口获取详情
 */
const getDetailWithApi = async (id: any): Promise<any> => {
  const config = props.saveConfig!
  
  if (!config.getDetailApi) {
    throw new Error('getDetailApi is required')
  }
  
  const res = await config.getDetailApi(id)
  if (res.code === 200 && res.data) {
    return res.data
  }
  // 如果获取详情失败，返回 null，不抛出错误，避免影响保存流程
  // 因为保存已经成功，只是获取详情失败
  console.warn('获取详情失败：', res.msg || '获取详情失败')
  return null
}

/**
 * 保存数据（核心逻辑）
 */
const save = async (): Promise<void> => {
  const config = props.saveConfig
  if (!config) {
    console.warn('saveConfig is required to use save functionality')
    return
  }
  
  const useApi = !!(config.addApi && config.updateApi && config.getDetailApi)
  
  if (!useApi && !config.onSave) {
    console.warn('Either (addApi + updateApi + getDetailApi) or onSave is required')
    return
  }
  
  if (!useApi && config.onSave && !config.onGetDetail) {
    console.warn('onGetDetail is required when using onSave')
    return
  }
  
  // 先自动删除所有空白的新增记录（避免对空白记录进行不必要的校验）
  // 从后往前遍历，避免删除时索引变化的问题
  const removedIndices: number[] = []
  for (let i = dataList.value.length - 1; i >= 0; i--) {
    const row = dataList.value[i]
    const isNew = !row.id || row.id <= 0
    if (isNew && isEmptyRow(row)) {
      // 删除空白的新增记录
      dataList.value.splice(i, 1)
      originalData.value.splice(i, 1)
      removedIndices.push(i)
    }
  }
  
  // 如果有删除空白记录，等待 DOM 更新
  if (removedIndices.length > 0) {
    await nextTick()
  }
  
  // 校验必填字段（遇到第一个错误就停止）
  // 注意：此时空白记录已被删除，只校验实际需要保存的数据
  if (config.requiredFields && config.requiredFields.length > 0) {
    for (let index = 0; index < dataList.value.length; index++) {
      const row = dataList.value[index]
      for (const requiredField of config.requiredFields) {
        const value = row[requiredField.field]
        if (value === null || value === undefined || value === '') {
          const errorMessage = `第 ${index + 1} 行：${requiredField.label} 不能为空，请填写后点击"保存"继续处理...`
          if (prompInfoRef.value) {
            prompInfoRef.value.err(errorMessage)
          }
          config.onError?.(errorMessage)
          // 设置当前行（TablePlus 会自动定位）
          currentRowIndex.value = index
          return
        }
      }
    }
  }
  
  // 筛选需要保存的数据（使用公共函数）
  const dataToSave = getDataToSave()
  
  if (dataToSave.length === 0) {
    // 没有需要保存的数据
    const noChangeMessage = '没有数据需要保存。'
    if (prompInfoRef.value) {
      prompInfoRef.value.warn(noChangeMessage)
    }
    config.onWarn?.(noChangeMessage)
    return
  }
  
  try {
    let addCount = 0
    let updateCount = 0
    
    // ==================== 处理图片字段上传 ====================
    const imageColumns = props.columns.filter(col => col.type === 'image')
    for (const { index } of dataToSave) {
      // 遍历所有图片类型的列
      for (const column of imageColumns) {
        try {
          if (tablePlusRef.value?.uploadRowImageField) {
            await tablePlusRef.value.uploadRowImageField(index, column.field)
          }
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : '图片上传失败'
          const errorMessage = `第 ${index + 1} 行：${column.label || column.field} 图片上传失败，${errorMsg}`
          if (prompInfoRef.value) {
            prompInfoRef.value.err(errorMessage)
          }
          config.onError?.(errorMessage)
          // 设置当前行（TablePlus 会自动定位）
          currentRowIndex.value = index
          return
        }
      }
    }
    
    // 上传完成后，重新获取数据（因为图片数据已更新）
    await nextTick()
    
    // 逐行处理需要保存的数据
    for (const { row, index, isNew } of dataToSave) {
      // 设置当前行
      currentRowIndex.value = index
      
      // 显示进度
      const progressMessage = `正在提交第 ${index + 1} 行...`
      if (prompInfoRef.value) {
        prompInfoRef.value.info(progressMessage)
      }
      config.onProgress?.(progressMessage)
      
      try {
        // 重新获取行数据（因为图片上传后数据已更新）
        let currentData = dataList.value
        const updatedRow = currentData[index] || row
        
        // 深拷贝行数据
        let submitData = JSON.parse(JSON.stringify(updatedRow))
        
        // 处理图片字段：确保只保留字符串格式的图片（过滤掉数组格式的未上传图片）
        // 注意：必须保留标记（?original、?add、?delete），因为后端需要这些标记来判断操作类型
        // ?add 标记的图片在删除时已经从数组中移除，不会出现在这里
        const imageColumns = props.columns.filter(col => col.type === 'image')
        for (const column of imageColumns) {
          if (Array.isArray(submitData[column.field])) {
            submitData[column.field] = submitData[column.field].filter((item: any) => typeof item === 'string')
          }
        }
        
        // 数据预处理
        if (config.preprocessData) {
          submitData = config.preprocessData(submitData, isNew)
        }
        
        // 提交数据
        const result = useApi 
          ? await saveWithApi(submitData, isNew)
          : await config.onSave!({ row: submitData, index, isNew })
        
        if (!result.success) {
          throw new Error(result.message || '保存失败')
        }
        
        // 从数据库重新获取该条记录
        const id = result.id || (isNew ? (result.data?.id || (result.data && typeof result.data === 'object' && 'id' in result.data ? result.data.id : null)) : row.id)
        
        if (id) {
          // 重新获取完整记录（使用 API 接口或回调函数）
          let detail: any = null
          try {
            detail = useApi
              ? await getDetailWithApi(id)
              : await config.onGetDetail!(id)
          } catch (err) {
            // 如果获取详情失败，不抛出错误，避免影响保存流程
            // 因为保存已经成功，只是获取详情失败
            console.warn('获取详情失败：', err)
            detail = null
          }
          
          if (detail) {
            currentData = dataList.value
            const currentRow = currentData[index]
            
            // 数据后处理
            let updatedDetail = detail
            if (config.postprocessData) {
              updatedDetail = config.postprocessData(detail, currentRow)
            }
            
            // 处理图片字段（排序并移除排序前缀）
            // 从列配置中提取 type === 'image' 的字段名
            const imageFields = props.columns
              .filter((col) => col.type === 'image')
              .map((col) => col.field)
            
            // 使用 processImageFields 统一处理图片字段
            const processedDetail = processImageFields(updatedDetail, imageFields, {
              processList: true,
              cleanArray: false
            })
            
            // 更新表格中的数据（完全深拷贝以避免引用共享）
            const updatedRow = {
              ...deepCloneObject(currentRow),
              ...deepCloneObject(processedDetail)
            }
            
            dataList.value = dataList.value.map((row, idx) => 
              idx === index ? updatedRow : row
            )
            
            // 等待 ImagePlus 组件规范化数据后再更新原始数据
            await nextTick()
            await nextTick() // 双重 nextTick 确保 ImagePlus 完成规范化
            
            // 更新原始数据（使用规范化后的数据）
            originalData.value[index] = JSON.parse(JSON.stringify(dataList.value[index]))
          } else {
            // 如果没有获取到详情，清理图片标记并更新原始数据
            currentData = dataList.value
            const currentRow = currentData[index]
            const cleanedRow = deepCloneObject(currentRow)
            
            // 清理图片字段的状态标记
            const imageColumns = props.columns.filter(col => col.type === 'image')
            imageColumns.forEach(column => {
              if (Array.isArray(cleanedRow[column.field])) {
                cleanedRow[column.field] = cleanImageArray(cleanedRow[column.field])
              }
            })
            
            dataList.value = dataList.value.map((row, idx) => 
              idx === index ? cleanedRow : row
            )
            
            await nextTick()
            originalData.value[index] = JSON.parse(JSON.stringify(dataList.value[index]))
          }
        } else {
          // 如果没有 id，清理图片标记并更新原始数据
          currentData = dataList.value
          const currentRow = currentData[index]
          const cleanedRow = deepCloneObject(currentRow)
          
          // 清理图片字段的状态标记
          const imageColumns = props.columns.filter(col => col.type === 'image')
          imageColumns.forEach(column => {
            if (Array.isArray(cleanedRow[column.field])) {
              cleanedRow[column.field] = cleanImageArray(cleanedRow[column.field])
            }
          })
          
          dataList.value = dataList.value.map((row, idx) => 
            idx === index ? cleanedRow : row
          )
          
          await nextTick()
          originalData.value[index] = JSON.parse(JSON.stringify(dataList.value[index]))
        }
        
        if (isNew) {
          addCount++
        } else {
          updateCount++
        }
      } catch (err: any) {
        const errorMsg = err.message || err.msg || '保存失败'
        const errorMessage = `第 ${index + 1} 行：${errorMsg}，修改后点击"保存"继续处理...`
        if (prompInfoRef.value) {
          prompInfoRef.value.err(errorMessage)
        }
        config.onError?.(errorMessage)
        // 设置当前行（不选中具体单元格，因为无法确定具体字段）
        currentRowIndex.value = index
        // 中断整个处理流程
        return
      }
    }
    
    // 显示最终统计
    const messages: string[] = []
    if (addCount > 0) {
      messages.push(`新增了 ${addCount} 条`)
    }
    if (updateCount > 0) {
      messages.push(`修改了 ${updateCount} 条`)
    }
    if (messages.length > 0) {
      const successMessage = `成功${messages.join('、')}数据。`
      if (prompInfoRef.value) {
        prompInfoRef.value.info(successMessage)
      }
      config.onSuccess?.(successMessage)
    } else {
      // 没有需要保存的数据
      const noChangeMessage = '没有需要保存的数据'
      if (prompInfoRef.value) {
        prompInfoRef.value.info(noChangeMessage)
      }
      config.onWarn?.(noChangeMessage)
    }
    
    // 清除当前行
    currentRowIndex.value = null
  } catch (err) {
    console.error('保存失败：', err)
    const errorMessage = '保存失败，请稍后重试'
    if (prompInfoRef.value) {
      prompInfoRef.value.err(errorMessage)
    }
    config.onError?.(errorMessage)
  }
}

// ==================== 新增行 ====================
const addRow = (): { row: any; index: number } => {
  const newRow = getDefaultRow()
  const newIndex = dataList.value.length
  
  dataList.value.push(newRow)
  originalData.value.push(JSON.parse(JSON.stringify(newRow)))
  
  // 切换当前行到新行
  currentRowIndex.value = newIndex
  
  emit('rowAdded', newRow, newIndex)
  props.onRowAdded?.(newRow, newIndex)
  prompInfoRef.value?.info(props.addRowMessage)
  
  return { row: newRow, index: newIndex }
}

// ==================== 工具栏相关 ====================
/**
 * 计算工具栏按钮配置
 */
const toolbarButtons = computed<ToolbarButton[]>(() => {
  const mappedButtons: ToolbarButton[] = []
  
  if (props.toolbarButtons && props.toolbarButtons.length > 0) {
    // 映射用户自定义的按钮
    props.toolbarButtons.forEach(btn => {
      if (btn.type === 'add') {
        mappedButtons.push({
          ...btn,
          stype: 'new',
          onClick: async () => {
            addRow()
            if (btn.onClick) {
              await btn.onClick()
            }
          }
        })
      } else if (btn.type === 'save') {
        mappedButtons.push({
          ...btn,
          stype: 'save',
          loading: saveLoading.value,
          onClick: async () => {
            await handleSave()
            if (btn.onClick) {
              await btn.onClick()
            }
          }
        })
      } else if (btn.type === 'refresh') {
        mappedButtons.push({
          ...btn,
          stype: 'refresh',
          loading: refreshLoading.value,
          alignRight: true,
          onClick: async () => {
            await handleRefresh()
            if (btn.onClick) {
              await btn.onClick()
            }
          }
        })
      } else {
        mappedButtons.push(btn)
      }
    })
  } else {
    // 没有自定义按钮，使用默认按钮
    if (props.saveConfig) {
      mappedButtons.push({
        type: 'save',
        stype: 'save',
        loading: saveLoading.value,
        onClick: handleSave
      })
    }
  }
  
  // 如果配置了 saveConfig，自动在保存按钮右边添加刷新按钮（如果还没有的话）
  if (props.saveConfig) {
    const hasRefreshButton = mappedButtons.some(btn => btn.type === 'refresh')
    if (!hasRefreshButton) {
      // 找到保存按钮的位置，在它后面插入刷新按钮
      const saveIndex = mappedButtons.findIndex(btn => btn.type === 'save')
      if (saveIndex >= 0) {
        mappedButtons.splice(saveIndex + 1, 0, {
          type: 'refresh',
          stype: 'refresh',
          loading: refreshLoading.value,
          alignRight: true,
          onClick: handleRefresh
        })
      } else {
        // 如果没有保存按钮，直接添加刷新按钮
        mappedButtons.push({
          type: 'refresh',
          stype: 'refresh',
          loading: refreshLoading.value,
          alignRight: true,
          onClick: handleRefresh
        })
      }
    }
  }
  
  return mappedButtons
})

/**
 * 处理保存操作
 */
const handleSave = async (): Promise<void> => {
  if (!props.saveConfig) {
    console.warn('saveConfig is required to use save functionality')
    return
  }
  
  saveLoading.value = true
  try {
    await save()
  } catch (err) {
    console.error('保存失败：', err)
    const errorMessage = err instanceof Error ? err.message : '保存失败，请稍后重试'
    if (prompInfoRef.value) {
      prompInfoRef.value.err(errorMessage)
    }
    if (props.saveConfig?.onError) {
      props.saveConfig.onError(errorMessage)
    }
  } finally {
    saveLoading.value = false
  }
}

/**
 * 处理刷新操作
 */
const handleRefresh = async (): Promise<void> => {
  if (!props.saveConfig) {
    console.warn('saveConfig is required to use refresh functionality')
    return
  }
  
  // 检查是否有未保存的修改
  if (hasUnsavedChanges()) {
    // 有未保存的修改，弹出确认对话框
    try {
      await ElMessageBox.confirm('要放弃已修改的数据吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
    } catch {
      // 用户取消，不执行刷新
      return
    }
  }
  
  refreshLoading.value = true
  try {
    // 从当前数据中提取已保存的记录的 ID（排除新增的行）
    const savedIds = dataList.value
      .filter(row => row.id && row.id > 0)
      .map(row => row.id)
    
    if (savedIds.length === 0) {
      // 没有已保存的数据，清空数据列表（不插入空行，与 F5 刷新行为一致）
      clearDataList('没有已保存的数据')
      return
    }
    
    // 使用 getDetailApi 批量获取详情
    const config = props.saveConfig
    if (!config.getDetailApi) {
      throw new Error('getDetailApi is required for refresh functionality')
    }
    
    // 批量获取详情
    const detailPromises = savedIds.map(id => config.getDetailApi!(id))
    const detailResults = await Promise.all(detailPromises)
    
    // 处理获取到的数据
    const rawDataArray: any[] = []
    for (let i = 0; i < detailResults.length; i++) {
      const res = detailResults[i]
      if (res.code === 200 && res.data) {
        rawDataArray.push(res.data)
      }
    }
    
    if (rawDataArray.length === 0) {
      // 没有获取到数据，清空数据列表（不插入空行，与 F5 刷新行为一致）
      clearDataList('没有获取到数据')
      return
    }
    
    // 映射和合并数据，然后设置并等待初始化
    const refreshedData = mapAndMergeRowData(rawDataArray)
    await setDataAndWaitForInit(refreshedData, `已刷新 ${refreshedData.length} 条数据`)
  } catch (err) {
    console.error('刷新失败：', err)
    const errorMessage = err instanceof Error ? err.message : '刷新失败，请稍后重试'
    if (prompInfoRef.value) {
      prompInfoRef.value.err(errorMessage)
    }
    if (props.saveConfig?.onError) {
      props.saveConfig.onError(errorMessage)
    }
  } finally {
    refreshLoading.value = false
  }
}

/**
 * 处理数据更新
 */
const handleDataUpdate = (newData: any[]) => {
  dataList.value = newData
  // 同步更新 originalData（删除行时需要）
  if (originalData.value.length > newData.length) {
    // 有行被删除，需要同步 originalData
    originalData.value = originalData.value.slice(0, newData.length)
  }
}

/**
 * 处理行删除
 */
const handleRowDelete = (rowIndex: number) => {
  // 同步删除 originalData 中对应的行
  if (rowIndex >= 0 && rowIndex < originalData.value.length) {
    originalData.value.splice(rowIndex, 1)
  }
}

/**
 * 处理行新增
 */
const handleRowAdd = (defaultRow: any) => {
  const newRow = { ...getDefaultRow(), ...defaultRow }
  const newIndex = dataList.value.length
  
  dataList.value.push(newRow)
  originalData.value.push(JSON.parse(JSON.stringify(newRow)))
  
  // 切换当前行到新行
  currentRowIndex.value = newIndex
  
  // 触发回调
  if (props.onRowAdded) {
    props.onRowAdded(newRow, newIndex)
  }
  
  // 显示提示信息
  if (prompInfoRef.value) {
    prompInfoRef.value.info(props.addRowMessage || '已新增 1 行')
  }
}

// ==================== 数据持久化 ====================
// 状态保存和恢复功能已由 StatusStoragePlus 组件处理

// 注意：图片处理已转移到 @/utils/imageList，使用 processImageFields 函数

/**
 * 映射和合并行数据（公共逻辑）
 * @param rawData 原始数据
 * @returns 合并后的行数据数组
 */
const mapAndMergeRowData = (rawDataArray: any[]): any[] => {
  return rawDataArray.map((item: any) => {
    const defaultRow = getDefaultRow() // 每行独立创建
    const mappedRow = props.mapRowData ? props.mapRowData(item) : item
    // 对mappedRow做完全深拷贝，避免任何引用共享
    const deepClonedMappedRow = JSON.parse(JSON.stringify(mappedRow))
    
    // 处理图片字段（排序并移除排序前缀）
    // 从列配置中提取 type === 'image' 的字段名
    const imageFields = props.columns
      .filter((col) => col.type === 'image')
      .map((col) => col.field)
    
    const processedRow = processImageFields(deepClonedMappedRow, imageFields, {
      processList: true,
      cleanArray: false
    })
    
    const mergedRow = {
      ...defaultRow,
      ...processedRow
    }
    return mergedRow
  })
}

/**
 * 设置数据并等待组件初始化完成（公共逻辑）
 * @param newData 新的数据数组
 * @param infoMessage 可选的提示信息
 */
const setDataAndWaitForInit = async (newData: any[], infoMessage?: string): Promise<void> => {
  // 更新数据
  dataList.value = newData
  
  // 等待 ImagePlus 组件完成数据初始化（如果有图片列）
  // 使用双重 nextTick 确保所有子组件（包括 ImagePlus）都已完成数据更新
  await nextTick()
  await nextTick()
  
  // 在 ImagePlus 组件完成数据初始化后再设置 originalData
  // 这样可以确保 dataList 和 originalData 的一致性，避免误报未保存修改
  originalData.value = JSON.parse(JSON.stringify(dataList.value))
  
  emit('dataLoaded', dataList.value)
  
  if (infoMessage && prompInfoRef.value) {
    prompInfoRef.value.info(infoMessage)
  }
}

/**
 * 清空数据列表（不插入空行，用于刷新时无数据的情况）
 * @param infoMessage 可选的提示信息
 */
const clearDataList = (infoMessage?: string): void => {
  dataList.value = []
  originalData.value = []
  if (infoMessage && prompInfoRef.value) {
    prompInfoRef.value.info(infoMessage)
  }
}

/**
 * 设置空表（插入一个空行，用于首次打开需要默认行的情况）
 * @param infoMessage 可选的提示信息
 */
const setEmptyTable = async (infoMessage?: string): Promise<void> => {
  await setDataAndWaitForInit([getDefaultRow()], infoMessage)
}

/**
 * 从 sessionStorage 加载导入数据
 * @returns {Promise<boolean>} 是否成功加载了数据
 */
const loadDataFromStorage = async (): Promise<boolean> => {
  try {
    const savedPayload = sessionStorage.getItem(props.storageKey)
    if (savedPayload) {
      const parsed = JSON.parse(savedPayload)
      
      // 兼容两种数据格式：
      // 1. 直接是数组格式（从 Dish.vue 等父窗口传入）
      // 2. 对象格式，包含 action 和 data
      let dataArray: any[] = []
      
      if (Array.isArray(parsed)) {
        // 格式1：直接是数组
        dataArray = parsed
      } else if (parsed && parsed.action === 'import' && Array.isArray(parsed.data)) {
        // 格式2：对象格式，包含 action 和 data
        dataArray = parsed.data
      }
      
      if (dataArray.length > 0) {
        // 有数据，加载数据
        const mergedData = mapAndMergeRowData(dataArray)
        await setDataAndWaitForInit(mergedData, `已导入 ${mergedData.length} 条数据`)
        
        // 清除 sessionStorage，避免重复加载
        sessionStorage.removeItem(props.storageKey)
        return true
      } else {
        // 数据为空数组，清除 sessionStorage
        sessionStorage.removeItem(props.storageKey)
        return false
      }
    }
  } catch (err) {
    console.error('加载导入数据失败：', err)
    // 数据格式错误，清除 sessionStorage
    sessionStorage.removeItem(props.storageKey)
  }
  
  // 没有数据，返回 false，让调用方决定如何处理（恢复状态或显示空表）
  return false
}

// ==================== 数据监听 ====================
watch(
  () => dataList.value,
  (newData) => {
    emit('dataChanged', newData)
    // 状态保存由 StatusStoragePlus 组件自动处理
  },
  { deep: true, flush: 'post' }
)

// ==================== 生命周期 ====================
onMounted(async () => {
  // 初始化选项数据（从列配置中获取）
  await initFieldOptions()
  
  // 检查是否有手选数据（sessionStorage）
  const hasManualSelection = sessionStorage.getItem(props.storageKey) !== null
  
  if (hasManualSelection) {
    // 情况1：窗口新打开，有手选数据
    // 使用手选数据，清空 sessionStorage，清除状态数据（避免下次恢复时混淆）
    const loaded = await loadDataFromStorage()
    if (loaded) {
      // 清除状态数据，因为使用了新的手选数据
      statusStoragePlusRef.value?.clearState()
    } else {
      // 手选数据格式错误，显示空表
      await setEmptyTable()
      if (prompInfoRef.value) {
        prompInfoRef.value.ready()
      }
    }
  } else {
    // 情况2：页面恢复（从其他页面切换回来），或首次打开，或刷新页面
    // 状态恢复由 StatusStoragePlus 组件自动处理（只有切换回来时才恢复，首次打开/刷新不恢复）
    // StatusStoragePlus 会在 onMounted 时检查恢复标记，如果是切换回来会自动调用 setState
    // 状态恢复完成后会调用 handleRestoreComplete 回调
    // 如果是首次打开（没有保存的状态），handleRestoreComplete 也会被调用（restored = false）
    // 等待状态恢复完成（通过 handleRestoreComplete 回调处理）
    await nextTick()
    
    // 检查是否有保存的状态（通过 StatusStoragePlus 的 waitForRestore 方法）
    const hasSavedState = await statusStoragePlusRef.value?.waitForRestore()
    
    if (!hasSavedState) {
      // 首次打开，没有保存的状态，不自动插入空行
      // 让 dataList 保持为空数组，用户需要手动添加数据
      if (!hasRestoredState.value && dataList.value.length === 0) {
        // 不调用 setEmptyTable()，保持空数组，避免刷新后自动插入空行导致提示保存
        // 如果用户需要添加数据，可以通过工具栏的"新增"按钮添加
        if (prompInfoRef.value) {
          prompInfoRef.value.ready()
        }
      }
      // 设置 pageReady，显示页面
      pageReady.value = true
    }
    // 如果有保存的状态，handleRestoreComplete 会在状态恢复完成后被调用，并设置 pageReady
  }
  
  // 注册页签关闭前检查函数（仅在配置了 saveConfig 时）
  if (props.saveConfig) {
    const currentRoute = router.currentRoute.value
    tagsViewStore.registerBeforeCloseHandler(currentRoute.fullPath, beforeCloseHandler)
    // 注意：不再监听 beforeunload 事件
    // 原因：状态已由 StatusStoragePlus 自动保存，刷新/关闭标签页时不会丢失数据
    // 如果需要浏览器级别的提示，可以取消下面的注释
    // window.addEventListener('beforeunload', handleBeforeUnload)
  }
})

onBeforeUnmount(() => {
  // 注销页签关闭前检查函数
  if (props.saveConfig) {
    const currentRoute = router.currentRoute.value
    tagsViewStore.unregisterBeforeCloseHandler(currentRoute.fullPath)
    // 注意：不再移除 beforeunload 监听（因为已经不再添加）
    // window.removeEventListener('beforeunload', handleBeforeUnload)
  }
  
  // 状态清空由 StatusStoragePlus 组件自动处理
})

/**
 * 处理状态恢复完成回调
 * 当 StatusStoragePlus 完成状态恢复后，调用此函数
 */
const handleRestoreComplete = async (_restored: boolean) => {
  // 状态恢复已完成（无论是否成功恢复）
  // 如果没有恢复状态（首次打开、刷新页面或没有保存的状态），不自动插入空行
  if (!hasRestoredState.value && dataList.value.length === 0) {
    // 不调用 setEmptyTable()，保持空数组，避免刷新后自动插入空行导致提示保存
    // 如果用户需要添加数据，可以通过工具栏的"新增"按钮添加
    if (prompInfoRef.value) {
      prompInfoRef.value.ready()
    }
  }
  
  // 显示页面
  pageReady.value = true
}

// ==================== 暴露方法 ====================
defineExpose({
  getData: () => dataList.value,
  setData: (data: any[]) => {
    dataList.value = data
    originalData.value = JSON.parse(JSON.stringify(data))
  },
  getDefaultRow,
  loadDataFromStorage,
  save,
  addRow,
  prompInfoRef,
  hasUnsavedChanges
})
</script>

<template>
  <StatusStoragePlus
    ref="statusStoragePlusRef"
    :stores="stateStores"
    :storage-prefix="props.windowId || 'IMPORT_GRID_STATE_'"
    :on-restore-complete="handleRestoreComplete"
  >
    <div class="import-grid-container">
      <!-- 工具栏 -->
      <div v-if="props.showToolbar" class="import-grid-toolbar">
        <div class="toolbar-left">
        <template v-for="(btn, index) in toolbarButtons" :key="index">
          <ButtonPlus
            v-if="btn.type === 'add'"
            :stype="btn.stype"
            :loading="btn.loading"
            @click="btn.onClick"
          />
          <ButtonPlus
            v-else-if="btn.type === 'custom' && !btn.alignRight"
            :stype="btn.stype"
            :loading="btn.loading"
            @click="btn.onClick"
          >
            {{ btn.label }}
          </ButtonPlus>
        </template>
      </div>
      <div class="toolbar-info">
        <PrompInfo ref="prompInfoRef" />
      </div>
      <div class="toolbar-right">
        <template v-for="(btn, index) in toolbarButtons" :key="`right-${index}`">
          <ButtonPlus
            v-if="btn.type === 'save'"
            :stype="btn.stype"
            :loading="btn.loading"
            @click="btn.onClick"
          />
          <ButtonPlus
            v-else-if="btn.type === 'refresh'"
            :stype="btn.stype"
            :loading="btn.loading"
            @click="btn.onClick"
          />
          <ButtonPlus
            v-else-if="btn.type === 'custom' && btn.alignRight"
            :stype="btn.stype"
            :loading="btn.loading"
            @click="btn.onClick"
          >
            {{ btn.label }}
          </ButtonPlus>
        </template>
        </div>
      </div>
    
      <!-- 表格 -->
    <div class="table-wrapper">
      <TablePlus
        ref="tablePlusRef"
        :columns="processedColumns"
        :data="dataList"
        v-model:currentRowIndex="currentRowIndex"
        :show-delete-button="true"
        @update:data="handleDataUpdate"
        @row-delete="handleRowDelete"
        @row-add="handleRowAdd"
      />
      </div>
    </div>
  </StatusStoragePlus>
</template>

<style lang="less" scoped>
.import-grid-container {
  padding: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.import-grid-toolbar {
  display: flex;
  align-items: center;
  margin: 0 0 10px 0;
  gap: 10px;
  flex-shrink: 0;
}

.toolbar-left {
  flex: 0 0 auto;
  display: flex;
  gap: 10px;
}

.toolbar-info {
  flex: 1;
  min-width: 0;
}

.toolbar-right {
  flex: 0 0 auto;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// 确保在 ContentWrap 容器中正确显示
// 这些样式确保 ImportGrid 能够填充整个 ContentWrap 容器的高度
:deep(.content-wrap),
:deep(.content-wrap .el-card),
:deep(.content-wrap .el-card__body) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  min-height: 0 !important;
  overflow: hidden !important;
}

:deep(.content-wrap > div) {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}
</style>
