<!--
  ImportGrid - Excel 风格的通用数据导入/批量维护组件
  
  功能：Excel 风格表格编辑、多种数据类型、数据持久化、键盘导航、复制粘贴
  使用：通过 columns 配置列，通过 saveConfig 配置保存逻辑
-->
<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, onUnmounted, watch, nextTick, toRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ElTable, ElTableColumn, ElInput, ElInputNumber, ElSelect, ElOption, ElImage, ElUpload, ElIcon, ElMessage, UploadProps } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useTagsViewStoreWithOut } from '@/store/modules/tagsView'
import { useAuthStore } from '@/store/modules/auth'
import ImagePlus from '@/components/ImagePlus/src/ImagePlus.vue'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PrompInfo } from '@/components/PrompInfo'

/**
 * 列配置接口
 */
export interface ImportGridColumn {
  /** 字段名（对应数据对象的 key） */
  field: string
  /** 列标题 */
  label: string
  /** 列宽度（如 '100px'） */
  width?: string
  /** 最小列宽度 */
  minWidth?: string
  /** 是否显示该列（默认 true） */
  show?: boolean
  /** 数据类型 */
  type?: 'text' | 'number' | 'select' | 'image' | 'date'
  /** ImagePlus 组件尺寸（仅当 type='image' 时有效，默认 'small'） */
  size?: 'normal' | 'small'
  /** 字段初始值（用于新增行时，与 FormSchema 的 value 属性保持一致） */
  value?: any
  /** 自定义格式化函数 */
  formatter?: (row: any, column: any, cellValue: any) => string
  /** 下拉选择选项（type='select' 时必填） */
  options?: Array<{ label: string; value: any }>
  /** 是否可编辑（默认 true） */
  editable?: boolean
  /** 是否必填（默认 false） */
  required?: boolean
  /** Element Plus Select 组件的属性（仅当 type='select' 时有效） */
  selectProps?: {
    /** 是否禁用（默认 false，即可编辑） */
    disabled?: boolean
    /** 是否只读 */
    readonly?: boolean
    /** 是否可清空 */
    clearable?: boolean
    /** 是否可搜索/输入（默认 false，即不支持输入） */
    filterable?: boolean
    /** 是否允许创建新条目（默认 false，即不支持输入） */
    allowCreate?: boolean
    /** 其他 Element Plus Select 属性 */
    [key: string]: any
  }
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

/**
 * 获取默认行数据
 * 
 * 根据列配置中的 value 生成默认行数据（与 FormSchema 的 value 属性保持一致）
 * 如果列配置中没有 value，则根据类型设置默认值：
 * - image: []
 * - text: ''（如果 required 为 true）
 * 
 * 如果提供了 createDefaultRow 函数，会先合并它的返回值（向后兼容）
 * 
 * @returns {object} 默认行数据对象
 */
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
  const cloned: any = {}
  for (const key in obj) {
    cloned[key] = deepCloneValue(obj[key])
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
  
  return {
    ...deepCloneObject(props.createDefaultRow()),
    ...defaultRowFromColumns
  }
}

const emit = defineEmits<{
  dataLoaded: [data: any[]]
  dataChanged: [data: any[]]
  rowAdded: [row: any, index: number]
}>()

// ==================== 状态 ====================
const router = useRouter()
const tagsViewStore = useTagsViewStoreWithOut()
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

const DEFAULT_IMAGE = '/src/assets/imgs/no_image.png'
const PAGE_STATE_KEY = computed(() => `IMPORT_GRID_STATE_${router.currentRoute.value.fullPath}`)

const pageReady = ref(false)
const isRestoring = ref(false)
let saveStateTimer: NodeJS.Timeout | null = null
let mountedRoutePath: string | null = null
let mountedRouteFullPath: string | null = null

const dataList = ref<any[]>([])
const originalData = ref<any[]>([])
const editingCell = ref<{ rowIndex: number; field: string } | null>(null)
const selectedRowIndex = ref<number | null>(null)
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()
const saveLoading = ref(false)
const isInputting = ref(false)
const currentInputRef = ref<HTMLInputElement | null>(null)
const blurTimerRef = ref<NodeJS.Timeout | null>(null)
const pendingInputValue = ref<{ rowIndex: number; field: string; value: string } | null>(null)
const tableRef = ref<InstanceType<typeof ElTable>>()

// ==================== ImagePlus 引用管理 ====================
/** ImagePlus 组件引用映射 */
const imagePlusRefsMap = new Map<string, InstanceType<typeof ImagePlus>>()

/** 设置 ImagePlus 组件引用 */
const setImagePlusRef = (rowIndex: number, field: string, el: any) => {
  setTimeout(() => {
    const refKey = `${rowIndex}-${field}`
    el ? imagePlusRefsMap.set(refKey, el) : imagePlusRefsMap.delete(refKey)
  }, 0)
}

/** 上传指定行的图片字段 */
const uploadRowImageField = async (rowIndex: number, field: string): Promise<void> => {
  const refKey = `${rowIndex}-${field}`
  const imagePlusRef = imagePlusRefsMap.get(refKey)
  if (imagePlusRef?.uploadPendingImages) {
    await imagePlusRef.uploadPendingImages()
  }
}

/** 上传所有行的图片字段 */
const uploadAllRowImages = async (): Promise<void> => {
  const imageColumns = props.columns.filter(col => col.type === 'image')
  if (!imageColumns.length) return
  
  for (let rowIndex = 0; rowIndex < dataList.value.length; rowIndex++) {
    for (const column of imageColumns) {
      await uploadRowImageField(rowIndex, column.field)
    }
  }
}

// ==================== 数据修改检测 ====================

/**
 * 判断数据是否被修改（默认实现）
 * 
 * 比较当前行和原始行的所有字段，如果字段值不同则返回 true
 * 对于图片字段，会比较数组长度和每个元素（包括顺序）
 * 
 * @param currentRow 当前行数据
 * @param originalRow 原始行数据
 * @returns 是否被修改
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
 * 使用 API 接口保存单条数据
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
 * 使用 API 接口获取详情数据
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
  throw new Error(res.msg || '获取详情失败')
}

/**
 * 保存数据
 * 包含：数据校验、筛选变更、图片上传、API 调用、数据刷新
 */
const save = async (): Promise<void> => {
  if (!props.saveConfig) {
    throw new Error('saveConfig is required')
  }
  
  const config = props.saveConfig
  const useApi = !!(config.addApi && config.updateApi && config.getDetailApi)
  
  if (!useApi && (!config.onSave || !config.onGetDetail)) {
    throw new Error('Either provide addApi/updateApi/getDetailApi or provide onSave/onGetDetail callbacks')
  }
  
  const data = dataList.value
  if (!data.length) {
    const msg = '没有数据需要保存。'
    prompInfoRef.value?.warn(msg)
    config.onWarn?.(msg)
    return
  }
  
  // 校验必填字段
  if (config.requiredFields?.length) {
    const errors: string[] = []
    data.forEach((row: any, index: number) => {
      config.requiredFields!.forEach(({ field, label }) => {
        const value = row[field]
        if (value === undefined || value === null || value === '') {
          errors.push(`第 ${index + 1} 行：${label} 为必填项`)
        }
      })
    })
    
    if (errors.length > 0) {
      const msg = errors.join('；')
      prompInfoRef.value?.err(msg)
      config.onError?.(msg)
      return
    }
  }
  
  // 筛选需要保存的数据
  const dataToSave: Array<{ row: any; index: number; isNew: boolean; originalRow: any }> = []
  const isDataModifiedFn = config.isDataModified || defaultIsDataModified
  
  for (let i = 0; i < data.length; i++) {
    const row = data[i]
    const originalRow = originalData.value[i]
    const isNew = !row.id
    
    if (isNew) {
      dataToSave.push({ row, index: i, isNew: true, originalRow: null })
    } else if (isDataModifiedFn(row, originalRow)) {
      dataToSave.push({ row, index: i, isNew: false, originalRow })
    }
  }
  
  if (dataToSave.length === 0) {
    const msg = '没有数据需要保存。'
    prompInfoRef.value?.warn(msg)
    config.onWarn?.(msg)
    return
  }
  
  let addCount = 0
  let updateCount = 0
  
  try {
    // ==================== 处理图片字段上传 ====================
    try {
      // 遍历所有需要保存的行，上传每行的图片字段
      const imageColumns = props.columns.filter(col => col.type === 'image')
      for (const { index } of dataToSave) {
        // 遍历所有图片类型的列
        for (const column of imageColumns) {
          await uploadRowImageField(index, column.field)
        }
      }
      
      // 上传完成后，重新获取数据（因为图片数据已更新）
      await nextTick()
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '图片上传失败'
      if (prompInfoRef.value) {
        prompInfoRef.value.err(errorMessage)
      }
      config.onError?.(errorMessage)
      return
    }
    
    // 逐行处理
    for (const { row, index, isNew } of dataToSave) {
      // 设置当前行
      setCurrentRow(index)
      
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
        
        // 提交数据（使用 API 接口或回调函数）
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
          const detail = useApi
            ? await getDetailWithApi(id)
            : await config.onGetDetail!(id)
          
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
    }
    
    // 清除编辑状态和当前行
    if (editingCell.value) {
      endEdit()
    }
    setCurrentRow(null)
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
    // 使用自定义按钮配置
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
  
  // 默认按钮配置：只有保存按钮
  const buttons: ToolbarButton[] = []
  
  // 如果提供了 saveConfig，显示保存按钮
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

// ==================== 计算属性 ====================

/** 可编辑的列配置（过滤掉隐藏和不可编辑的列） */
const editableColumns = computed(() => {
  return props.columns.filter(col => col.show !== false && col.editable !== false)
})

/** 可编辑的字段名列表 */
const editableFields = computed(() => {
  return editableColumns.value.map(col => col.field)
})

/** 当前行索引（基于编辑或选中的单元格） */
const currentRowIndex = computed(() => {
  // 优先使用编辑状态的单元格
  if (editingCell.value?.rowIndex !== undefined && editingCell.value?.rowIndex !== null) {
    return editingCell.value.rowIndex
  }
  
  // 如果没有编辑状态，使用选中的单元格所在的行索引
  return selectedRowIndex.value
})

/** 当前行颜色常量 */
const CURRENT_ROW_COLOR = 'rgb(16, 153, 104)'

/** 整行选中的索引数组（通过点击序号列选中，支持多选） */
const selectedWholeRowIndices = ref<number[]>([])

/** 最后选中的行索引（用于Shift范围选择） */
const lastSelectedRowIndex = ref<number | null>(null)

/**
 * 更新选中行的单元格样式
 * 通过 DOM 操作直接添加/移除类名
 * 支持多行选择
 */
const updateSelectedRowCells = () => {
  nextTick(() => {
    // 移除所有选中行样式
    document.querySelectorAll('.selected-row-cell').forEach(el => {
      el.classList.remove('selected-row-cell', 'selected-row-cell-first', 'selected-row-cell-last')
    })
    
    if (selectedWholeRowIndices.value.length === 0) return
    
    // 为所有选中的行添加样式
    const tbody = document.querySelector('.excel-table .el-table__body tbody')
    if (!tbody) return
    
    const rows = tbody.querySelectorAll('tr')
    
    selectedWholeRowIndices.value.forEach(rowIndex => {
      const targetRow = rows[rowIndex]
      if (!targetRow) return
      
      const cells = Array.from(targetRow.querySelectorAll('.el-table__cell'))
      
      // 跳过第一个单元格（序号列）和最后一个单元格（action列）
      cells.forEach((cell, index) => {
        if (index === 0) return // 序号列
        if (index === cells.length - 1) return // action列
        
        cell.classList.add('selected-row-cell')
        
        // 第二列（index=1）添加左边框
        if (index === 1) {
          cell.classList.add('selected-row-cell-first')
        }
        // 倒数第二列添加右边框
        if (index === cells.length - 2) {
          cell.classList.add('selected-row-cell-last')
        }
      })
    })
  })
}

/**
 * 更新选中行的索引
 * 从选中的单元格元素中提取行索引
 */
const updateSelectedRowIndex = () => {
  const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
  if (selectedCell) {
    const rowElement = selectedCell.closest('tr') as HTMLElement
    if (rowElement) {
      const tbody = rowElement.closest('tbody')
      if (tbody) {
        const rowIndex = Array.from(tbody.children).indexOf(rowElement)
        if (rowIndex !== -1) {
          selectedRowIndex.value = rowIndex
          return
        }
      }
    }
  }
  // 如果没有选中的单元格，清除选中行索引
  selectedRowIndex.value = null
}

/**
 * 设置当前行（程序内部指定）
 * @param rowIndex 行索引（从0开始），如果为 null 则清除当前行
 */
const setCurrentRow = (rowIndex: number | null) => {
  if (rowIndex === null || rowIndex < 0 || rowIndex >= dataList.value.length) {
    selectedRowIndex.value = null
    // 清除所有选中状态
    document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
      el.classList.remove('selected-cell')
    })
    return
  }
  
  selectedRowIndex.value = rowIndex
  
  // 如果当前行没有选中的单元格，选中该行的第一个可编辑单元格
  const visibleColumns = props.columns.filter(col => col.show !== false)
  const editableColumns = visibleColumns.filter(col => col.editable !== false)
  
  if (editableColumns.length > 0) {
    const firstEditableField = editableColumns[0].field
    const firstEditableColumnIndex = visibleColumns.findIndex(c => c.field === firstEditableField)
    
    if (firstEditableColumnIndex !== -1) {
      nextTick(() => {
        const tbody = document.querySelector('.el-table__body tbody')
        if (tbody) {
          const rowElement = tbody.children[rowIndex] as HTMLElement
          if (rowElement) {
            const cell = rowElement.children[firstEditableColumnIndex + 1] as HTMLElement
            if (cell) {
              // 清除其他选中状态
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              cell.classList.add('selected-cell')
            }
          }
        }
      })
    }
  }
}

// ==================== 数据加载 ====================

/**
 * 保存页面状态
 * 同时写入 tagsViewStore.pageStates（内存）和 sessionStorage（刷新恢复）
 */
const savePageState = async () => {
  try {
    // 深拷贝数据，避免保存引用
    const state = {
      dataList: JSON.parse(JSON.stringify(toRaw(dataList.value) || []))
    }
    
    // 同时保存到内存（tagsViewStore）和 sessionStorage
    const fullPath = router.currentRoute.value.fullPath
    tagsViewStore.setPageState(fullPath, state)
    sessionStorage.setItem(PAGE_STATE_KEY.value, JSON.stringify(state))
  } catch (err) {
    console.error('ImportGrid: 保存页面状态失败', err)
  }
}

/**
 * 恢复页面状态
 * 优先从 tagsViewStore.pageStates（内存）读取，如果没有则从 sessionStorage 恢复并同步到 tagsViewStore
 */
const restorePageState = () => {
  try {
    const fullPath = router.currentRoute.value.fullPath
    
    // 优先从内存（tagsViewStore）读取
    let state = tagsViewStore.getPageState(fullPath)
    
    if (state) {
      // 内存中有状态，深拷贝后返回（避免多次打开时共享引用）
      return JSON.parse(JSON.stringify(state))
    }
    
    // 内存中没有，尝试从 sessionStorage 恢复（页面刷新场景）
    const cache = sessionStorage.getItem(PAGE_STATE_KEY.value)
    if (cache) {
      state = JSON.parse(cache)
      // 同步到 tagsViewStore（内存）
      tagsViewStore.setPageState(fullPath, state)
      // 深拷贝后返回
      return JSON.parse(JSON.stringify(state))
    }
    
    return null
  } catch (err) {
    console.error('ImportGrid: 恢复页面状态失败', err)
    return null
  }
}

/**
 * 清除页面状态缓存
 * 同时清理 tagsViewStore.pageStates（内存）和 sessionStorage
 * @param stateKey - 可选的状态 key，如果不提供则使用默认的 PAGE_STATE_KEY
 * @param fullPath - 可选的路由完整路径，如果不提供则使用当前路由的 fullPath
 */
const clearPageState = (stateKey?: string, fullPath?: string) => {
  try {
    const keyToRemove = stateKey || PAGE_STATE_KEY.value
    const pathToClear = fullPath || router.currentRoute.value.fullPath
    
    // 同时清理内存和 sessionStorage
    tagsViewStore.clearPageState(pathToClear)
    sessionStorage.removeItem(keyToRemove)
  } catch (err) {
    console.error('ImportGrid: 清除页面状态失败', err)
  }
}

/**
 * 从 sessionStorage 加载数据（从父窗口传入的数据）
 * 
 * 工作流程：
 * 1. 从 sessionStorage 读取数据（由父窗口通过 persistImportPayload 保存）
 * 2. 使用 mapRowData 转换数据格式
 * 3. 合并默认行数据，确保所有字段都有默认值
 * 4. 加载完成后清除 sessionStorage，避免重复加载
 * 5. 如果没有数据，创建一行默认数据
 * 
 * @returns {boolean} 是否成功加载了数据
 */
const loadDataFromStorage = () => {
  try {
    const cache = sessionStorage.getItem(props.storageKey)
    if (cache) {
      const payload = JSON.parse(cache)
      if (Array.isArray(payload) && payload.length > 0) {
        // 合并默认行数据和传入数据
        // 每行都需要创建独立的 defaultRow 以避免引用共享
        dataList.value = payload.map(row => {
          const defaultRow = getDefaultRow() // 每行独立创建
          const mappedRow = props.mapRowData(row)
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
        // 显示准备就绪提示
        if (prompInfoRef.value) {
          prompInfoRef.value.ready()
        }
        // 清除 sessionStorage，避免重复加载
        sessionStorage.removeItem(props.storageKey)
        return true
      }
    }
  } catch (err) {
    console.error('加载导入数据失败：', err)
  }
  
  // 如果没有数据，创建一行默认数据
  dataList.value = [getDefaultRow()]
  // 初始化原始数据
  originalData.value = JSON.parse(JSON.stringify(dataList.value))
  emit('dataLoaded', dataList.value)
  // 显示准备就绪提示
  if (prompInfoRef.value) {
    prompInfoRef.value.ready()
  }
  return false
}

/**
 * 监听数据变化
 */
watch(
  () => dataList.value,
  (newData) => {
    emit('dataChanged', newData)
    
    // 自动保存状态（debounce）
    if (pageReady.value && !isRestoring.value) {
      if (saveStateTimer) {
        clearTimeout(saveStateTimer)
      }
      saveStateTimer = setTimeout(async () => {
        await savePageState()
      }, 500)
    }
    
    // 如果正在编辑，确保输入框保持焦点
    // 使用 flush: 'post' 确保在 DOM 更新后执行
    if (editingCell.value && isInputting.value) {
      const editing = editingCell.value
      if (editing && isEditing(editing.rowIndex, editing.field)) {
        const { rowIndex, field } = editing
        // 使用 requestAnimationFrame 确保浏览器完成渲染
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
            if (cellInput) {
              const inputElement = cellInput.querySelector('input') as HTMLInputElement
              if (inputElement) {
                // 标记正在输入，防止 blur 事件误触发
                isInputting.value = true
                // 恢复焦点
                if (document.activeElement !== inputElement) {
                  inputElement.focus()
                  // 将光标移到末尾（number 类型不支持 setSelectionRange）
                  if (inputElement.type !== 'number') {
                    const len = inputElement.value.length
                    inputElement.setSelectionRange(len, len)
                  }
                }
                currentInputRef.value = inputElement
                // 延迟清除标记
                setTimeout(() => {
                  isInputting.value = false
                }, 200)
              }
            }
          })
        })
      }
    }
  },
  { deep: true, flush: 'post' }
)

