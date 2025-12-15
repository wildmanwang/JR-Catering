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
const getDefaultRow = (): any => {
  // 根据列配置生成默认行数据
  const defaultRowFromColumns: any = {}
  
  props.columns.forEach(column => {
    if (column.value !== undefined) {
      // 如果列配置中有 value，使用该值（与 FormSchema 保持一致）
      defaultRowFromColumns[column.field] = column.value
    } else if (column.type === 'image') {
      // 图片类型默认值为空数组
      defaultRowFromColumns[column.field] = []
    } else if (column.type === 'text' && column.required) {
      // 必填的文本类型默认值为空字符串
      defaultRowFromColumns[column.field] = ''
    }
    // 其他类型默认值为 undefined，不需要设置
  })
  
  // 如果提供了 createDefaultRow 函数，先合并它的返回值（向后兼容）
  // 然后覆盖列配置中的默认值
  const createDefaultRowResult = props.createDefaultRow()
  return {
    ...createDefaultRowResult,
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
/**
 * ImagePlus 组件引用映射
 * 使用非响应式 Map 避免在 ref 回调中触发响应式更新导致的 parentNode 错误
 */
const imagePlusRefsMap = new Map<string, InstanceType<typeof ImagePlus>>()

/**
 * 设置 ImagePlus 组件引用
 * 使用 setTimeout 延迟执行，确保 DOM 更新完成
 */
const setImagePlusRef = (rowIndex: number, field: string, el: any) => {
  setTimeout(() => {
    const refKey = `${rowIndex}-${field}`
    el ? imagePlusRefsMap.set(refKey, el) : imagePlusRefsMap.delete(refKey)
  }, 0)
}

/**
 * 上传指定行的图片字段
 */
const uploadRowImageField = async (rowIndex: number, field: string): Promise<void> => {
  const refKey = `${rowIndex}-${field}`
  const imagePlusRef = imagePlusRefsMap.get(refKey)
  
  if (imagePlusRef?.uploadPendingImages) {
    await imagePlusRef.uploadPendingImages()
  }
}

/**
 * 上传所有行的图片字段
 */
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
      
      // 如果长度不同，肯定有变化
      if (currentImages.length !== originalImages.length) {
        return true
      }
      
      // 比较每个元素（包括顺序），因为排序变化也应该被检测到
      for (let i = 0; i < currentImages.length; i++) {
        if (currentImages[i] !== originalImages[i]) {
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
        const currentData = dataList.value
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
        
        // 保存成功后，从数据库重新获取该条记录
        const id = result.id || (isNew ? (result.data?.id || (result.data && typeof result.data === 'object' && 'id' in result.data ? result.data.id : null)) : row.id)
        
        if (id) {
          // 重新获取完整记录（使用 API 接口或回调函数）
          const detail = useApi
            ? await getDetailWithApi(id)
            : await config.onGetDetail!(id)
          
          if (detail) {
            const currentData = dataList.value
            const currentRow = currentData[index]
            
            // 数据后处理
            let updatedDetail = detail
            if (config.postprocessData) {
              updatedDetail = config.postprocessData(detail, currentRow)
            }
            
            // 更新表格中的数据
            currentData[index] = {
              ...currentRow,
              ...updatedDetail
            }
            
            dataList.value = [...currentData]
            
            // 更新原始数据
            originalData.value[index] = JSON.parse(JSON.stringify(currentData[index]))
          }
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
    
    // 清除当前行
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
    const state = {
      dataList: toRaw(dataList.value) || []
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
      // 内存中有状态，直接返回
      return state
    }
    
    // 内存中没有，尝试从 sessionStorage 恢复（页面刷新场景）
    const cache = sessionStorage.getItem(PAGE_STATE_KEY.value)
    if (cache) {
      state = JSON.parse(cache)
      // 同步到 tagsViewStore（内存）
      tagsViewStore.setPageState(fullPath, state)
      return state
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
        // 如果 mapRowData 只是做合并操作，可以直接使用传入的 row
        const defaultRow = getDefaultRow()
        dataList.value = payload.map(row => ({
          ...defaultRow,
          ...props.mapRowData(row)
        }))
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
  
  if (cell) {
    cell.classList.add('selected-cell')
    updateSelectedRowIndex()
  }
  
  // 然后进入编辑模式
  startEdit(rowIndex, field)
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
    if (col?.type === 'select') {
      // 下拉框时，方向键用于选择，不阻止
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
 * 处理复制（Ctrl+C）
 */
const handleCopy = (event: ClipboardEvent) => {
  // 优先处理编辑模式
  if (editingCell.value) {
    const { rowIndex, field } = editingCell.value
    const value = dataList.value[rowIndex]?.[field]
    if (value !== undefined && value !== null) {
      const copyValue = String(value)
      // 使用 clipboardData 设置剪贴板（必须在 copy 事件中同步设置）
      if (event.clipboardData) {
        event.clipboardData.setData('text/plain', copyValue)
      }
      // 同时使用 Clipboard API 确保设置成功（异步，作为备用）
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(copyValue).catch(() => {
          // Clipboard API 失败时静默处理（已通过 clipboardData 设置）
        })
      }
    }
    return
  }
  
  // 非编辑模式：从选中的单元格复制
  const cellInfo = getSelectedCellInfo()
  if (cellInfo) {
    const { rowIndex, field } = cellInfo
    const value = dataList.value[rowIndex]?.[field]
    
    let copyValue = ''
    if (value !== undefined && value !== null) {
      // 拷贝原始值（字符串形式），而不是格式化后的显示值
      copyValue = String(value)
    }
    
    // 使用 clipboardData 设置剪贴板（必须在 copy 事件中同步设置）
    if (event.clipboardData) {
      event.clipboardData.setData('text/plain', copyValue)
    }
    
    // 同时使用 Clipboard API 确保设置成功（异步，作为备用）
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(copyValue).catch(() => {
        // Clipboard API 失败时静默处理（已通过 clipboardData 设置）
      })
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
    // 直接使用系统剪贴板
    const pasteData = event.clipboardData?.getData('text/plain') || ''
    if (pasteData) {
      const { rowIndex, field } = editingCell.value
      const col = props.columns.find(c => c.field === field)
      
      if (col?.type === 'number') {
        const num = Number(pasteData)
        if (!isNaN(num)) {
          dataList.value[rowIndex][field] = num
        }
      } else {
        dataList.value[rowIndex][field] = pasteData
      }
    }
    return
  }
  
  // 非编辑模式：粘贴到选中的单元格
  const cellInfo = getSelectedCellInfo()
  if (cellInfo) {
    event.preventDefault()
    // 直接使用系统剪贴板
    const pasteData = event.clipboardData?.getData('text/plain') || ''
    if (pasteData !== undefined && pasteData !== null && pasteData !== '') {
      const { rowIndex, field, column } = cellInfo
      
      // 检查列是否可编辑
      if (column.editable === false) {
        return
      }
      
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
      } else {
        dataList.value[rowIndex][field] = pasteData
      }
    } else {
      // 如果粘贴数据为空，清空单元格
      const { rowIndex, field, column } = cellInfo
      if (column.editable !== false) {
        dataList.value[rowIndex][field] = column.type === 'number' ? null : ''
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
    // 恢复表格数据
    dataList.value = state.dataList.map(row => ({
      ...props.createDefaultRow(),
      ...row
    }))
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
            :key="`image-${scope.$index}-${column.field}`"
            class="excel-edit-image"
            @click.stop
          >
            <ImagePlus
              :ref="(el: any) => setImagePlusRef(scope.$index, column.field, el)"
              :model-value="scope.row[column.field] || []"
              @update:model-value="(val: any[]) => {
                scope.row[column.field] = val
              }"
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
          
          <!-- 编辑模式：文本输入框 -->
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
              'cell-text': column.type !== 'number'
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
  min-width: 0; // 允许收缩
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
    padding: 4px 8px !important;
    position: relative;
    // 确保单元格有最小高度
    min-height: 32px;
    
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
  
  // 序号列表头隐藏
  .el-table__header-wrapper .el-table__header th:first-child {
    background-color: #fafafa;
    border-right: 1px solid #ebeef5;
  }
  
  // Element Plus Table 自动生成的 .cell 包装器
  // 重置其默认样式，确保完全填充单元格内容区域
  :deep(.el-table__cell .cell) {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    display: block !important;
    border: none !important;
    position: relative !important;
    // 不设置 height: 100%，让内容自然撑开，但确保最小高度
    min-height: 100% !important;
    // 确保有最小高度，即使内容为空（absolute 定位的元素不占位）
    min-height: 32px !important;
  }
  
  .excel-cell {
    display: block;
    // 宽度与上层div一样宽（100%）
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    // 高度由内容决定，但确保最小高度
    min-height: 100% !important;
    padding-top: 2px !important;
    padding-right: 5px !important;
    padding-bottom: 2px !important;
    padding-left: 5px !important;
    cursor: cell;
    outline: none;
    position: relative;
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
  
  // ==================== ElSelect 下拉框样式 ====================
  // 
  // 样式说明：
  // 1. 使用 absolute 定位完全填充单元格
  // 2. 通过透明背景确保不遮挡单元格边框
  // 3. 移除所有边框、阴影和轮廓，提供无缝编辑体验
  .excel-edit-select {
    position: absolute !important;
    top: 0 !important;
    left: -1px !important;
    right: -1px !important;
    bottom: 0 !important;
    width: calc(100% + 2px) !important;
    min-width: calc(100% + 2px) !important;
    max-width: calc(100% + 2px) !important;
    height: 100% !important;
    min-height: 32px !important;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
    box-sizing: border-box !important;
    overflow: visible !important;
    z-index: 10 !important;
    visibility: visible !important;
    opacity: 1 !important;
    
    // 确保 Element Plus 组件的根元素（直接子元素）也有最小高度和宽度
    > * {
      min-height: 32px !important;
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }
    visibility: visible !important;
    opacity: 1 !important;
    
    // Element Plus Select 根元素 - 强制宽度
    :deep(.el-select) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      display: block !important;
      box-sizing: border-box;
      position: relative;
    }
    
    // Element Plus Select 的容器
    :deep(.el-select__tags) {
      width: 100% !important;
      max-width: 100% !important;
    }
    
    // 确保 Select 组件本身没有宽度限制
    :deep(.el-select__caret-wrapper) {
      flex-shrink: 0;
    }
    
    // Select wrapper（Element Plus 的新版本结构）
    :deep(.el-select__wrapper) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      min-height: 100% !important;
      max-height: 100% !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      border-color: transparent !important;
      background: transparent !important;
      background-color: transparent !important;
      box-shadow: none !important;
      border-radius: 0 !important;
      padding: 0 4px !important;
      line-height: 1.5 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      box-sizing: border-box !important;
      margin: 0 !important;
      text-align: left !important;
      outline: none !important;
      
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
        border-color: transparent !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
      }
    }
    
    // Input wrapper（Element Plus 的内部结构）
    :deep(.el-input__wrapper) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      min-height: 100% !important;
      max-height: 100% !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      border-color: transparent !important;
      background: transparent !important;
      background-color: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
      box-shadow: none !important;
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      box-sizing: border-box !important;
      outline: none !important;
      
      &:hover,
      &:focus,
      &:focus-within,
      &.is-focus,
      &.is-hover {
        border: none !important;
        border-width: 0 !important;
        border-color: transparent !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        border-left: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
      }
    }
    
    // Input inner（实际输入框）
    :deep(.el-input__inner) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      min-height: 100% !important;
      max-height: 100% !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      background: transparent !important;
      background-color: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
      line-height: inherit !important;
      display: flex !important;
      align-items: center !important;
      box-sizing: border-box !important;
      text-align: left !important;
      outline: none !important;
      
      &:hover,
      &:focus {
        border: none !important;
        border-width: 0 !important;
        background: transparent !important;
        background-color: transparent !important;
        outline: none !important;
      }
    }
    
    // input 元素本身也要透明
    :deep(input),
    :deep(input:hover),
    :deep(input:focus) {
      background: transparent !important;
      background-color: transparent !important;
    }
    
    // 占位符文本
    :deep(.el-select__placeholder) {
      line-height: inherit !important;
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      height: 100% !important;
      width: 100% !important;
      box-sizing: border-box !important;
      text-align: left !important;
    }
    
    // 选中的项
    :deep(.el-select__selected-item) {
      line-height: inherit !important;
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      height: 100% !important;
      width: 100% !important;
      box-sizing: border-box !important;
      text-align: left !important;
    }
    
    // 下拉图标
    :deep(.el-select__caret) {
      display: flex !important;
      align-items: center !important;
      flex-shrink: 0 !important;
    }
  }
  
  // ==================== ElInput 和 ElInputNumber 文本/数字输入框样式 ====================
  // 
  // 样式说明：
  // 1. 使用 absolute 定位完全填充单元格
  // 2. 通过透明背景确保不遮挡单元格边框
  // 3. 移除所有边框、阴影和轮廓，提供无缝编辑体验
  .excel-edit-input {
    position: absolute !important;
    top: 0 !important;
    left: -1px !important;
    right: -1px !important;
    bottom: 0 !important;
    width: calc(100% + 2px) !important;
    min-width: calc(100% + 2px) !important;
    max-width: calc(100% + 2px) !important;
    height: 100% !important;
    min-height: 32px !important;
    margin: 0 !important;
    padding: 0 !important;
    display: block !important;
    box-sizing: border-box !important;
    overflow: visible !important;
    z-index: 10 !important;
    visibility: visible !important;
    opacity: 1 !important;
    
    // 确保 Element Plus 组件的根元素（直接子元素）也有最小高度和宽度
    > * {
      min-height: 32px !important;
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      box-sizing: border-box !important;
    }
    
    // ElInput（文本输入框）样式
    :deep(.el-input) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      min-height: 32px !important;
      display: block !important;
      box-sizing: border-box !important;
    }
    
    :deep(.el-input__wrapper) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      border-color: transparent !important;
      background: transparent !important;
      background-color: transparent !important;
      box-shadow: none !important;
      border-radius: 0 !important;
      padding: 0 4px !important;
      margin: 0 !important;
      box-sizing: border-box !important;
      outline: none !important;
      
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
        border-color: transparent !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
      }
    }
    
    :deep(.el-input__inner) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      background: transparent !important;
      background-color: transparent !important;
      padding: 0 !important;
      margin: 0 !important;
      text-align: left !important;
      box-sizing: border-box !important;
      outline: none !important;
      
      &:hover,
      &:focus {
        border: none !important;
        border-width: 0 !important;
        background: transparent !important;
        background-color: transparent !important;
        outline: none !important;
      }
    }
    
    // input 元素本身也要透明
    :deep(input),
    :deep(input:hover),
    :deep(input:focus) {
      background: transparent !important;
      background-color: transparent !important;
    }
    
    // ElInputNumber（数字输入框）样式
    :deep(.el-input-number) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      min-height: 32px !important;
      display: flex !important;
      align-items: stretch !important;
      visibility: visible !important;
      opacity: 1 !important;
      text-align: left !important;
      box-sizing: border-box !important;
    }
    
    :deep(.el-input-number__input) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      flex: 1 !important;
      visibility: visible !important;
      opacity: 1 !important;
      text-align: left !important;
      box-sizing: border-box !important;
    }
    
    :deep(.el-input-number__input-wrapper) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      visibility: visible !important;
      opacity: 1 !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      border-color: transparent !important;
      background: transparent !important;
      background-color: transparent !important;
      box-shadow: none !important;
      border-radius: 0 !important;
      padding: 0 4px !important;
      margin: 0 !important;
      text-align: left !important;
      box-sizing: border-box !important;
      outline: none !important;
      
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
        border-color: transparent !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
      }
    }
    
    // 数字输入框也使用 el-input__wrapper，需要单独处理
    :deep(.el-input-number .el-input__wrapper) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      border-color: transparent !important;
      background: transparent !important;
      background-color: transparent !important;
      box-shadow: none !important;
      margin: 0 !important;
      outline: none !important;
      
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
        border-color: transparent !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
      }
    }
    
    // ElInputNumber 内部的 input 元素样式
    :deep(.el-input-number__input input) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      height: 100% !important;
      visibility: visible !important;
      opacity: 1 !important;
      color: inherit !important;
      background-color: transparent !important;
      border: none !important;
      border-width: 0 !important;
      border-top: none !important;
      border-right: none !important;
      border-bottom: none !important;
      border-left: none !important;
      box-shadow: none !important;
      padding: 0 !important;
      margin: 0 !important;
      text-align: left !important;
      box-sizing: border-box !important;
      outline: none !important;
      
      &:hover,
      &:focus {
        border: none !important;
        border-width: 0 !important;
        outline: none !important;
      }
    }
    
    // 覆盖 Element Plus 默认的右对齐样式
    :deep(.el-input-number__input input[type="text"]),
    :deep(.el-input-number__input input[type="number"]) {
      text-align: left !important;
    }
    
    :deep(.el-input-number__decrease),
    :deep(.el-input-number__increase) {
      display: none !important;
    }
  }
  
  // ==================== 编辑状态下的单元格样式 ====================
  // 
  // 编辑模式下单元格的通用样式设置
  .el-table__cell.editing-cell {
    padding: 0 !important;
    overflow: visible !important;
    position: relative;
    
    // 确保编辑模式下 .cell 也充满单元格
    :deep(.cell) {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      padding: 0 !important;
      margin: 0 !important;
      box-sizing: border-box !important;
      display: block !important;
      border: none !important;
      position: relative !important;
      // 编辑模式下需要明确高度，让 absolute 定位的子元素能正确计算
      // 使用固定最小高度，因为 absolute 定位的子元素不占位
      height: 100% !important;
      min-height: 32px !important;
    }
    
    // ElSelect 下拉框样式（独立设置，不受 ElInputNumber 影响）
    .excel-edit-select {
      // wrapper 背景透明，完全填充单元格而不会遮挡边框
      position: absolute !important;
      left: -1px !important;
      right: -1px !important;
      top: 0 !important;
      bottom: 0 !important;
      width: calc(100% + 2px) !important;
      min-width: calc(100% + 2px) !important;
      max-width: calc(100% + 2px) !important;
      height: 100% !important;
      display: block !important;
      z-index: 10 !important;
      
      // 强制 Element Plus Select 组件宽度
      :deep(.el-select) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        display: block !important;
        height: 100% !important;
        min-height: 32px !important;
      }
      
      :deep(.el-select__wrapper) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        height: 100% !important;
        min-height: 100% !important;
        max-height: 100% !important;
        border: none !important;
        border-width: 0 !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        border-left: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 4px !important;
        line-height: 1.5 !important;
        align-items: center !important;
        justify-content: flex-start !important;
        box-sizing: border-box !important;
        margin: 0 !important;
        text-align: left !important;
        outline: none !important;
        
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
          background: transparent !important;
          background-color: transparent !important;
          box-shadow: none !important;
          outline: none !important;
        }
      }
      
      :deep(.el-input__wrapper) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        min-height: 100% !important;
        max-height: 100% !important;
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        box-sizing: border-box !important;
        outline: none !important;
        
        &:hover,
        &:focus,
        &:focus-within {
          border: none !important;
          background: transparent !important;
          background-color: transparent !important;
          box-shadow: none !important;
          outline: none !important;
        }
      }
      
      :deep(.el-input__inner) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        min-height: 100% !important;
        max-height: 100% !important;
        border: none !important;
        border-width: 0 !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        border-left: none !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: inherit !important;
        display: flex !important;
        align-items: center !important;
        box-sizing: border-box !important;
        text-align: left !important;
        outline: none !important;
        
        &:hover,
        &:focus {
          border: none !important;
          border-width: 0 !important;
          outline: none !important;
        }
      }
      
      :deep(.el-select__placeholder),
      :deep(.el-select__selected-item) {
        line-height: inherit !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        height: 100% !important;
        width: 100% !important;
        box-sizing: border-box !important;
        text-align: left !important;
      }
      
      :deep(.el-select__caret) {
        display: flex !important;
        align-items: center !important;
        flex-shrink: 0 !important;
      }
    }
    
    // ElInput 和 ElInputNumber 文本/数字输入框样式（独立设置，不影响 ElSelect）
    // wrapper 背景透明，完全填充单元格而不会遮挡边框
    .excel-edit-input {
      position: absolute !important;
      top: 0 !important;
      left: -1px !important;
      right: -1px !important;
      bottom: 0 !important;
      width: calc(100% + 2px) !important;
      min-width: calc(100% + 2px) !important;
      max-width: calc(100% + 2px) !important;
      height: 100% !important;
      display: block !important;
      z-index: 10 !important;
      
      // 确保 Element Plus 组件的根元素（直接子元素）也有正确的宽度
      > * {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
      }
      
      // ElInput（文本输入框）样式
      :deep(.el-input) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        display: block !important;
        box-sizing: border-box !important;
      }
      
      :deep(.el-input__wrapper) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        border: none !important;
        border-width: 0 !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        border-left: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 4px !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        outline: none !important;
        
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
          background: transparent !important;
          background-color: transparent !important;
          box-shadow: none !important;
          outline: none !important;
        }
      }
      
      :deep(.el-input__inner) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        border: none !important;
        border-width: 0 !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        border-left: none !important;
        background: transparent !important;
        background-color: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        text-align: left !important;
        box-sizing: border-box !important;
        outline: none !important;
        
        &:hover,
        &:focus {
          border: none !important;
          border-width: 0 !important;
          background: transparent !important;
          background-color: transparent !important;
          outline: none !important;
        }
      }
      
      // 所有 input 元素都要透明
      :deep(input),
      :deep(input:hover),
      :deep(input:focus),
      :deep(textarea),
      :deep(textarea:hover),
      :deep(textarea:focus) {
        background: transparent !important;
        background-color: transparent !important;
      }
      
      // ElInputNumber（数字输入框）样式
      :deep(.el-input-number) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        min-height: 32px !important;
        display: flex !important;
        align-items: stretch !important;
        visibility: visible !important;
        opacity: 1 !important;
        text-align: left !important;
        box-sizing: border-box !important;
      }
      
      :deep(.el-input-number__input) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        flex: 1 !important;
        visibility: visible !important;
        opacity: 1 !important;
        text-align: left !important;
        box-sizing: border-box !important;
      }
      
      :deep(.el-input-number__input-wrapper) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        visibility: visible !important;
        opacity: 1 !important;
        border: none !important;
        border-width: 0 !important;
        border-top: none !important;
        border-right: none !important;
        border-bottom: none !important;
        border-left: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 4px !important;
        margin: 0 !important;
        text-align: left !important;
        box-sizing: border-box !important;
        outline: none !important;
        
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
          background: transparent !important;
          background-color: transparent !important;
          box-shadow: none !important;
          outline: none !important;
        }
      }
      
      // ElInputNumber 内部的 input 元素样式
      :deep(.el-input-number__input input) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        height: 100% !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: inherit !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        text-align: left !important;
        box-sizing: border-box !important;
        outline: none !important;
        
        &:hover,
        &:focus {
          border: none !important;
          background: transparent !important;
          background-color: transparent !important;
          outline: none !important;
        }
      }
      
      // 覆盖 Element Plus 默认的右对齐样式
      :deep(.el-input-number__input input[type="text"]),
      :deep(.el-input-number__input input[type="number"]) {
        text-align: left !important;
      }
    }
  }
  
  // 表头样式
  .el-table__header {
    th {
      background-color: #fafafa;
      font-weight: 600;
      border-bottom: 2px solid #e8e8e8;
      text-align: center !important;
    }
  }
  
  // ==================== 图片列样式 ====================
  // 图片列始终显示编辑模式（类似 BaseFree.vue 的新增/修改模式）
  // image列随内容增长自动伸长，以容纳内容
  .excel-edit-image {
    position: relative !important;
    width: 100% !important;
    min-width: 100% !important;
    max-width: none !important; // 允许超出，随内容增长
    height: auto !important; // 改为 auto，让高度由内容决定
    min-height: auto !important; // 移除固定的 min-height
    margin: 0 !important;
    padding: 4px !important;
    display: block !important;
    box-sizing: border-box !important;
    overflow: visible !important; // 改为 visible，不显示滚动条，让内容自然撑开
    background: transparent !important;
  }
  
  // 确保 image 列的单元格可以自动伸长
  // 使用更兼容的方式，通过类名选择器
  .el-table__cell {
    // 如果单元格包含图片编辑组件，允许自动伸长
    &:has(.excel-edit-image) {
      height: auto !important;
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
// 
// 确保 .cell 和 .excel-cell 在所有情况下都有正确的尺寸
.excel-table {
  // 所有单元格（包括编辑和非编辑模式）的 .cell 样式
  .el-table__cell .cell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    display: block !important;
    border: none !important;
    position: relative !important;
    min-height: 100% !important;
  }
  
  // 编辑模式下 .cell 需要明确高度
  .el-table__cell.editing-cell .cell {
    height: 100% !important;
    min-height: 32px !important;
  }
  
  // 非编辑模式下的 .excel-cell 样式
  .el-table__cell:not(.editing-cell) .cell .excel-cell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    min-height: 100% !important;
    padding-top: 2px !important;
    padding-right: 5px !important;
    padding-bottom: 2px !important;
    padding-left: 5px !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    display: block !important;
    position: relative !important;
  }
  
  // 更具体的选择器，确保样式优先级
  tbody .el-table__cell .cell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 100% !important;
  }
}

// ==================== 全局样式：编辑输入框宽度设置 ====================
// 
// 使用全局样式确保样式优先级足够高，覆盖 Element Plus 默认样式
// 注意：这些样式与 scoped 样式中的设置保持一致，确保在所有情况下都能正确渲染
.excel-table {
  .el-table__cell.editing-cell {
    // 确保所有输入组件的宽度设置
    .excel-edit-input,
    .excel-edit-select {
      > * {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
      }
      
      :deep(.el-input),
      :deep(.el-select),
      :deep(.el-input-number),
      :deep(.el-input__wrapper),
      :deep(.el-select__wrapper),
      :deep(.el-input-number__input),
      :deep(.el-input-number__input-wrapper),
      :deep(.el-input__inner) {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
      }
    }
  }
}
</style>
