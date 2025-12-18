<!--
  ImportGrid - Excel 风格的通用数据导入/批量维护组件
  
  功能：工具栏、数据持久化、保存逻辑、提示信息
  使用：通过 columns 配置列，通过 saveConfig 配置保存逻辑
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { useTagsViewStoreWithOut } from '@/store/modules/tagsView'
import { ElMessageBox } from 'element-plus'
import TablePlus from '@/components/TablePlus'
import type { TablePlusColumn } from '@/components/TablePlus'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PrompInfo } from '@/components/PrompInfo'

/**
 * 列配置接口（扩展 TablePlusColumn）
 */
export interface ImportGridColumn extends TablePlusColumn {
  /** 字段初始值（用于新增行时） */
  value?: any
}

/**
 * 工具栏按钮配置接口
 */
export interface ToolbarButton {
  /** 按钮类型：'add' | 'save' | 'custom' */
  type: 'add' | 'save' | 'custom'
  /** 按钮文本（custom 类型时必填） */
  label?: string
  /** 按钮样式类型（custom 类型时使用） */
  stype?: string
  /** 点击回调函数 */
  onClick?: () => void | Promise<void>
  /** 是否显示 loading 状态 */
  loading?: boolean
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
}

const props = withDefaults(defineProps<ImportGridProps>(), {
  createDefaultRow: () => ({}),
  mapRowData: (row: any) => row,
  showToolbar: true,
  addRowMessage: '已新增 1 行'
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

/**
 * 清理图片数组的状态标记
 */
const cleanImageArray = (imageArray: any[]): any[] => {
  if (!Array.isArray(imageArray)) return []
  return imageArray
    .filter((item: any) => typeof item === 'string' && !item.includes('?delete'))
    .map((item: any) => typeof item === 'string' ? item.replace(/\?(original|add|delete)/, '') : item)
}

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

const PAGE_STATE_KEY = computed(() => `IMPORT_GRID_STATE_${router.currentRoute.value.fullPath}`)

const pageReady = ref(false)
const isRestoring = ref(false)
let saveStateTimer: NodeJS.Timeout | null = null
let mountedRoutePath: string | null = null
let mountedRouteFullPath: string | null = null

const dataList = ref<any[]>([])
const originalData = ref<any[]>([])
const currentRowIndex = ref<number | null>(null)
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()
const saveLoading = ref(false)
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

/**
 * 路由守卫：离开页面前检查未保存的修改（仅用于路由跳转，不用于页签关闭）
 * 注意：页签关闭由页签守卫处理，这里只处理路由跳转的情况
 */
onBeforeRouteLeave((_to, _from, next) => {
  // 如果没有配置 saveConfig，不需要检查
  if (!props.saveConfig) {
    next()
    return
  }
  
  // 检查是否是关闭页签的操作
  // 如果当前路由不在已访问的页签列表中，说明页签被删除了，这是关闭页签的操作
  // 页签关闭由页签守卫处理，这里直接允许
  const isClosing = !tagsViewStore.getVisitedViews.some(
    view => view.fullPath === _from.fullPath || view.path === _from.path
  )
  
  if (isClosing) {
    // 页签关闭由页签守卫处理，这里直接允许
    next()
    return
  }
  
  // 路由跳转（切换窗口），检查是否有未保存的修改
  if (!hasUnsavedChanges()) {
    // 没有未保存的修改，允许跳转
    next()
    return
  }
  
  // 有未保存的修改，弹出确认对话框
  ElMessageBox.confirm('数据未保存，确定要退出吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      // 用户确认退出，允许跳转
      next()
    })
    .catch(() => {
      // 用户取消退出，阻止跳转
      next(false)
    })
})

/**
 * 浏览器标签页关闭前检查未保存的修改
 */
const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  if (props.saveConfig && hasUnsavedChanges()) {
    // 现代浏览器会忽略自定义消息，只显示默认消息
    event.preventDefault()
    event.returnValue = '' // Chrome 需要设置 returnValue
    return '' // 其他浏览器
  }
}