// 监听编辑状态变化，确保输入框渲染后设置值
watch(
  editingCell,
  (newVal) => {
    if (newVal && pendingInputValue.value) {
      // 等待Vue重新渲染
      nextTick(() => {
        nextTick(() => {
          // data-cell-key 是直接设置在 input 元素上的，所以找到的就是 input 元素本身
          const elInput = document.querySelector(`[data-cell-key="${newVal.rowIndex}-${newVal.field}"]`) as HTMLInputElement
          if (elInput && pendingInputValue.value) {
            elInput.value = pendingInputValue.value.value
            dataList.value[newVal.rowIndex][newVal.field] = pendingInputValue.value.value
            elInput.focus()
            // number 类型不支持 setSelectionRange
            if (elInput.type !== 'number') {
              const len = elInput.value.length
              elInput.setSelectionRange(len, len)
            }
            currentInputRef.value = elInput
            setTimeout(() => {
              isInputting.value = false
              pendingInputValue.value = null
            }, 300)
          }
        })
      })
    }
  },
  { immediate: false }
)

/**
 * 检查单元格是否正在编辑
 */
const isEditing = (rowIndex: number, field: string) => {
  return editingCell.value?.rowIndex === rowIndex && editingCell.value?.field === field
}

/**
 * 开始编辑单元格
 */
const startEdit = (rowIndex: number, field: string) => {
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) {
    return
  }
  
  // 标记正在输入，防止blur事件误触发
  isInputting.value = true
  
  editingCell.value = { rowIndex, field }
  
  // 延迟聚焦，确保输入框已经渲染
  nextTick(() => {
    nextTick(() => {
      focusInput(rowIndex, field, false)
      // 延迟清除输入标记
      setTimeout(() => {
        isInputting.value = false
      }, 100)
    })
  })
}

/**
 * 结束编辑
 */
const endEdit = () => {
  // 清除blur定时器
  if (blurTimerRef.value) {
    clearTimeout(blurTimerRef.value)
    blurTimerRef.value = null
  }
  
  // 移除选中状态和编辑状态
  document.querySelectorAll('.el-table__cell.selected-cell, .el-table__cell.editing-cell').forEach(el => {
    el.classList.remove('selected-cell', 'editing-cell')
  })
  
  editingCell.value = null
  currentInputRef.value = null
  isInputting.value = false
  selectedRowIndex.value = null // 清除选中行索引
}

/**
 * 聚焦输入框
 */
const focusInput = (rowIndex: number, field: string, shouldSelect = true) => {
  // 使用双重 nextTick 和 requestAnimationFrame 确保 DOM 完全渲染
  nextTick(() => {
    nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          const element = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
          
          if (!element) {
            return
          }
          
          // data-cell-key 可能设置在 Element Plus 组件容器上，也可能直接设置在 input 元素上
          let elInput: HTMLInputElement | null = null
          
          // 如果找到的元素本身就是 input 或 textarea，直接使用
          if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            elInput = element as HTMLInputElement
          } else {
            // 否则查找内部的 input 或 textarea
            // 对于 ElInputNumber，需要查找 .el-input-number__input input
            elInput = element.querySelector('input, textarea, .el-input-number__input input') as HTMLInputElement
            // 如果还是找不到，尝试查找更深层的input
            if (!elInput) {
              elInput = element.querySelector('.el-input-number input') as HTMLInputElement
            }
          }
          
          if (elInput) {
            elInput.focus()
            // 检查 input 类型，number 类型不支持 setSelectionRange 和 select
            const inputType = elInput.type
            if (inputType !== 'number') {
              // 只有在没有初始值的情况下才选中所有文本
              if (shouldSelect) {
                elInput.select()
              } else {
                // 如果有初始值，将光标移到末尾
                const len = elInput.value.length
                elInput.setSelectionRange(len, len)
              }
            }
          }
          
          // 给父单元格添加选中类和编辑类
          const cell = element.closest('.el-table__cell') as HTMLElement
          if (cell) {
            // 移除其他单元格的选中状态和编辑状态
            document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
              el.classList.remove('selected-cell', 'editing-cell')
            })
            cell.classList.add('selected-cell', 'editing-cell')
            updateSelectedRowIndex()
          }
        })
      })
    })
  })
}

/**
 * 处理单元格点击
 */
const handleCellClick = (row: any, column: any, cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = dataList.value.indexOf(row)
  const field = column.property || column.field
  
  // 处理序号列的点击（序号列没有 field，type 为 'index'）
  if (!field && column.type === 'index') {
    // 选中行时，清除单元格选中状态（两者互斥）
    document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
      el.classList.remove('selected-cell')
    })
    
    // 如果有编辑状态，退出编辑
    if (editingCell.value) {
      endEdit()
    }
    
    // 判断是否按住了 Ctrl 或 Shift 键
    const isCtrlPressed = event?.ctrlKey || event?.metaKey // metaKey 为 Mac 的 Cmd 键
    const isShiftPressed = event?.shiftKey
    
    if (isShiftPressed && lastSelectedRowIndex.value !== null) {
      // Shift + 点击：选择范围内的所有行
      const start = Math.min(lastSelectedRowIndex.value, rowIndex)
      const end = Math.max(lastSelectedRowIndex.value, rowIndex)
      const rangeIndices: number[] = []
      for (let i = start; i <= end; i++) {
        rangeIndices.push(i)
      }
      selectedWholeRowIndices.value = rangeIndices
      selectedRowIndex.value = rowIndex
    } else if (isCtrlPressed) {
      // Ctrl + 点击：切换该行的选中状态
      const index = selectedWholeRowIndices.value.indexOf(rowIndex)
      if (index > -1) {
        // 已选中，取消选中
        selectedWholeRowIndices.value.splice(index, 1)
        if (selectedWholeRowIndices.value.length === 0) {
          selectedRowIndex.value = null
          lastSelectedRowIndex.value = null
        } else {
          selectedRowIndex.value = selectedWholeRowIndices.value[selectedWholeRowIndices.value.length - 1]
        }
      } else {
        // 未选中，添加到选中列表
        selectedWholeRowIndices.value.push(rowIndex)
        selectedRowIndex.value = rowIndex
        lastSelectedRowIndex.value = rowIndex
      }
    } else {
      // 普通点击：单选该行
      if (selectedWholeRowIndices.value.length === 1 && selectedWholeRowIndices.value[0] === rowIndex) {
        // 点击已选中的行，取消选中
        selectedWholeRowIndices.value = []
        selectedRowIndex.value = null
        lastSelectedRowIndex.value = null
      } else {
        // 选中该行
        selectedWholeRowIndices.value = [rowIndex]
        selectedRowIndex.value = rowIndex
        lastSelectedRowIndex.value = rowIndex
      }
    }
    
    // 更新选中行的样式
    updateSelectedRowCells()
    return
  }
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  // image 类型列始终处于编辑模式，不需要进入编辑状态
  if (col && col.type === 'image') {
    return
  }
  
  // 如果点击的是正在编辑的单元格，不处理（保持编辑状态）
  if (isEditing(rowIndex, field)) {
    return
  }
  
  // 如果点击的是另一个单元格，先退出当前编辑模式
  if (editingCell.value) {
    endEdit()
  }
  
  // 单击时只获得焦点，不进入编辑模式
  // 清除其他单元格的选中状态
  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
    el.classList.remove('selected-cell')
  })
  
  // 单元格被选中时，取消选中行（两者互斥）
  if (selectedWholeRowIndices.value.length > 0) {
    selectedWholeRowIndices.value = []
    lastSelectedRowIndex.value = null
    updateSelectedRowCells()
  }
  
  // 添加当前单元格的选中状态
  // 使用 nextTick 确保 DOM 已更新
  nextTick(() => {
    // 通过事件目标查找单元格
    if (event && event.target) {
      const targetCell = (event.target as HTMLElement).closest('.el-table__cell') as HTMLElement
      if (targetCell) {
        targetCell.classList.add('selected-cell')
        updateSelectedRowIndex()
        return
      }
    }
    
    // 如果事件目标不存在，通过 DOM 查找
    const visibleColumns = props.columns.filter(col => col.show !== false)
    const columnIndex = visibleColumns.findIndex(c => c.field === field)
    if (columnIndex !== -1) {
      // 跳过序号列，所以 columnIndex + 2
      const cellElement = document.querySelector(
        `.el-table__body tbody tr:nth-child(${rowIndex + 1}) .el-table__cell:nth-child(${columnIndex + 2})`
      ) as HTMLElement
      if (cellElement) {
        cellElement.classList.add('selected-cell')
        updateSelectedRowIndex()
      }
    }
  })
}

/**
 * 处理单元格双击
 */
const handleCellDblclick = (row: any, column: any, cell?: HTMLElement, event?: MouseEvent) => {
  const rowIndex = dataList.value.indexOf(row)
  const field = column.property || column.field
  
  if (rowIndex === -1 || !field) return
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  // image 类型列始终处于编辑模式，不需要进入编辑状态
  if (col && col.type === 'image') {
    return
  }
  
  // 双击时获得焦点并进入编辑模式
  // 先设置选中状态
  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
    el.classList.remove('selected-cell')
  })
  
  // 单元格被选中时，取消选中行（两者互斥）
  if (selectedWholeRowIndices.value.length > 0) {
    selectedWholeRowIndices.value = []
    lastSelectedRowIndex.value = null
    updateSelectedRowCells()
  }
  
  if (cell) {
    cell.classList.add('selected-cell')
    updateSelectedRowIndex()
  }
  
  // 然后进入编辑模式
  startEdit(rowIndex, field)
}

/**
 * 处理图片单元格点击
 */
/**
 * 获取 ImagePlus 组件的唯一key
 */
const getImagePlusKey = (rowIndex: number, field: string) => {
  const row = dataList.value[rowIndex]
  const rowId = row?.id || `temp-${rowIndex}`
  return `image-${rowId}-${field}`
}

/**
 * 处理 ImagePlus 组件的值更新
 * 创建新行对象避免引用共享
 */
const handleImageUpdate = (rowIndex: number, field: string, val: any[]) => {
  const newValue = Array.isArray(val) ? [...val] : val
  
  dataList.value = dataList.value.map((row, idx) => {
    if (idx === rowIndex) {
      return { ...row, [field]: newValue }
    }
    return row
  })
}

const handleImageCellClick = (rowIndex: number, field: string, event: MouseEvent) => {
  // 如果点击的是正在编辑的其他单元格，先退出编辑模式
  if (editingCell.value) {
    endEdit()
  }
  
  // 清除其他单元格的选中状态
  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
    el.classList.remove('selected-cell')
  })
  
  // 单元格被选中时，取消选中行（两者互斥）
  if (selectedWholeRowIndices.value.length > 0) {
    selectedWholeRowIndices.value = []
    lastSelectedRowIndex.value = null
    updateSelectedRowCells()
  }
  
  // 添加当前图片单元格的选中状态
  nextTick(() => {
    // 通过事件目标查找单元格
    const targetCell = (event.target as HTMLElement).closest('.el-table__cell') as HTMLElement
    if (targetCell) {
      targetCell.classList.add('selected-cell')
      updateSelectedRowIndex()
    }
  })
}

/**
 * 处理键盘输入（直接进入编辑）
 */
const handleCellKeydown = (event: KeyboardEvent, row: any, column: any) => {
  const rowIndex = dataList.value.indexOf(row)
  const field = column.property || column.field
  
  // 忽略 Ctrl+C 和 Ctrl+V，让全局事件处理
  if (event.ctrlKey || event.metaKey) {
    if (event.key === 'c' || event.key === 'C' || event.key === 'v' || event.key === 'V') {
      return
    }
  }
  
  if (rowIndex === -1 || !field) {
    return
  }
  
  const col = props.columns.find(c => c.field === field)
  if (col && col.editable === false) return
  
  // image 类型列始终处于编辑模式，不需要进入编辑状态
  if (col && col.type === 'image') {
    return
  }
  
  // 如果已经在编辑状态，不处理（让输入框自己处理）
  if (isEditing(rowIndex, field)) {
    return
  }
  
  // 如果按下的是可打印字符，直接进入编辑
  if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    event.preventDefault()
    event.stopPropagation()
    
    // 清除之前的blur定时器
    if (blurTimerRef.value) {
      clearTimeout(blurTimerRef.value)
      blurTimerRef.value = null
    }
    
    // 标记正在输入（提前标记，防止blur事件误触发）
    isInputting.value = true
    
    // 直接设置第一个字符（Excel行为：输入时替换整个内容）
    dataList.value[rowIndex][field] = event.key
    
    // 设置编辑状态（这会触发Vue重新渲染）
    editingCell.value = { rowIndex, field }
    
    // 确保输入框渲染后获得焦点
    nextTick(() => {
      nextTick(() => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            focusInput(rowIndex, field, false)
            setTimeout(() => {
              isInputting.value = false
            }, 300)
          })
        })
      })
    })
  }
  
  // Delete 或 Backspace 删除单元格内容
  if ((event.key === 'Delete' || event.key === 'Backspace') && !editingCell.value) {
    event.preventDefault()
    const col = props.columns.find(c => c.field === field)
    dataList.value[rowIndex][field] = col?.type === 'number' ? null : ''
  }
  
  // F2 进入编辑
  if (event.key === 'F2') {
    event.preventDefault()
    startEdit(rowIndex, field)
  }
}

/**
 * 处理输入框键盘事件
 */
const handleInputKeydown = (event: KeyboardEvent, rowIndex: number, field: string) => {
  const col = props.columns.find(c => c.field === field)
  const currentIndex = editableFields.value.indexOf(field)
  
  // Tab: 行为与非编辑模式一致（向右移动到下一列，但不进入编辑模式）
  if (event.key === 'Tab') {
    event.preventDefault()
    endEdit()
    
    const visibleColumns = props.columns.filter(col => col.show !== false)
    
    if (event.shiftKey) {
      // Shift+Tab: 向左移动
      if (currentIndex > 0) {
        // 跳转到上一列（不进入编辑模式）
        const prevField = editableFields.value[currentIndex - 1]
        const prevColumn = visibleColumns.find(col => col.field === prevField)
        if (prevColumn) {
          const prevColumnIndex = visibleColumns.indexOf(prevColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const rowElement = tbody.children[rowIndex] as HTMLElement
            if (rowElement) {
              const prevCell = rowElement.children[prevColumnIndex + 1] as HTMLElement
              if (prevCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                prevCell.classList.add('selected-cell')
                updateSelectedRowIndex()
              }
            }
          }
        }
      } else if (rowIndex > 0) {
        // 如果已是行首，则跳转到上一行最后一列
        const prevField = editableFields.value[editableFields.value.length - 1]
        const prevColumn = visibleColumns.find(col => col.field === prevField)
        if (prevColumn) {
          const prevColumnIndex = visibleColumns.indexOf(prevColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const prevRow = tbody.children[rowIndex - 1] as HTMLElement
            if (prevRow) {
              const prevCell = prevRow.children[prevColumnIndex + 1] as HTMLElement
              if (prevCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                prevCell.classList.add('selected-cell')
                updateSelectedRowIndex()
              }
            }
          }
        }
      }
    } else {
      // Tab: 向右移动到下一列（不进入编辑模式）
      if (currentIndex < editableFields.value.length - 1) {
        // 如果还有下一列，跳转到下一列
        const nextField = editableFields.value[currentIndex + 1]
        const nextColumn = visibleColumns.find(col => col.field === nextField)
        if (nextColumn) {
          const nextColumnIndex = visibleColumns.indexOf(nextColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const rowElement = tbody.children[rowIndex] as HTMLElement
            if (rowElement) {
              const nextCell = rowElement.children[nextColumnIndex + 1] as HTMLElement
              if (nextCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                nextCell.classList.add('selected-cell')
                updateSelectedRowIndex()
              }
            }
          }
        }
      } else if (rowIndex < dataList.value.length - 1) {
        // 如果已是行尾，则跳转到下一行第1列
        const firstField = editableFields.value[0]
        const firstColumn = visibleColumns.find(col => col.field === firstField)
        if (firstColumn) {
          const firstColumnIndex = visibleColumns.indexOf(firstColumn)
          const tbody = document.querySelector('.el-table__body tbody')
          if (tbody) {
            const nextRow = tbody.children[rowIndex + 1] as HTMLElement
            if (nextRow) {
              const firstCell = nextRow.children[firstColumnIndex + 1] as HTMLElement
              if (firstCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                firstCell.classList.add('selected-cell')
                updateSelectedRowIndex()
              }
            }
          }
        }
      } else {
        // 如果已是最后1行，则新增1行，并跳转到该行第1列
        const newRow = { ...getDefaultRow() }
        dataList.value.push(newRow)
        nextTick(() => {
          const firstField = editableFields.value[0]
          const firstColumn = visibleColumns.find(col => col.field === firstField)
          if (firstColumn) {
            const firstColumnIndex = visibleColumns.indexOf(firstColumn)
            const tbody = document.querySelector('.el-table__body tbody')
            if (tbody) {
              const newRowElement = tbody.children[dataList.value.length - 1] as HTMLElement
              if (newRowElement) {
                const firstCell = newRowElement.children[firstColumnIndex + 1] as HTMLElement
                if (firstCell) {
                  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                    el.classList.remove('selected-cell')
                  })
                  firstCell.classList.add('selected-cell')
                  updateSelectedRowIndex()
                }
              }
            }
          }
        })
      }
    }
  }
  
  // Enter: 退出编辑，但焦点保留在当前单元格
  if (event.key === 'Enter') {
    event.preventDefault()
    endEdit()
    // 保持当前单元格的选中状态
    nextTick(() => {
      const visibleColumns = props.columns.filter(col => col.show !== false)
      const columnIndex = visibleColumns.findIndex(c => c.field === field)
      if (columnIndex !== -1) {
        const tbody = document.querySelector('.el-table__body tbody')
        if (tbody) {
          const rowElement = tbody.children[rowIndex] as HTMLElement
          if (rowElement) {
            const cell = rowElement.children[columnIndex + 1] as HTMLElement
            if (cell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              cell.classList.add('selected-cell')
              updateSelectedRowIndex()
            }
          }
        }
      }
    })
  }
  
  // Escape: 退出编辑，但焦点保留在当前单元格（与 Enter 行为一致）
  if (event.key === 'Escape') {
    event.preventDefault()
    endEdit()
    // 保持当前单元格的选中状态
    nextTick(() => {
      const visibleColumns = props.columns.filter(col => col.show !== false)
      const columnIndex = visibleColumns.findIndex(c => c.field === field)
      if (columnIndex !== -1) {
        const tbody = document.querySelector('.el-table__body tbody')
        if (tbody) {
          const rowElement = tbody.children[rowIndex] as HTMLElement
          if (rowElement) {
            const cell = rowElement.children[columnIndex + 1] as HTMLElement
            if (cell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              cell.classList.add('selected-cell')
              updateSelectedRowIndex()
            }
          }
        }
      }
    })
  }
  
  // 方向键导航
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
    if (col?.type === 'select' || col?.type === 'text' || col?.type === 'number') {
      // 下拉框、文本框、数字框时，方向键用于编辑框内的光标操作，不阻止
      return
    }
    event.preventDefault()
    endEdit()
    
    let newRowIndex = rowIndex
    let newFieldIndex = currentIndex
    
    if (event.key === 'ArrowUp' && rowIndex > 0) {
      newRowIndex = rowIndex - 1
    } else if (event.key === 'ArrowDown') {
      if (rowIndex < dataList.value.length - 1) {
        newRowIndex = rowIndex + 1
      } else {
        // 添加新行
        const newRow = { ...getDefaultRow() }
        dataList.value.push(newRow)
        newRowIndex = dataList.value.length - 1
      }
    } else if (event.key === 'ArrowLeft' && currentIndex > 0) {
      newFieldIndex = currentIndex - 1
    } else if (event.key === 'ArrowRight' && currentIndex < editableFields.value.length - 1) {
      newFieldIndex = currentIndex + 1
    }
    
    startEdit(newRowIndex, editableFields.value[newFieldIndex])
  }
}