// ==================== 数据修改检测 ====================
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
      dataToSave.push({ row, index: i, isNew: true, originalRow: null })
    } else if (isModifiedFunc(row, originalRow)) {
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
  if (!originalRow) return true // 新增记录
  
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
        typeof item === 'string' && !item.includes('?delete')
      )
      const originalValidImages = originalImages.filter((item: any) => 
        typeof item === 'string' && !item.includes('?delete')
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
  
  // 校验必填字段（遇到第一个错误就停止）
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
            
            // 更新表格中的数据（完全深拷贝以避免引用共享）
            const updatedRow = {
              ...deepCloneObject(currentRow),
              ...deepCloneObject(updatedDetail)
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
  if (props.toolbarButtons && props.toolbarButtons.length > 0) {
    return props.toolbarButtons.map(btn => {
      if (btn.type === 'add') {
        return {
          ...btn,
          stype: 'new',
          onClick: async () => {
            addRow()
            if (btn.onClick) {
              await btn.onClick()
            }
          }
        }
      } else if (btn.type === 'save') {
        return {
          ...btn,
          stype: 'save',
          loading: saveLoading.value,
          onClick: async () => {
            await handleSave()
            if (btn.onClick) {
              await btn.onClick()
            }
          }
        }
      }
      return btn
    })
  }
  
  const buttons: ToolbarButton[] = []
  
  if (props.saveConfig) {
    buttons.push({
      type: 'save',
      stype: 'save',
      loading: saveLoading.value,
      onClick: handleSave
    })
  }
  
  return buttons
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
  dataList.value.push(newRow)
  originalData.value.push(JSON.parse(JSON.stringify(newRow)))
  
  // 触发回调
  if (props.onRowAdded) {
    props.onRowAdded(newRow, dataList.value.length - 1)
  }
  
  // 显示提示信息
  if (prompInfoRef.value) {
    prompInfoRef.value.info(props.addRowMessage || '已新增 1 行')
  }
}

// ==================== 数据持久化 ====================
/**
 * 保存页面状态到 localStorage
 */
const savePageState = async () => {
  if (!pageReady.value || isRestoring.value) return
  
  try {
    const state = {
      data: JSON.parse(JSON.stringify(dataList.value)),
      originalData: JSON.parse(JSON.stringify(originalData.value)),
      timestamp: Date.now(),
      fullPath: router.currentRoute.value.fullPath
    }
    localStorage.setItem(PAGE_STATE_KEY.value, JSON.stringify(state))
  } catch (err) {
    console.error('保存页面状态失败：', err)
  }
}

/**
 * 从 localStorage 恢复页面状态
 */
const restorePageState = () => {
  try {
    const savedState = localStorage.getItem(PAGE_STATE_KEY.value)
    if (savedState) {
      const state = JSON.parse(savedState)
      
      const now = Date.now()
      const elapsed = now - state.timestamp
      const maxAge = 24 * 60 * 60 * 1000 // 24小时
      
      if (elapsed < maxAge) {
        isRestoring.value = true
        dataList.value = state.data
        originalData.value = state.originalData
        isRestoring.value = false
        return true
      } else {
        localStorage.removeItem(PAGE_STATE_KEY.value)
      }
    }
  } catch (err) {
    console.error('恢复页面状态失败：', err)
  }
  return false
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
  } catch (err) {
    console.error('清空页面状态失败：', err)
  }
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
        // 合并默认行数据和传入数据
        // 每行都需要创建独立的 defaultRow 以避免引用共享
        dataList.value = dataArray.map((item: any) => {
          const defaultRow = getDefaultRow() // 每行独立创建
          const mappedRow = props.mapRowData(item)
          // 对mappedRow做完全深拷贝，避免任何引用共享
          const deepClonedMappedRow = JSON.parse(JSON.stringify(mappedRow))
          const mergedRow = {
            ...defaultRow,
            ...deepClonedMappedRow
          }
          return mergedRow
        })
        // 初始化原始数据
        originalData.value = JSON.parse(JSON.stringify(dataList.value))
        emit('dataLoaded', dataList.value)
        
        if (prompInfoRef.value) {
          prompInfoRef.value.info(`已导入 ${dataList.value.length} 条数据`)
        }
        
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
    
    if (pageReady.value && !isRestoring.value) {
      if (saveStateTimer) {
        clearTimeout(saveStateTimer)
      }
      saveStateTimer = setTimeout(async () => {
        await savePageState()
      }, 500)
    }
  },
  { deep: true, flush: 'post' }
)