/**
 * 获取当前选中的单元格信息
 */
const getSelectedCellInfo = () => {
  const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
  if (!selectedCell) return null
  
  const rowElement = selectedCell.closest('tr')
  if (!rowElement) return null
  
  const tbody = rowElement.parentElement
  if (!tbody) return null
  
  const rowIndex = Array.from(tbody.children).indexOf(rowElement)
  if (rowIndex === -1) return null
  
  const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
  if (cellIndex === -1) return null
  
  // 跳过序号列
  const columnIndex = cellIndex - 1
  if (columnIndex < 0) return null
  
  const visibleColumns = props.columns.filter(col => col.show !== false)
  if (columnIndex >= visibleColumns.length) return null
  
  const column = visibleColumns[columnIndex]
  return { rowIndex, field: column.field, column }
}

/**
 * 处理原图片数组的删除标记
 * 在粘贴新图片之前，需要将原图片标记为删除
 */
const markOriginalImagesAsDeleted = (imageArray: any[]): any[] => {
  if (!Array.isArray(imageArray)) {
    return []
  }
  
  return imageArray
    .map(item => {
      // 如果是对象：直接删除（还没保存到后台，不需要保留）
      if (typeof item === 'object' && item !== null) {
        return null
      }
      
      // 如果是字符串：处理标记
      if (typeof item === 'string') {
        if (item.includes('?original') || item.includes('?add')) {
          // original 或 add → delete（标记为删除）
          return item.replace(/\?(original|add)/, '?delete')
        } else if (item.includes('?delete')) {
          // delete → 保持不变
          return item
        } else {
          // 没有标记的字符串（默认是 original），改为 delete
          return item + '?delete'
        }
      }
      
      return item
    })
    .filter(item => item !== null) // 过滤掉对象元素
}

/**
 * 处理图片数组的粘贴转换
 * 将复制的图片数组转换为可粘贴的格式
 * 注意：只复制粘贴字符串格式的图片 URL，不复制对象（内存预览）
 */
const processImageArrayForPaste = (imageArray: any[]): any[] => {
  if (!Array.isArray(imageArray)) {
    return []
  }
  
  return imageArray
    .filter(item => {
      // 过滤掉对象格式（内存预览），只保留字符串格式的图片 URL
      // 因为内存预览 URL 在其他行无法访问
      if (typeof item === 'object' && item !== null) {
        return false
      }
      // 过滤掉删除标记的图片
      if (typeof item === 'string' && item.includes('?delete')) {
        return false
      }
      return typeof item === 'string'
    })
    .map(item => {
      // 处理字符串格式的图片标记
      if (typeof item === 'string') {
        // original → add（这样后台会新增这个图片）
        if (item.includes('?original')) {
          return item.replace('?original', '?add')
        }
        // add → 保持不变（后台会新增）
        if (item.includes('?add')) {
          return item
        }
        // 没有标记的，添加 ?add 标记
        return item + '?add'
      }
      return item
    })
    .filter(Boolean) // 过滤掉空值
}

/**
 * 处理复制（Ctrl+C）
 */
const handleCopy = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    const { rowIndex, field } = editingCell.value
    const col = props.columns.find(c => c.field === field)
    const value = dataList.value[rowIndex]?.[field]
    
    if (value !== undefined && value !== null) {
      event.preventDefault()
      let copyValue = ''
      let copyData = value
      
      // 根据列类型处理显示值和复制数据
      if (col?.type === 'image') {
        // 图片类型：只复制字符串格式的图片 URL，过滤掉对象（内存预览）
        const imageArray = Array.isArray(value) ? value : []
        const stringImages = imageArray.filter((item: any) => typeof item === 'string')
        copyData = stringImages
        copyValue = `${stringImages.length} image(s)`
      } else {
        copyValue = String(value)
      }
      
      // 使用 clipboardData 设置剪贴板
      if (event.clipboardData) {
        // text/plain: 用户可见的文本
        event.clipboardData.setData('text/plain', copyValue)
        // 自定义格式：包含类型和值的元数据
        const cellData = {
          type: col?.type || 'text',
          value: copyData,
          field: field
        }
        event.clipboardData.setData('application/x-importgrid-cell', JSON.stringify(cellData))
      }
    }
    return
  }
  
  // 非编辑模式：从选中的单元格复制
  const cellInfo = getSelectedCellInfo()
  if (cellInfo) {
    event.preventDefault()
    const { rowIndex, field, column } = cellInfo
    const value = dataList.value[rowIndex]?.[field]
    
    let copyValue = ''
    let copyData = value
    
    if (value !== undefined && value !== null) {
      // 根据列类型处理显示值和复制数据
      if (column.type === 'image') {
        // 图片类型：只复制字符串格式的图片 URL，过滤掉对象（内存预览）
        const imageArray = Array.isArray(value) ? value : []
        const stringImages = imageArray.filter((item: any) => typeof item === 'string')
        copyData = stringImages
        copyValue = `${stringImages.length} image(s)`
      } else {
        // 其他类型：拷贝原始值（字符串形式）
        copyValue = String(value)
      }
    }
    
    // 使用 clipboardData 设置剪贴板
    if (event.clipboardData) {
      // text/plain: 用户可见的文本
      event.clipboardData.setData('text/plain', copyValue)
      // 自定义格式：包含类型和值的元数据
      const cellData = {
        type: column.type || 'text',
        value: copyData,
        field: field
      }
      event.clipboardData.setData('application/x-importgrid-cell', JSON.stringify(cellData))
    }
  }
}

/**
 * 处理粘贴（Ctrl+V）
 */
const handlePaste = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    event.preventDefault()
    const { rowIndex, field } = editingCell.value
    const targetCol = props.columns.find(c => c.field === field)
    
    if (!targetCol || targetCol.editable === false) {
      return
    }
    
    // 尝试获取自定义格式的数据
    const customData = event.clipboardData?.getData('application/x-importgrid-cell')
    let cellData: any = null
    
    if (customData) {
      try {
        cellData = JSON.parse(customData)
      } catch (e) {
        // 解析失败，使用普通文本
      }
    }
    
    // 如果有自定义数据且类型匹配
    if (cellData && cellData.type === targetCol.type) {
      // 类型匹配，直接复制值
      if (targetCol.type === 'image') {
        // 图片类型：特殊处理数组
        // 1. 先标记原图片为删除
        const deletedImages = markOriginalImagesAsDeleted(dataList.value[rowIndex][field])
        // 2. 处理要粘贴的新图片（确保深拷贝）
        const newImages = processImageArrayForPaste(cellData.value)
        // 3. 合并删除标记的原图片和新图片（创建全新数组）
        const mergedImages = [...deletedImages, ...newImages]
        
        // 4. 更新行数据（创建新行对象以避免引用共享）
        dataList.value = dataList.value.map((row, idx) => {
          if (idx === rowIndex) {
            return { ...row, [field]: mergedImages }
          }
          return row
        })
      } else {
        // 非图片类型，也创建新行对象
        dataList.value = dataList.value.map((row, idx) => {
          if (idx === rowIndex) {
            return { ...row, [field]: cellData.value }
          }
          return row
        })
      }
    } else if (cellData && cellData.type !== targetCol.type) {
      // 类型不匹配，忽略粘贴
      console.log('类型不匹配，忽略粘贴操作')
      return
    } else {
      // 没有自定义数据，使用普通文本粘贴（兼容外部复制）
      const pasteData = event.clipboardData?.getData('text/plain') || ''
      if (pasteData) {
        if (targetCol.type === 'number') {
          const num = Number(pasteData)
          if (!isNaN(num)) {
            dataList.value[rowIndex][field] = num
          }
        } else if (targetCol.type === 'image') {
          // 图片类型不支持从普通文本粘贴
          console.log('图片列不支持从文本粘贴')
        } else {
          dataList.value[rowIndex][field] = pasteData
        }
      }
    }
    return
  }
  
  // 非编辑模式：粘贴到选中的单元格
  const cellInfo = getSelectedCellInfo()
  if (cellInfo) {
    event.preventDefault()
    const { rowIndex, field, column } = cellInfo
    
    // 检查列是否可编辑
    if (column.editable === false) {
      return
    }
    
    // 尝试获取自定义格式的数据
    const customData = event.clipboardData?.getData('application/x-importgrid-cell')
    let cellData: any = null
    
    if (customData) {
      try {
        cellData = JSON.parse(customData)
      } catch (e) {
        // 解析失败，使用普通文本
      }
    }
    
    // 如果有自定义数据且类型匹配
    if (cellData && cellData.type === column.type) {
      // 类型匹配，直接复制值
      if (column.type === 'image') {
        // 图片类型：特殊处理数组
        // 1. 先标记原图片为删除
        const deletedImages = markOriginalImagesAsDeleted(dataList.value[rowIndex][field])
        // 2. 处理要粘贴的新图片
        const newImages = processImageArrayForPaste(cellData.value)
        // 3. 合并删除标记的原图片和新图片
        dataList.value[rowIndex][field] = [...deletedImages, ...newImages]
      } else {
        dataList.value[rowIndex][field] = cellData.value
      }
    } else if (cellData && cellData.type !== column.type) {
      // 类型不匹配，忽略粘贴
      console.log('类型不匹配，忽略粘贴操作')
      return
    } else {
      // 没有自定义数据，使用普通文本粘贴（兼容外部复制）
      const pasteData = event.clipboardData?.getData('text/plain') || ''
      if (pasteData !== undefined && pasteData !== null && pasteData !== '') {
        if (column.type === 'number') {
          const num = Number(pasteData)
          if (!isNaN(num)) {
            dataList.value[rowIndex][field] = num
          }
        } else if (column.type === 'select' && column.options) {
          // 对于 select 类型，尝试通过 label 或 value 匹配
          const option = column.options.find(opt => opt.label === pasteData || String(opt.value) === pasteData)
          if (option) {
            dataList.value[rowIndex][field] = option.value
          } else {
            // 如果没有匹配的选项，直接使用粘贴的值
            dataList.value[rowIndex][field] = pasteData
          }
        } else if (column.type === 'image') {
          // 图片类型不支持从普通文本粘贴
          console.log('图片列不支持从文本粘贴')
        } else {
          dataList.value[rowIndex][field] = pasteData
        }
      } else {
        // 如果粘贴数据为空，清空单元格
        if (column.type === 'image') {
          dataList.value[rowIndex][field] = []
        } else if (column.type === 'number') {
          dataList.value[rowIndex][field] = null
        } else {
          dataList.value[rowIndex][field] = ''
        }
      }
    }
  }
}

/**
 * 格式化单元格显示值
 */
const formatCellValue = (value: any, column: ImportGridColumn) => {
  if (value === null || value === undefined) return ''
  
  if (column.type === 'select' && column.options) {
    const option = column.options.find(opt => opt.value === value)
    return option ? option.label : value
  }
  
  // image 类型不显示文本，由专门的组件处理
  if (column.type === 'image') {
    return ''
  }
  
  return String(value)
}

/**
 * 处理图片上传前的验证
 */
const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const isImage = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
  const isLtSize = rawFile.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('上传图片必须是 JPG/GIF/PNG/ 格式!')
  }
  if (!isLtSize) {
    ElMessage.error('上传图片大小不能超过2MB!')
  }
  return isImage && isLtSize
}

/**
 * 处理图片文件变化
 */
const handleImageFileChange = (file: any, rowIndex: number, field: string) => {
  const row = dataList.value[rowIndex]
  if (!row) return
  
  const imageField = field
  const imageDisplayField = `${field}_display`
  
  // 确保字段存在
  if (!row[imageField]) {
    row[imageField] = []
  }
  if (!row[imageDisplayField]) {
    row[imageDisplayField] = []
  }
  
  if (file.raw) {
    const exists = row[imageField].some((item: any) => {
      if (Array.isArray(item)) {
        return item[2] === file.name
      }
      return false
    })
    
    if (!exists) {
      const previewUrl = URL.createObjectURL(file.raw)
      row[imageDisplayField].push(previewUrl)
      row[imageField].push([previewUrl, 'add', file.name, file])
      // 图片上传后，修复 SVG 图标尺寸
      nextTick(() => fixSvgIconSize())
    }
  }
}

/**
 * 处理删除图片
 */
const handleRemoveImage = (index: number, rowIndex: number, field: string) => {
  const row = dataList.value[rowIndex]
  if (!row) return
  
  const imageField = field
  const imageDisplayField = `${field}_display`
  
  if (Array.isArray(row[imageField][index])) {
    // 新上传的图片，直接删除
    row[imageDisplayField].splice(index, 1)
    row[imageField].splice(index, 1)
    // 删除图片后，修复 SVG 图标尺寸
    nextTick(() => fixSvgIconSize())
  } else {
    // 已存在的图片，标记为删除
    const imageUrl = row[imageField][index]
    if (typeof imageUrl === 'string') {
      const [path] = imageUrl.split('?')
      row[imageDisplayField][index] = `${path}?delete`
      row[imageField][index] = `${path}?delete`
    }
  }
}

/**
 * 处理图片拖拽排序
 */
const dragIndex = ref<Record<string, number>>({})
const dragOverIndex = ref<Record<string, number>>({})

const handleDragStart = (index: number, rowIndex: number, field: string, event: DragEvent) => {
  const key = `${rowIndex}-${field}`
  dragIndex.value[key] = index
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer!.setData('text/plain', index.toString())
  setTimeout(() => {
    (event.target as HTMLElement).classList.add('dragging')
  }, 0)
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
}

const handleDragEnter = (index: number, rowIndex: number, field: string, event: DragEvent) => {
  event.preventDefault()
  const key = `${rowIndex}-${field}`
  dragOverIndex.value[key] = index
}

const handleDragLeave = (_rowIndex: number, _field: string, event: DragEvent) => {
  if (!(event.currentTarget as HTMLElement).contains(event.relatedTarget as HTMLElement)) {
    const key = `${_rowIndex}-${_field}`
    dragOverIndex.value[key] = -1
  }
}

const handleDrop = (targetIndex: number, rowIndex: number, field: string, event: DragEvent) => {
  event.preventDefault()
  const sourceIndex = parseInt(event.dataTransfer!.getData('text/plain'))
  const key = `${rowIndex}-${field}`
  
  if (sourceIndex !== targetIndex && sourceIndex >= 0 && targetIndex >= 0) {
    const row = dataList.value[rowIndex]
    if (!row) return
    
    const imageField = field
    const imageDisplayField = `${field}_display`
    
    const images_display = [...row[imageDisplayField]]
    const [movedItem1] = images_display.splice(sourceIndex, 1)
    images_display.splice(targetIndex, 0, movedItem1)
    row[imageDisplayField] = images_display

    const images_data = [...row[imageField]]
    const [movedItem2] = images_data.splice(sourceIndex, 1)
    images_data.splice(targetIndex, 0, movedItem2)
    row[imageField] = images_data
  }
  
  dragIndex.value[key] = -1
  dragOverIndex.value[key] = -1
}

const handleDragEnd = (_rowIndex: number, _field: string) => {
  const key = `${_rowIndex}-${_field}`
  dragIndex.value[key] = -1
  dragOverIndex.value[key] = -1
  const draggingElements = document.querySelectorAll('.dragging')
  draggingElements.forEach(el => {
    el.classList.remove('dragging')
  })
}

/**
 * 生成图片预览列表：过滤掉删除标记和 OSS 参数
 */
const generatePreviewList = (images: any[]): string[] => {
  if (!images || !Array.isArray(images)) {
    return []
  }
  return images
    .filter((img: any) => {
      if (typeof img === 'string') {
        return img && !img.endsWith('?delete')
      }
      if (Array.isArray(img)) {
        return img.length > 0
      }
      return false
    })
    .map((img: any) => {
      if (typeof img === 'string') {
        // 移除 OSS 参数和删除标记，使用原始图片进行预览
        const [path] = img.split('?')
        return path || img
      }
      if (Array.isArray(img) && img.length > 0) {
        return img[0]
      }
      return img
    })
    .filter(Boolean)
}

/**
 * 图片加载失败处理
 */
const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (img && img.src !== DEFAULT_IMAGE) {
    img.src = DEFAULT_IMAGE
  }
}

/**
 * 处理删除行
 */
const handleDeleteRow = (rowIndex: number) => {
  if (rowIndex >= 0 && rowIndex < dataList.value.length) {
    dataList.value.splice(rowIndex, 1)
  }
}

/**
 * 修复单个 SVG 图标的尺寸和样式
 * @param svgElement SVG 元素
 */
const fixSingleSvgIcon = (svgElement: SVGElement) => {
  // 设置 SVG 属性
  svgElement.setAttribute('width', '24')
  svgElement.setAttribute('height', '24')
  
  // 设置尺寸样式（保持原始 viewBox，不修改以确保内容正确显示）
  const sizeStyles = {
    width: '24px',
    height: '24px',
    'max-width': '24px',
    'max-height': '24px',
    'min-width': '24px',
    'min-height': '24px',
    'box-sizing': 'border-box',
    overflow: 'visible',
    position: 'static',
    margin: '0'
  }
  
  Object.entries(sizeStyles).forEach(([prop, value]) => {
    svgElement.style.setProperty(prop, value, 'important')
  })
  
  // 移除可能存在的 transform，避免位置偏移
  svgElement.style.removeProperty('transform')
  svgElement.style.removeProperty('transform-origin')
}

/**
 * 修复所有上传图标 SVG 元素的尺寸
 * 确保 SVG 图标尺寸与容器一致（24x24），并正确居中显示
 */
const fixSvgIconSize = () => {
  const selector = '.image-group-uploader-edit .el-icon--upload svg'
  
  // 立即执行一次
  nextTick(() => {
    const svgElements = document.querySelectorAll(selector)
    svgElements.forEach((svg) => fixSingleSvgIcon(svg as SVGElement))
  })
  
  // 延迟执行，确保 DOM 完全渲染（处理动态添加的情况）
  setTimeout(() => {
    const svgElements = document.querySelectorAll(selector)
    svgElements.forEach((svg) => fixSingleSvgIcon(svg as SVGElement))
  }, 100)
}

/**
 * 处理输入框焦点事件
 */
const handleInputFocus = (rowIndex: number, field: string) => {
  // 清除blur定时器
  if (blurTimerRef.value) {
    clearTimeout(blurTimerRef.value)
    blurTimerRef.value = null
  }
  
  // 确保输入框获得焦点时保持编辑状态
  if (!isEditing(rowIndex, field)) {
    editingCell.value = { rowIndex, field }
  }
  
  // 标记正在输入
  isInputting.value = true
  setTimeout(() => {
    isInputting.value = false
  }, 100)
  
  // 对于数字输入框，设置左对齐样式
  const column = props.columns.find(col => col.field === field)
  if (column && column.type === 'number') {
    nextTick(() => {
      const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
      if (cellInput) {
        // 查找 ElInputNumber 内部的 input 元素
        const inputElement = cellInput.querySelector('.el-input-number__input-wrapper input') as HTMLInputElement ||
                            cellInput.querySelector('.el-input-number__input input') as HTMLInputElement ||
                            cellInput.querySelector('.el-input-number input') as HTMLInputElement ||
                            cellInput.querySelector('input') as HTMLInputElement
        if (inputElement) {
          inputElement.style.textAlign = 'left'
        }
      }
    })
  }
}

/**
 * 处理下拉菜单显示/隐藏事件
 * 当下拉菜单显示时，设置其宽度与单元格一致
 */
const handleSelectVisibleChange = (visible: boolean, rowIndex: number, field: string) => {
  if (visible) {
    // 下拉菜单显示时，设置宽度与单元格一致
    nextTick(() => {
      const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
      if (cellInput) {
        const cell = cellInput.closest('.el-table__cell') as HTMLElement
        if (cell) {
          const cellWidth = cell.offsetWidth
          // 查找下拉菜单（popper）
          const dropdown = document.querySelector('.excel-select-dropdown') as HTMLElement
          if (dropdown) {
            dropdown.style.minWidth = `${cellWidth}px`
            dropdown.style.width = `${cellWidth}px`
          }
        }
      }
    })
  }
}

/**
 * 处理输入框失去焦点事件
 */
const handleInputBlur = (e: FocusEvent, rowIndex: number, field: string) => {
  // 如果正在输入，不处理blur
  if (isInputting.value) {
    return
  }
  
  // 清除之前的blur定时器
  if (blurTimerRef.value) {
    clearTimeout(blurTimerRef.value)
    blurTimerRef.value = null
  }
  
  // 延迟处理blur，检查焦点是否真的离开了
  blurTimerRef.value = setTimeout(() => {
    // 如果正在输入，不退出编辑
    if (isInputting.value) {
      blurTimerRef.value = null
      return
    }
    
    // 检查是否仍然是当前编辑的单元格
    if (!isEditing(rowIndex, field)) {
      blurTimerRef.value = null
      return
    }
    
    // 检查焦点是否真的离开了输入框
    const activeElement = document.activeElement
    
    // 查找当前单元格的输入框
    const cellInput = document.querySelector(`[data-cell-key="${rowIndex}-${field}"]`) as HTMLElement
    if (cellInput) {
      // 对于 ElInputNumber，需要查找 .el-input-number__input input
      let inputElement = cellInput.querySelector('input') as HTMLInputElement
      if (!inputElement) {
        inputElement = cellInput.querySelector('.el-input-number__input input') as HTMLInputElement
      }
      if (!inputElement) {
        inputElement = cellInput.querySelector('.el-input-number input') as HTMLInputElement
      }
      // 如果焦点还在当前输入框上，不退出编辑
      if (inputElement && (inputElement === activeElement || inputElement.contains(activeElement as Node))) {
        blurTimerRef.value = null
        return
      }
    }
    
    // 检查焦点是否在单元格内的其他元素中（如下拉框）
    const input = e.target as HTMLElement
    const cell = input?.closest('.el-table__cell')
    if (cell && cell.contains(activeElement)) {
      blurTimerRef.value = null
      return
    }
    
    // 只有焦点确实离开了单元格，才退出编辑
    if (isEditing(rowIndex, field)) {
      endEdit()
    }
    
    blurTimerRef.value = null
  }, 200)
}

/**
 * 处理输入框输入事件
 */
const handleInputInput = (rowIndex: number, field: string) => {
  // 标记正在输入
  isInputting.value = true
  setTimeout(() => {
    isInputting.value = false
  }, 300)
}

/**
 * 处理输入框更新事件
 */