// ==================== 生命周期 ====================
onMounted(async () => {
  mountedRoutePath = router.currentRoute.value.path
  mountedRouteFullPath = router.currentRoute.value.fullPath
  
  // 检查是否有手选数据（sessionStorage）
  const hasManualSelection = sessionStorage.getItem(props.storageKey) !== null
  
  if (hasManualSelection) {
    // 情况1：窗口新打开，有手选数据
    // 使用手选数据，清空 sessionStorage，清除状态数据（避免下次恢复时混淆）
    const loaded = await loadDataFromStorage()
    if (loaded) {
      // 清除状态数据，因为使用了新的手选数据
      clearPageState()
    } else {
      // 手选数据格式错误，显示空表
      dataList.value = [getDefaultRow()]
      originalData.value = JSON.parse(JSON.stringify(dataList.value))
      emit('dataLoaded', dataList.value)
      if (prompInfoRef.value) {
        prompInfoRef.value.ready()
      }
    }
  } else {
    // 情况2：页面恢复（从其他页面切换回来），或首次打开
    // 使用状态数据，不检查手选数据
    const restored = restorePageState()
    
    if (restored) {
      emit('dataLoaded', dataList.value)
      if (prompInfoRef.value) {
        prompInfoRef.value.info('已恢复上次编辑的数据')
      }
    } else {
      // 没有状态数据，显示空表
      dataList.value = [getDefaultRow()]
      originalData.value = JSON.parse(JSON.stringify(dataList.value))
      emit('dataLoaded', dataList.value)
      if (prompInfoRef.value) {
        prompInfoRef.value.ready()
      }
    }
  }
  
  pageReady.value = true
  
  // 注册页签关闭前检查函数（仅在配置了 saveConfig 时）
  if (props.saveConfig) {
    const currentRoute = router.currentRoute.value
    tagsViewStore.registerBeforeCloseHandler(currentRoute.fullPath, beforeCloseHandler)
    // 监听浏览器标签页关闭事件
    window.addEventListener('beforeunload', handleBeforeUnload)
  }
})

onBeforeUnmount(() => {
  if (saveStateTimer) {
    clearTimeout(saveStateTimer)
    saveStateTimer = null
  }
  
  // 注销页签关闭前检查函数并移除浏览器标签页关闭事件监听
  if (props.saveConfig) {
    const currentRoute = router.currentRoute.value
    tagsViewStore.unregisterBeforeCloseHandler(currentRoute.fullPath)
    window.removeEventListener('beforeunload', handleBeforeUnload)
  }
  
  const checkAndClear = () => {
    const fullPathToCheck = mountedRouteFullPath || router.currentRoute.value.fullPath
    const visitedViews = tagsViewStore.getVisitedViews
    const pathToCheck = mountedRoutePath || router.currentRoute.value.path
    const isStillOpen = visitedViews.some(view => view.path === pathToCheck)
    
    if (!isStillOpen) {
      const stateKey = `IMPORT_GRID_STATE_${fullPathToCheck}`
      clearPageState(stateKey, fullPathToCheck)
      return true
    } else {
      return false
    }
  }
  
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
        :columns="props.columns"
        :data="dataList"
        v-model:currentRowIndex="currentRowIndex"
        :show-delete-button="true"
        @update:data="handleDataUpdate"
        @row-delete="handleRowDelete"
        @row-add="handleRowAdd"
      />
    </div>
  </div>
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
</style>