const handleInputUpdate = (val: string, rowIndex: number, field: string) => {
  // 标记正在输入
  isInputting.value = true
  
  // 更新值时，确保不会因为数据变化导致失去焦点
  if (isEditing(rowIndex, field)) {
    dataList.value[rowIndex][field] = val
    // 确保编辑状态保持
    if (!isEditing(rowIndex, field)) {
      editingCell.value = { rowIndex, field }
    }
  }
  
  setTimeout(() => {
    isInputting.value = false
  }, 300)
}

onMounted(async () => {
  // 先不显示页面，等待状态恢复完成
  isRestoring.value = true
  
  // 保存组件挂载时的路由信息（用于检测标签页关闭）
  mountedRoutePath = router.currentRoute.value.path
  mountedRouteFullPath = router.currentRoute.value.fullPath
  
  // 优先恢复页面状态（如果存在）
  const state = restorePageState()
  if (state && state.dataList && Array.isArray(state.dataList) && state.dataList.length > 0) {
    // 恢复表格数据 - 使用完全深拷贝避免任何引用共享
    dataList.value = state.dataList.map(row => {
      const defaultRow = getDefaultRow() // 每行独立创建
      // 对row做完全深拷贝，避免任何引用共享
      const deepClonedRow = JSON.parse(JSON.stringify(row))
      return {
        ...defaultRow,
        ...deepClonedRow
      }
    })
    // 初始化原始数据
    originalData.value = JSON.parse(JSON.stringify(dataList.value))
    emit('dataLoaded', dataList.value)
    // 显示准备就绪提示
    if (prompInfoRef.value) {
      prompInfoRef.value.ready()
    }
  } else {
    // 如果没有页面状态，尝试从父窗口传入的数据加载
    const loaded = loadDataFromStorage()
    if (!loaded) {
      // 如果两者都没有，创建一行默认数据
      dataList.value = [getDefaultRow()]
      // 初始化原始数据
      originalData.value = JSON.parse(JSON.stringify(dataList.value))
      emit('dataLoaded', dataList.value)
      // 显示准备就绪提示
      if (prompInfoRef.value) {
        prompInfoRef.value.ready()
      }
    }
  }
  
  // 状态恢复完成，显示页面
  isRestoring.value = false
  pageReady.value = true
  
  // 修复 SVG 图标尺寸
  fixSvgIconSize()
  
  // 监听数据变化，修复动态添加的 SVG 图标尺寸
  watch(
    () => dataList.value,
    () => nextTick(() => fixSvgIconSize()),
    { deep: true }
  )
  
  // 监听全局复制粘贴事件
  document.addEventListener('copy', handleCopy)
  document.addEventListener('paste', handlePaste)
  
  // 监听全局键盘事件，处理焦点单元格的键盘输入
  const handleGlobalKeydown = (event: KeyboardEvent) => {
    // 如果焦点在输入框内，不处理（让输入框自己处理）
    const activeElement = document.activeElement
    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'SELECT')) {
      return
    }
    
    // 如果正在编辑，不处理（让 handleInputKeydown 处理）
    if (editingCell.value) {
      return
    }
    
    // 查找当前选中的单元格
    const selectedCell = document.querySelector('.el-table__cell.selected-cell') as HTMLElement
    if (!selectedCell) return
    
    // 获取单元格对应的行和列信息
    const rowElement = selectedCell.closest('tr')
    if (!rowElement) return
    
    // 从表格body中获取行索引（排除表头）
    const tbody = rowElement.parentElement
    if (!tbody) return
    
    const rowIndex = Array.from(tbody.children).indexOf(rowElement)
    if (rowIndex === -1) return
    
    const cellIndex = Array.from(rowElement.children).indexOf(selectedCell)
    if (cellIndex === -1) return
    
    // 跳过序号列
    const columnIndex = cellIndex - 1
    if (columnIndex < 0) return
    
    const visibleColumns = props.columns.filter(col => col.show !== false)
    if (columnIndex >= visibleColumns.length) return
    
    const column = visibleColumns[columnIndex]
    const currentIndex = editableFields.value.indexOf(column.field)
    
    // Tab 或 Enter: 跳转到下一列
    if (event.key === 'Tab' || event.key === 'Enter') {
      event.preventDefault()
      
      if (event.key === 'Tab' && event.shiftKey) {
        // Shift+Tab: 向左移动
        if (currentIndex > 0) {
          // 跳转到上一列
          const prevField = editableFields.value[currentIndex - 1]
          const prevColumn = visibleColumns.find(col => col.field === prevField)
          if (prevColumn) {
            const prevColumnIndex = visibleColumns.indexOf(prevColumn)
            const prevCell = rowElement.children[prevColumnIndex + 1] as HTMLElement
            if (prevCell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              prevCell.classList.add('selected-cell')
              updateSelectedRowIndex()
            }
          }
        } else if (rowIndex > 0) {
          // 如果已是行首，则跳转到上一行最后一列
          const prevRow = tbody.children[rowIndex - 1] as HTMLElement
          if (prevRow) {
            const lastField = editableFields.value[editableFields.value.length - 1]
            const lastColumn = visibleColumns.find(col => col.field === lastField)
            if (lastColumn) {
              const lastColumnIndex = visibleColumns.indexOf(lastColumn)
              const lastCell = prevRow.children[lastColumnIndex + 1] as HTMLElement
              if (lastCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                lastCell.classList.add('selected-cell')
                updateSelectedRowIndex()
              }
            }
          }
        }
      } else {
        // Tab 或 Enter: 向右移动到下一列
        if (currentIndex < editableFields.value.length - 1) {
          // 如果还有下一列，跳转到下一列
          const nextField = editableFields.value[currentIndex + 1]
          const nextColumn = visibleColumns.find(col => col.field === nextField)
          if (nextColumn) {
            const nextColumnIndex = visibleColumns.indexOf(nextColumn)
            const nextCell = rowElement.children[nextColumnIndex + 1] as HTMLElement
            if (nextCell) {
              document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                el.classList.remove('selected-cell')
              })
              nextCell.classList.add('selected-cell')
              updateSelectedRowIndex()
            }
          }
        } else if (rowIndex < dataList.value.length - 1) {
          // 如果已是行尾，则跳转到下一行第1列
          const nextRow = tbody.children[rowIndex + 1] as HTMLElement
          if (nextRow) {
            const firstField = editableFields.value[0]
            const firstColumn = visibleColumns.find(col => col.field === firstField)
            if (firstColumn) {
              const firstColumnIndex = visibleColumns.indexOf(firstColumn)
              const firstCell = nextRow.children[firstColumnIndex + 1] as HTMLElement
              if (firstCell) {
                document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                  el.classList.remove('selected-cell')
                })
                firstCell.classList.add('selected-cell')
                updateSelectedRowIndex()
              }
            }
          }
        } else {
          // 如果已是最后1行，则新增1行，并跳转到该行第1列
          const newRow = { ...getDefaultRow() }
          dataList.value.push(newRow)
          nextTick(() => {
            const newRowElement = tbody.children[dataList.value.length - 1] as HTMLElement
            if (newRowElement) {
              const firstField = editableFields.value[0]
              const firstColumn = visibleColumns.find(col => col.field === firstField)
              if (firstColumn) {
                const firstColumnIndex = visibleColumns.indexOf(firstColumn)
                const firstCell = newRowElement.children[firstColumnIndex + 1] as HTMLElement
                if (firstCell) {
                  document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
                    el.classList.remove('selected-cell')
                  })
                  firstCell.classList.add('selected-cell')
                  updateSelectedRowIndex()
                }
              }
            }
          })
        }
      }
      return
    }
    
    // Esc: 取消当前焦点
    if (event.key === 'Escape') {
      event.preventDefault()
      document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
        el.classList.remove('selected-cell')
      })
      return
    }
    
    // 方向键导航（非编辑模式）
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)) {
      event.preventDefault()
      
      let newRowIndex = rowIndex
      let newColumnIndex = columnIndex
      let needsNewRow = false
      
      if (event.key === 'ArrowUp' && rowIndex > 0) {
        newRowIndex = rowIndex - 1
      } else if (event.key === 'ArrowDown') {
        if (rowIndex < dataList.value.length - 1) {
          newRowIndex = rowIndex + 1
        } else {
          // 添加新行
          const newRow = { ...getDefaultRow() }
          dataList.value.push(newRow)
          newRowIndex = dataList.value.length - 1
          needsNewRow = true
        }
      } else if (event.key === 'ArrowLeft' && currentIndex > 0) {
        newColumnIndex = visibleColumns.findIndex(col => col.field === editableFields.value[currentIndex - 1])
      } else if (event.key === 'ArrowRight' && currentIndex < editableFields.value.length - 1) {
        newColumnIndex = visibleColumns.findIndex(col => col.field === editableFields.value[currentIndex + 1])
      }
      
      // 跳转到新单元格
      const navigateToCell = () => {
        const targetRow = tbody.children[newRowIndex] as HTMLElement
        if (targetRow) {
          const targetCell = targetRow.children[newColumnIndex + 1] as HTMLElement
          if (targetCell) {
            document.querySelectorAll('.el-table__cell.selected-cell').forEach(el => {
              el.classList.remove('selected-cell')
            })
            targetCell.classList.add('selected-cell')
            updateSelectedRowIndex()
            // 确保单元格可见
            targetCell.scrollIntoView({ block: 'nearest', inline: 'nearest' })
          }
        }
      }
      
      // 如果添加了新行，需要等待 DOM 更新
      if (needsNewRow) {
        nextTick(navigateToCell)
      } else {
        navigateToCell()
      }
      return
    }
    
    // 其他可打印字符，调用 handleCellKeydown 处理
    const row = dataList.value[rowIndex]
    if (row && column) {
      handleCellKeydown(event, row, { property: column.field, field: column.field })
    }
  }
  
  document.addEventListener('keydown', handleGlobalKeydown)
  
  // 清理函数
  const cleanup = () => {
    document.removeEventListener('copy', handleCopy)
    document.removeEventListener('paste', handlePaste)
    document.removeEventListener('keydown', handleGlobalKeydown)
  }
  
  // 组件卸载时清理
  onUnmounted(cleanup)
})

/**
 * 组件卸载前保存状态
 */
onBeforeUnmount(() => {
  // 先保存状态（无论切换还是关闭都先保存，确保数据不丢失）
  savePageState()
  
  // 清理 ImagePlus 引用
  imagePlusRefsMap.clear()
  
  // 清除定时器
  if (saveStateTimer) {
    clearTimeout(saveStateTimer)
    saveStateTimer = null
  }
  
  // 检查标签页是否被关闭
  // 注意：必须使用挂载时的路由信息，因为关闭标签页时路由会跳转到其他页面
  if (!mountedRoutePath || !mountedRouteFullPath) {
    console.warn('ImportGrid: 无法检查标签页状态，挂载路由信息丢失')
    return
  }
  
  const pathToCheck = mountedRoutePath
  const fullPathToCheck = mountedRouteFullPath
  
  // 延迟检查，确保标签页状态已经更新
  const checkAndClear = () => {
    const visitedViews = tagsViewStore.getVisitedViews
    // 检查挂载时的路由是否还在 visitedViews 中（使用 path 匹配，因为 store 使用 path）
    const isStillOpen = visitedViews.some(view => view.path === pathToCheck)
    
    if (!isStillOpen) {
      // 标签页已被关闭，清空状态数据
      // 使用保存的 fullPath 来生成正确的 key
      const stateKey = `IMPORT_GRID_STATE_${fullPathToCheck}`
      clearPageState(stateKey, fullPathToCheck)
      return true
    } else {
      // 标签页仍然打开，只是切换了路由，保持状态数据
      return false
    }
  }
  
  // 延迟检查，确保标签页状态已经更新
  nextTick(() => {
    // 第一次检查（50ms后）
    setTimeout(() => {
      if (checkAndClear()) return
      
      // 第二次检查（200ms后，如果第一次检查标签页还在）
      setTimeout(() => {
        checkAndClear()
      }, 150)
    }, 50)
  })
})

// 暴露方法供父组件调用
defineExpose({
  getData: () => dataList.value,
  setData: (data: any[]) => {
    dataList.value = data
    // 更新原始数据
    originalData.value = JSON.parse(JSON.stringify(data))
  },
  getDefaultRow,
  loadDataFromStorage,
  setCurrentRow, // 允许程序内部指定当前行
  uploadRowImageField, // 上传指定行的图片字段
  uploadAllRowImages, // 上传所有行的图片字段
  save: save, // 通用的保存方法（显式引用，确保可以访问）
  addRow, // 新增行方法
  prompInfoRef // 暴露 PrompInfo 引用，方便外部调用
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
    
    <div class="table-wrapper">
      <ElTable
      ref="tableRef"
      :data="dataList"
      border
      class="excel-table"
      @cell-click="handleCellClick"
      @cell-dblclick="handleCellDblclick"
    >
      <!-- 序号列 -->
      <ElTableColumn
        type="index"
        :index="(index: number) => index + 1"
        width="40"
        align="center"
        label=""
      >
        <template #default="scope">
          <div class="row-index-cell">
            <span v-if="currentRowIndex === scope.$index" class="row-index-pointer">
              <!-- 右箭头图标 -->
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                style="cursor: pointer; display: block;"
              >
                <!-- 右箭头 -->
                <path
                  d="M9 6L15 12L9 18"
                  :stroke="CURRENT_ROW_COLOR"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  fill="none"
                />
              </svg>
            </span>
            <span v-else class="row-index-number">{{ scope.$index + 1 }}</span>
          </div>
        </template>
      </ElTableColumn>
      
      <ElTableColumn
        v-for="column in props.columns.filter(col => col.show !== false)"
        :key="column.field"
        :prop="column.field"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
      >
        <template #header>
          <span>
            {{ column.label }}
            <span v-if="column.required" style="color: #f56c6c; margin-left: 2px;">*</span>
          </span>
        </template>
        <template #default="scope">
          <!-- 图片列：使用 ImagePlus 组件 -->
          <div
            v-if="column.type === 'image' && column.editable !== false"
            :key="getImagePlusKey(scope.$index, column.field)"
            class="excel-edit-image"
            @click="handleImageCellClick(scope.$index, column.field, $event)"
          >
            <ImagePlus
              :ref="(el: any) => setImagePlusRef(scope.$index, column.field, el)"
              :model-value="scope.row[column.field] || []"
              @update:model-value="(val: any[]) => handleImageUpdate(scope.$index, column.field, val)"
              :disabled="false"
              :limit="10"
              :size="column.size || 'small'"
            />
          </div>
          
          <!-- 编辑模式：数字输入框 -->
          <ElInputNumber
            v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'number'"
            :key="`input-number-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            size="small"
            :controls="false"
            class="excel-edit-input excel-input-number-left"
            :style="{ textAlign: 'left' }"
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
            @input="handleInputInput(scope.$index, column.field)"
          />
          
          <!-- 编辑模式：下拉选择 -->
          <ElSelect
            v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'select' && column.options"
            :key="`select-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            size="small"
            class="excel-edit-select"
            popper-class="excel-select-dropdown"
            :style="{ width: '100%', minWidth: '100%', maxWidth: '100%', display: 'block' }"
            :disabled="column.selectProps?.disabled ?? false"
            :readonly="column.selectProps?.readonly"
            :clearable="column.selectProps?.clearable"
            :filterable="column.selectProps?.filterable ?? false"
            :allow-create="column.selectProps?.allowCreate ?? false"
            v-bind="column.selectProps || {}"
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
            @visible-change="(visible: boolean) => handleSelectVisibleChange(visible, scope.$index, column.field)"
          >
            <ElOption
              v-for="opt in column.options"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </ElSelect>
          
          <!-- 编辑模式：多行文本输入框 (type='text') -->
          <ElInput
            v-else-if="isEditing(scope.$index, column.field) && column.editable !== false && column.type === 'text'"
            :key="`textarea-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            type="textarea"
            resize="none"
            size="small"
            class="excel-edit-input excel-edit-textarea"
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
            @input="handleInputInput(scope.$index, column.field)"
            @update:model-value="handleInputUpdate(scope.$index, column.field, $event)"
          />
          
          <!-- 编辑模式：单行文本输入框 (其他类型) -->
          <ElInput
            v-else-if="isEditing(scope.$index, column.field) && column.editable !== false"
            :key="`input-${scope.$index}-${column.field}`"
            :data-cell-key="`${scope.$index}-${column.field}`"
            v-model="scope.row[column.field]"
            size="small"
            class="excel-edit-input"
            @keydown.stop="handleInputKeydown($event, scope.$index, column.field)"
            @focus="handleInputFocus(scope.$index, column.field)"
            @blur="handleInputBlur($event, scope.$index, column.field)"
            @input="handleInputInput(scope.$index, column.field)"
            @update:model-value="handleInputUpdate(scope.$index, column.field, $event)"
          />
          
          <!-- 显示模式：其他类型 -->
          <span 
            v-else
            class="excel-cell"
            :class="{ 
              'cell-focused': isEditing(scope.$index, column.field),
              'cell-number': column.type === 'number',
              'cell-text': column.type !== 'number',
              'cell-text-multiline': column.type === 'text'
            }"
            @keydown="column.editable !== false && handleCellKeydown($event, scope.row, { property: column.field })"
            tabindex="0"
          >{{ formatCellValue(scope.row[column.field], column) }}</span>
        </template>
      </ElTableColumn>
      
      <!-- Action 列：删除按钮 -->
      <ElTableColumn
        label=""
        width="40"
        align="center"
        fixed="right"
      >
        <template #default="scope">
          <div
            class="action-delete"
            :class="{ 'action-delete-current': currentRowIndex === scope.$index }"
            @click.stop="handleDeleteRow(scope.$index)"
          >
            <ElIcon :size="16">
              <Delete />
            </ElIcon>
          </div>
        </template>
      </ElTableColumn>
    </ElTable>
    </div>
  </div>
</template>

<style lang="less" scoped>
// ==================== Less Mixins ====================
// Mixin: 移除边框和背景，设置为透明
.remove-border-bg() {
  border: none !important;
  border-width: 0 !important;
  border-top: none !important;
  border-right: none !important;
  border-bottom: none !important;
  border-left: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  outline: none !important;
  background: transparent !important;
  background-color: transparent !important;
}

// Mixin: 完全填充容器
.fill-container() {
  width: 100% !important;
  min-width: 100% !important;
  max-width: 100% !important;
  height: 100% !important;
}

// Mixin: 编辑组件绝对定位填充
.absolute-fill-cell() {
  position: absolute !important;
  top: 0 !important;
  left: -1px !important;
  right: -1px !important;
  bottom: 0 !important;
  width: calc(100% + 2px) !important;
  min-width: calc(100% + 2px) !important;
  max-width: calc(100% + 2px) !important;
  height: 100% !important;
  min-height: 100% !important;
  max-height: 100% !important;
}

// ==================== 基础布局样式 ====================
.import-grid-container {
  padding: 0 !important;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 工具栏样式 */
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

:deep(.excel-table) {
  height: 100%;
  
  .el-table__body-wrapper {
    overflow-y: auto;
  }
  
  .el-table__cell {
    padding: 4px !important;
    position: relative;
    // 确保单元格有最小高度
    min-height: 32px;
    vertical-align: middle !important; // 纵向居中对齐
    
    &:hover {
      background-color: #f5f7fa;
    }
  }
  
  // 序号列样式
  .el-table__cell:first-child {
    background-color: #fafafa;
    font-weight: 500;
    text-align: center;
    user-select: none;
    padding-left: 0 !important;
    padding-right: 0 !important;
    font-size: 12px !important; // 减小2级字号
    cursor: pointer !important; // 序号列可点击
  }
  
  // 行号单元格样式
  .row-index-cell {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    min-height: 32px;
  }
  
  .row-index-number {
    font-size: 12px;
    color: #606266;
  }
  
  .row-index-pointer {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }
  
  // ==================== 选中行样式 ====================
  // 选中行的单元格边框样式
  // 使用伪元素绘制边框，不影响单元格内容布局
  .selected-row-cell {
    position: relative;
    
    // 使用伪元素绘制边框
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      border-top: 2px solid rgb(16, 153, 104);
      border-bottom: 2px solid rgb(16, 153, 104);
      pointer-events: none;
      z-index: 1;
    }
    
    // 第一列（第2列，因为序号是第1列）左边框
    &.selected-row-cell-first::before {
      border-left: 2px solid rgb(16, 153, 104);
    }
    
    // 最后一列（倒数第2列，因为action是最后1列）右边框
    &.selected-row-cell-last::before {
      border-right: 2px solid rgb(16, 153, 104);
    }
  }
  
  // 序号列表头隐藏
  .el-table__header-wrapper .el-table__header th:first-child {
    background-color: #fafafa;
    border-right: 1px solid #ebeef5;
  }
  
  // 强制覆盖 Element Plus 表头的默认 padding
  .el-table.el-table--default :deep(thead .cell) {
    padding-left: 0 !important;
    padding-right: 0 !important;
  }
  
  // Element Plus Table 自动生成的 .cell 包装器
  // 重置其默认样式，确保完全填充单元格内容区域
  :deep(.el-table__cell .cell) {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: 100% !important;
    min-height: 32px !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    border: none !important;
    position: relative !important;
  }
  
  // 标题栏 .cell 包装器
  :deep(.el-table__header-wrapper .el-table__header .el-table__cell .cell),
  :deep(.el-table__header .el-table__cell .cell) {
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    justify-content: center;
    
    span {
      padding: 0 !important;
      margin: 0 !important;
      flex: 1;
      min-width: 0;
      line-height: 1.2;
      text-align: center;
      word-break: break-word;
    }
  }
  
  .excel-cell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 2px 5px !important;
    cursor: cell;
    outline: none;
    box-sizing: border-box !important;
    text-align: left;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin: 0 !important;
    
    // 数字类型右对齐
    &.cell-number {
      text-align: right;
    }
    
    // 文本类型左对齐
    &.cell-text {
      text-align: left;
    }
    
    // 多行文本类型 (type='text')
    // 也使用纵向居中（由父容器 .cell 控制）
    &.cell-text-multiline {
      // 支持多行显示和换行
      white-space: normal !important;
      word-wrap: break-word !important;
      word-break: break-word !important;
      line-height: 1.5 !important;
      
      // 简单截断，不显示省略号
      overflow: hidden !important;
      box-sizing: border-box !important;
    }
  }
  
  // 单元格选中时的边框样式
  .el-table__cell {
    position: relative;
    
    &.selected-cell::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      border: 2px solid rgb(16, 153, 104);
      pointer-events: none;
      box-sizing: border-box;
      z-index: 1;
    }
  }
  
  // ==================== ElSelect 下拉框 ====================
  .excel-edit-select {
    overflow: visible !important;
    
    :deep(.el-select) {
      .fill-container();
      display: block !important;
    }
    
    :deep(.el-select__wrapper),
    :deep(.el-input__wrapper) {
      .fill-container();
      .remove-border-bg();
      padding: 0 4px !important;
      display: flex !important;
      align-items: center !important;
      
      &:hover, &:focus, &:focus-within, &.is-focus {
        .remove-border-bg();
      }
    }
    
    :deep(.el-input__inner) {
      .fill-container();
      .remove-border-bg();
      padding: 0 !important;
      
      &:hover, &:focus {
        .remove-border-bg();
      }
    }
    
    :deep(.el-select__placeholder),
    :deep(.el-select__selected-item) {
      .fill-container();
      display: flex !important;
      align-items: center !important;
    }
    
    :deep(.el-select__caret) {
      flex-shrink: 0 !important;
    }
  }
  
  // ==================== ElInput 和 ElInputNumber 文本/数字输入框 ====================
  .excel-edit-input {
    :deep(.el-input),
    :deep(.el-input-number) {
      .fill-container();
      display: block !important;
    }
    
    :deep(.el-input__wrapper),
    :deep(.el-input-number__input-wrapper) {
      .fill-container();
      .remove-border-bg();
      padding: 0 4px !important;
      // 垂直居中对齐
      display: flex !important;
      align-items: center !important;
      
      &:hover, &:focus, &:focus-within, &.is-focus {
        .remove-border-bg();
      }
    }
    
    :deep(.el-input__inner) {
      .fill-container();
      .remove-border-bg();
      padding: 0 !important;
      // 垂直居中对齐
      line-height: normal !important;
      display: flex !important;
      align-items: center !important;
      
      &:hover, &:focus {
        .remove-border-bg();
      }
    }
    
    :deep(.el-input-number__input) {
      .fill-container();
      flex: 1 !important;
      
      input {
        .fill-container();
        .remove-border-bg();
        text-align: left !important;
        
        &:hover, &:focus {
          .remove-border-bg();
        }
      }
    }
    
    // 隐藏数字输入框的加减按钮
    :deep(.el-input-number__decrease),
    :deep(.el-input-number__increase) {
      display: none !important;
    }
  }
  
  // ==================== 多行文本框 (Textarea) ====================
  .excel-edit-textarea {
    .absolute-fill-cell();
    display: block !important;
    z-index: 10 !important;
    
    :deep(.el-textarea) {
      .absolute-fill-cell();
      display: block !important;
      padding: 0 !important;
      margin: 0 !important;
    }
    
    :deep(.el-textarea__inner) {
      .absolute-fill-cell();
      .remove-border-bg();
      padding: 4px 5px !important; // 恢复原来的边距
      margin: 0 !important;
      resize: none !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      box-sizing: border-box !important;
      
      &:hover, &:focus, &:active {
        .remove-border-bg();
      }
    }
  }
  
  // ==================== 编辑状态下的单元格样式 ====================
  .el-table__cell.editing-cell {
    padding: 0 !important;
    overflow: visible !important;
    position: relative !important; // td 作为定位容器
    
    // 编辑模式下 .cell 完全不影响布局，编辑组件直接相对于 td 定位
    :deep(.cell) {
      padding: 0 !important;
      margin: 0 !important;
      position: static !important; // 不作为定位容器
      // 不设置任何高度，让编辑组件直接相对于 td 定位
    }
  }
  
  // ==================== 表头样式 ====================
  .el-table__header th {
    background-color: #fafafa;
    font-weight: 600;
    border-bottom: 2px solid #e8e8e8;
    text-align: center !important;
  }
  
  // ==================== 图片列样式 ====================
  // 图片列始终显示编辑模式（类似 BaseFree.vue 的新增/修改模式）
  // image列随内容增长自动伸长，以容纳内容
  .excel-edit-image {
    position: relative !important;
    width: 100% !important;
    min-width: 100% !important;
    max-width: none !important;
    height: auto !important;
    min-height: auto !important;
    margin: 0 !important;
    padding: 4px !important;
    display: block !important;
    box-sizing: border-box !important;
    overflow: visible !important;
    background: transparent !important;
  }
  
  // 确保 image 列的单元格可以自动伸长
  // 使用更兼容的方式，通过类名选择器
  // 如果行包含图片编辑组件，允许行自动伸长
  :deep(.el-table__body tbody tr:has(.excel-edit-image)) {
    height: auto !important;
    max-height: none !important;
  }
  
  .el-table__cell {
    // 如果单元格包含图片编辑组件，允许自动伸长
    &:has(.excel-edit-image) {
      height: auto !important;
      max-height: none !important;
      min-height: 32px !important;
      white-space: normal !important;
    }
  }
  
  // 兼容性处理：直接为包含图片编辑的单元格设置样式
  :deep(.el-table__cell) {
    .excel-edit-image {
      // 确保图片容器可以超出单元格宽度
      max-width: none !important;
    }
  }
  
  // ==================== Action 列样式 ====================
  .action-delete {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    cursor: pointer;
    color: inherit;
    transition: color 0.2s ease;
    
    // 非当前行的 hover 效果
    &:hover {
      color: #f56c6c;
    }
    
    // 当前行的删除图标颜色
    &.action-delete-current {
      color: rgb(16, 153, 104);
      
      // 当前行的 hover 效果，与非当前行保持一致（变红色）
      &:hover {
        color: #f56c6c;
      }
    }
    
    // 确保 ElIcon 继承颜色
    :deep(.el-icon) {
      color: inherit;
    }
  }
  
  // ==================== 图片列样式 ====================
  .image-container-edit {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0;
  }
  
  .image-group-edit {
    position: relative;
    width: 60px;
    height: 60px;
    margin: 0;
    cursor: move;
  }
  
  .image-item-edit {
    width: 100%;
    height: 100%;
    display: block;
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
  }
  
  .image-item-edit:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .action-delete {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    cursor: pointer;
    color: inherit; // 使用当前字体颜色
    transition: color 0.2s ease;
    
    // 非当前行的 hover 效果
    &:hover {
      color: #f56c6c; // hover 时变红色
    }
    
    // 当前行的删除图标颜色
    &.action-delete-current {
      color: rgb(16, 153, 104);
      
      // 当前行的 hover 效果，与非当前行保持一致（变红色）
      &:hover {
        color: #f56c6c; // hover 时变红色，同非当前行
      }
    }
    
    // 确保 ElIcon 继承颜色
    :deep(.el-icon) {
      color: inherit;
    }
  }
  
  .image-container-edit {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0;
  }
  
  .image-group-edit {
    position: relative;
    width: 60px;
    height: 60px;
    margin: 0;
    cursor: move;
  }
  
  .image-item-edit {
    width: 100%;
    height: 100%;
    border-radius: 4px;
    border: 1px solid #dcdfe6;
    transition: all 0.3s ease;
  }
  
  .image-item-edit:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .image-group-edit :deep(.el-image) {
    width: 100%;
    height: 100%;
    border-radius: 4px;
  }
  
  .image-group-edit :deep(.el-image__inner) {
    border-radius: 4px;
    object-fit: cover;
  }
  
  .remove-btn-edit {
    position: absolute;
    top: -6px;
    right: -6px;
    width: 20px;
    height: 20px;
    background: #f56c6c;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;
    font-weight: bold;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: 100;
  }
  
  .image-group-edit:hover .remove-btn-edit {
    opacity: 1;
  }
  
  .image-group-edit.dragging {
    opacity: 0.5;
    border-color: #409eff;
    transform: scale(0.95);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    cursor: grabbing;
    z-index: 1000;
  }
  
  .image-group-edit.drag-over {
    transform: scale(1.15);
    border: 2px solid #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
    z-index: 10;
    transition: all 0.2s ease;
  }
  
  .image-group-uploader-edit {
    width: 60px;
    height: 60px;
    flex-shrink: 0;
    box-sizing: border-box;
    overflow: hidden; // 防止子元素溢出
    
    // 修复 ElUpload 组件自动生成的中间层 div（没有 class 的包装元素）
    > div {
      width: 100% !important;
      height: 100% !important;
      min-width: 100% !important;
      min-height: 100% !important;
      max-width: 100% !important;
      max-height: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      box-sizing: border-box !important;
      display: block !important;
    }
  }
  
  .image-group-uploader-edit .el-upload {
    border: 2px dashed #c0c4cc;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 4px;
    box-sizing: border-box !important; // 确保 border 包含在尺寸内
    min-width: 100% !important;
    min-height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
  }
  
  .image-group-uploader-edit .el-upload:hover {
    border-color: #409eff;
    background: #f0f7ff;
    color: #409eff;
  }
  
  .image-group-uploader-edit .el-upload-dragger {
    width: 100% !important;
    height: 100% !important;
    min-width: 100% !important;
    min-height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
  }
  
  // 上传内容包装器：确保上传图标和文字居中显示
  .upload-content-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    overflow: visible;
    position: relative;
    gap: 0;
  }
  
  // 上传图标容器样式
  .image-group-uploader-edit .el-icon--upload {
    width: 24px;
    height: 24px;
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    flex-shrink: 0;
    overflow: visible !important;
    position: relative;
    
    // SVG 图标样式：固定尺寸 24x24，通过 flex 居中
    :deep(svg) {
      width: 24px !important;
      height: 24px !important;
      min-width: 24px !important;
      min-height: 24px !important;
      max-width: 24px !important;
      max-height: 24px !important;
      margin: 0 !important;
      padding: 0 !important;
      display: block !important;
      box-sizing: border-box !important;
      overflow: visible !important;
      position: static !important;
    }
    
    // 覆盖 SVG 元素上可能存在的固定高度属性
    :deep(svg[height]),
    :deep(svg[height="67"]),
    :deep(svg[height="67px"]) {
      height: 24px !important;
      max-height: 24px !important;
      width: 24px !important;
      max-width: 24px !important;
    }
  }
  
  .upload-text-edit {
    font-size: 10px;
    margin-top: 4px;
    margin-bottom: 0;
    text-align: center;
    line-height: 1.2;
    padding: 0;
    flex-shrink: 0;
  }
}
</style>

<style lang="less">
// 全局样式：强制覆盖 Element Plus 表头 .cell 的 padding
// 必须使用全局样式才能覆盖 Element Plus 的默认样式
.excel-table {
  .el-table__header {
    .el-table__cell {
      .cell {
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
      }
    }
  }
  
  // 也覆盖数据行的 .cell（如果需要）
  .el-table__body {
    .el-table__cell {
      .cell {
        padding-left: 0 !important;
        padding-right: 0 !important;
      }
    }
  }
}

// 全局样式：下拉菜单宽度与单元格一致
// 注意：下拉菜单是 teleported 到 body 的，所以需要使用全局样式
.excel-select-dropdown {
  min-width: fit-content !important;
  
  .el-select-dropdown__item {
    padding: 8px 12px;
    white-space: nowrap;
  }
}


// ==================== 全局样式：单元格内部容器 ====================
.excel-table {
  tbody .el-table__cell .cell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important; // 使用 flex 布局实现纵向居中
    align-items: center !important;
  }
  
  // 编辑模式下，让 .cell 不作为定位容器，编辑组件直接相对于 td 定位
  tbody .el-table__cell.editing-cell {
    position: relative !important; // td 作为定位容器
    // 移除 .cell 的高度限制，让它完全不影响布局
    // 编辑组件直接相对于 td 绝对定位，不依赖 .cell 的高度
  }
}

// ==================== 全局样式：多行文本单元格样式 ====================
// 包含多行文本的单元格，限制高度防止撑大行高
.excel-table {
  .el-table__cell:has(.cell-text-multiline) {
    vertical-align: top !important; // 顶部对齐，避免文本被裁剪
    
    // 在父容器上限制高度，防止行高被撑大
    .cell {
      max-height: 4.8em !important; // 约 3 行的高度 (line-height: 1.5)
      overflow: hidden !important;
      // 使用 flex 布局，但从顶部开始显示（不居中），避免文本被从上下裁剪
      display: flex !important;
      align-items: flex-start !important; // 顶部对齐，文本从第一行完整显示
    }
  }
}

// ==================== 全局样式：强制移除编辑组件边框 ====================
// 编辑模式下的所有 Element Plus 输入组件，强制移除边框和背景
.excel-table {
  // 所有编辑组件的 wrapper
  .el-input__wrapper,
  .el-select__wrapper,
  .el-input-number__wrapper {
    border: none !important;
    border-width: 0 !important;
    border-top: none !important;
    border-right: none !important;
    border-bottom: none !important;
    border-left: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
    background-color: transparent !important;
    // 垂直居中对齐
    display: flex !important;
    align-items: center !important;
    
    &:hover,
    &:focus,
    &:focus-within,
    &.is-focus,
    &.is-hover {
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      box-shadow: none !important;
      outline: none !important;
      background: transparent !important;
      background-color: transparent !important;
    }
  }
  
  // .el-textarea 组件本身，强制充满容器
  .el-textarea {
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    display: block !important;
  }
  
  // textarea 单独处理，不需要 flex 居中
  .el-textarea__inner {
    border: none !important;
    border-width: 0 !important;
    border-top: none !important;
    border-right: none !important;
    border-bottom: none !important;
    border-left: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
    background-color: transparent !important;
    padding: 4px 5px !important; // 恢复原来的边距
    box-sizing: border-box !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    
    &:hover,
    &:focus,
    &:focus-within,
    &.is-focus,
    &.is-hover {
      border: none !important;
      border-width: 0 !important;
      box-shadow: none !important;
      outline: none !important;
      background: transparent !important;
      background-color: transparent !important;
    }
  }
  
  // 所有 input 元素（单行输入框）
  .el-input__inner,
  input:not([type="textarea"]) {
    border: none !important;
    border-width: 0 !important;
    border-top: none !important;
    border-right: none !important;
    border-bottom: none !important;
    border-left: none !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
    background-color: transparent !important;
    // 垂直居中对齐
    line-height: normal !important;
    
    &:hover,
    &:focus,
    &:active {
      border: none !important;
      border-width: 0 !important;
      box-shadow: none !important;
      outline: none !important;
      background: transparent !important;
      background-color: transparent !important;
    }
  }
  
  // textarea 单独处理（多行文本框）
  textarea {
    border: none !important;
    border-width: 0 !important;
    box-shadow: none !important;
    outline: none !important;
    background: transparent !important;
    background-color: transparent !important;
    
    &:hover,
    &:focus,
    &:active {
      border: none !important;
      border-width: 0 !important;
      box-shadow: none !important;
      outline: none !important;
      background: transparent !important;
      background-color: transparent !important;
    }
  }
  
  // ElSelect 组件
  .el-select,
  .el-input,
  .el-input-number,
  .el-textarea {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
  }
}
</style>
