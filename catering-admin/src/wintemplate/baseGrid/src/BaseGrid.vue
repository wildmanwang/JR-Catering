<script setup lang="tsx">
import { unref, ref, reactive, watch, onMounted, onBeforeUnmount, nextTick, toRaw, watchEffect, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTable } from '@/hooks/web/useTable'
import { Table, TableColumn } from '@/components/Table'
import { ElCard, ElMenu, ElMenuItem, ElMessage } from 'element-plus'
import { BaseButton } from '@/components/Button'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PrompInfo } from '@/components/PrompInfo'
import { QueryBar, type QueryCondition } from '@/components/QueryBar'
import { StatusStoragePlus, type StatusStoreItem } from '@/components/StatusStoragePlus'
import { ImageSingle } from '@/components/ImageSingle'
import { BaseFree, type FreeFormField, type FreeTab } from '@/wintemplate/baseFree'
import { formatDataItem } from '@/utils/dsOptions'

/**
 * 根据格式配置生成 label 文本（使用 dsOptions.ts 的 formatDataItem）
 * @param dataSet - 数据集
 * @param uniqueId - 唯一标识
 * @param format - 格式配置
 * @returns 生成的 label 文本
 */
const generateLabelByFormat = (dataSet: any[], uniqueId: number | string, format: Array<['field' | 'value', string]>): string => {
  return formatDataItem(dataSet, uniqueId, format)
}
import { processImageFields, normalizeImageUrl, ImageQuerySuffix, getImageUrlWithSuffix } from '@/utils/imageList'

// ==================== 常量定义 ====================
/** 默认图片路径 */
const DEFAULT_IMAGE = '/src/assets/imgs/no_image.png'

// ==================== 类型定义 ====================
/** ButtonPlus 组件的按钮类型 */
type ButtonPlusSType =
  | 'new'
  | 'modify'
  | 'delete'
  | 'save'
  | 'copy'
  | 'batch'
  | 'query'
  | 'select'
  | 'refresh'
  | 'ok'
  | 'cancel'
  | 'import'
  | 'export'
  | 'print'
  | 'setting'
  | 'return'
  | 'normal'

/** 操作按钮选项 */
interface ActionOption {
  type: 'edit' | 'delete' | 'other' // 操作类型
  label?: string // 自定义按钮文字
  onClick?: (row: any) => void // 点击事件回调
  permission?: string[] // 权限控制
  [key: string]: any // 其他按钮属性
}

/** 工具栏按钮配置 */
interface ToolbarButton {
  stype: ButtonPlusSType // 按钮类型
  label?: string // 自定义按钮文字
  onClick?: () => void // 点击事件回调
  permission?: string[] // 权限控制
  // ==================== import 按钮专用配置 ====================
  /** 导入页面路由路径（如果配置，将启用导入功能，优先级高于 props.importRoute） */
  importRoute?: string
  // 注意：importStorageKey 会根据 windowId 自动生成，无需配置
  // 注意：importLabel 会自动使用按钮的 label，无需单独配置
  [key: string]: any // 其他按钮属性
}

/** 表格列配置 */
interface GridColumn {
  field: string // 字段名
  label: string // 列标题
  type?: 'selection' | 'image' | 'text' | 'status' | 'action' // 列类型
  width?: string | number // 列宽度
  minWidth?: string | number // 最小宽度
  align?: 'left' | 'center' | 'right' // 单元格内容对齐方式
  headerAlign?: 'left' | 'center' | 'right' // 表头对齐方式，默认 center
  fixed?: boolean | 'left' | 'right' // 固定列
  show?: boolean // 是否显示
  showConfig?: boolean // 是否可配置显示/隐藏（true=可在右上角配置显示/隐藏，false=不可配置固定显示），默认 true
  formatter?: (row: any) => any // 格式化函数
  // 图片列专用配置
  imageField?: string // 图片字段名，默认使用 field（支持 url 字符串或 url 数组，ImageSingle 组件会自动处理）
  imageSize?: 'normal' | 'small' // 图片尺寸：normal（100px*100px）或 small（60px*60px），默认 normal
  // 状态列专用配置
  statusOptions?: Array<{ label: string; value: any }> | (() => Array<{ label: string; value: any }>) // 状态映射选项
  /** 选项数据获取接口（用于自动获取该字段的选项数据，供 statusOptions、fieldOptions、searchConditions 使用） */
  optionsApi?: () => Promise<{ data?: any[]; code?: number; [key: string]: any }> // 返回格式：{ data: [...], code: 200 } 或直接返回数组
  /** 选项数据转换函数（将 API 返回的数据转换为标准格式，如果不提供则使用默认转换） */
  optionsTransform?: (data: any) => Array<{ label: string; value: any }> // 默认：假设返回的是 { data: [...] } 格式
  /** 选项数据的 id 字段名（用于简化配置，如果不提供 optionsTransform，将使用此字段作为唯一标识） */
  optionsIdField?: string // 例如：'id'
  /** 选项数据的 label 字段配置（用于简化配置，如果不提供 optionsTransform，将使用此配置生成 label） */
  optionsLabelFields?: Array<string> // 例如：['name_unique'] 或 ['固定字符串', 'name_unique']，数组中的项目可以是固定字符串或字段名（已废弃，请使用 optionsLabelFormat）
  /** 选项数据的 label 格式配置（用于简化配置，使用 dsOptions.ts 的格式） */
  optionsLabelFormat?: Array<['field' | 'value', string]> // 例如：[['field', 'name_unique'], ['value', '-'], ['field', 'status']]
  // 操作列专用配置
  actionSlots?: (data: any) => JSX.Element | JSX.Element[] | null // 自定义操作插槽
  actionOptions?: ActionOption[] // 操作按钮配置
  onEdit?: (row: any) => void // 编辑回调
  onDelete?: (row: any) => void // 删除回调
}

/** 查询条件配置（使用 QueryCondition 类型） */
type SearchCondition = QueryCondition

/** 快捷查询列表项 */
interface QuickQueryItem {
  id: number | string | null // 项的唯一标识（null 表示"全部"选项）
  label: string // 显示名称
  [key: string]: any // 其他属性
}

/** 快捷查询列表配置 */
interface QuickQueryList {
  title: string // 列表标题
  data?: QuickQueryItem[] | (() => Promise<QuickQueryItem[]>) // 数据数组或异步获取函数（已废弃，请使用 dataApi）
  dataApi?: () => Promise<{ data?: any[]; code?: number; [key: string]: any }> // 数据获取接口（返回格式：{ data: [...] } 或直接返回数组）
  field: string // 查询字段名（用于更新查询参数）
  showAllOption?: boolean // 是否显示"（全部）"选项，默认 true
  allOptionLabel?: string // "（全部）"选项的显示文字，默认 "（全部）"
  allOptionValue?: number | string | null // "（全部）"选项的值，默认 null
  /** id 字段名（用于简化配置，如果不提供 data，将使用此字段作为唯一标识） */
  idField?: string // 例如：'id'
  /** label 字段配置（用于简化配置，如果不提供 data，将使用此配置生成 label） */
  labelFields?: Array<string> // 例如：['name_unique'] 或 ['固定字符串', 'name_unique']（已废弃，请使用 labelFormat）
  /** label 格式配置（用于简化配置，使用 dsOptions.ts 的格式） */
  labelFormat?: Array<['field' | 'value', string]> // 例如：[['field', 'name_unique'], ['value', '-'], ['field', 'status']]
}

/** 组件 Props */
interface Props {
  columns: GridColumn[] // 列配置数组
  fetchDataApi: (params: { page: number; limit: number; [key: string]: any }) => Promise<{ data: any[]; count: number }> // 数据获取接口
  fetchDelApi?: (ids: string[] | number[] | number | string) => Promise<boolean | { code?: number; [key: string]: any }> // 删除接口（可选），支持返回 boolean 或响应对象（会自动检查 code === 200）
  nodeKey?: string // 行键，用于多选，默认 'id'
  showAction?: boolean // 是否显示操作栏，默认 false
  reserveSelection?: boolean // 是否保留选择（分页后保留），默认 false
  searchParams?: Record<string, any> // 搜索参数（已废弃，请使用 searchConditions）
  toolbarButtons?: ToolbarButton[] // 工具栏按钮配置
  searchConditions?: SearchCondition[] // 查询条件配置
  quickQueryList?: QuickQueryList // 左侧快捷查询列表配置
  /** 窗口标识（用于 StatusStoragePlus 的唯一标识，使用方需要赋值） */
  windowId?: string
  // ==================== 弹窗相关配置 ====================
  /** 页面标题（用于弹窗标题） */
  pageTitle?: string
  /** 表单字段配置（用于新增/编辑/查看弹窗） */
  formSchema?: FreeFormField[]
  /** 表单验证规则 */
  rules?: Record<string, any>
  /** Tab 配置 */
  tabs?: FreeTab[]
  /** 字段选项数据映射（字段名 -> 选项数组或函数），用于从主窗口传递下拉框选项，避免重复请求 */
  fieldOptions?: Record<string, any[] | (() => any[])>
  /** 新增接口 */
  addApi?: (data: any) => Promise<any>
  /** 编辑接口 */
  editApi?: (data: any) => Promise<any>
  /** 提交接口（如果提供，将优先使用此接口，会根据 mode 自动调用 addApi 或 editApi） */
  submitApi?: (data: any, mode?: 'add' | 'edit') => Promise<any>
  /** 保存成功回调 */
  onSuccess?: () => void
  /** 取消回调 */
  onCancel?: () => void
  /** 是否启用查看功能，默认 true */
  enableView?: boolean
  /** 是否启用新增功能，默认 true */
  enableAdd?: boolean
  /** 是否启用编辑功能，默认 true */
  enableEdit?: boolean
  /** 是否启用删除功能，默认 true */
  enableDelete?: boolean
  // ==================== 导入相关配置 ====================
  /** 导入页面路由路径（如果配置，将启用导入功能） */
  importRoute?: string
  /** 导入数据存储的 sessionStorage key（如果不提供，将使用默认格式：IMPORT_${windowId}_PAYLOAD） */
  importStorageKey?: string
  /** 行数据转换为导入格式的函数（如果不提供，将使用标准转换：自动处理图片、数字等） */
  importTransform?: (row: any) => any
  /** 导入按钮的标签（用于提示信息） */
  importLabel?: string
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  nodeKey: 'id',
  showAction: false,
  reserveSelection: false,
  searchParams: () => ({}),
  searchConditions: () => [],
  windowId: '',
  rules: () => ({}),
  tabs: () => [
    { label: '基础信息', name: 'basic' },
    { label: '操作日志', name: 'log' }
  ],
  fieldOptions: () => ({}),
  enableView: true,
  enableAdd: true,
  enableEdit: true,
  enableDelete: true
})

// ==================== 页面状态管理 ====================
/** 页面加载状态，用于避免闪屏 */
const pageReady = ref(false)

/** 防止恢复状态时重复调用 getList() 的标志 */
const isRestoringState = ref(false)

// ==================== 选项数据管理 ====================
/** 存储各字段的选项数据（字段名 -> 选项数组） */
const fieldOptionsData = ref<Record<string, any[]>>({})

/**
 * 根据配置生成 label 文本
 * @param item - 数据项
 * @param labelFields - label 字段配置数组
 * @returns 拼接后的 label 文本
 */
const generateLabel = (item: any, labelFields: string[]): string => {
  return labelFields
    .map((field) => {
      // 如果字段名在数据项中存在，使用字段值；否则作为固定字符串使用
      return item.hasOwnProperty(field) ? String(item[field] || '') : field
    })
    .filter(Boolean) // 过滤空值
    .join('') // 拼接
}

/**
 * 根据列配置转换选项数据
 * @param col - 列配置
 * @param rawData - 原始数据数组
 * @returns 转换后的选项数据数组
 */
const transformOptionsByConfig = (col: GridColumn, rawData: any[]): Array<{ label: string; value: any; [key: string]: any }> => {
  if (!rawData || rawData.length === 0) {
    return []
  }
  
  // 如果提供了自定义转换函数，优先使用
  if (col.optionsTransform && typeof col.optionsTransform === 'function') {
    return col.optionsTransform(rawData)
  }
  
  // 如果配置了 optionsLabelFormat，使用 dsOptions.ts 格式
  if (col.optionsIdField && col.optionsLabelFormat && col.optionsLabelFormat.length > 0) {
    return rawData.map((item: any) => {
      const id = item[col.optionsIdField!]
      const label = generateLabelByFormat(rawData, id, col.optionsLabelFormat!)
      
      // 返回标准格式，同时保留原始数据
      return {
        id,
        label,
        value: id, // 为了兼容，同时提供 value
        ...item // 保留原始数据，供表单下拉框使用
      }
    })
  }
  
  // 如果配置了 optionsIdField 和 optionsLabelFields（旧格式，向后兼容）
  if (col.optionsIdField && col.optionsLabelFields && col.optionsLabelFields.length > 0) {
    return rawData.map((item: any) => {
      const id = item[col.optionsIdField!]
      const label = generateLabel(item, col.optionsLabelFields!)
      
      // 返回标准格式，同时保留原始数据
      return {
        id,
        label,
        value: id, // 为了兼容，同时提供 value
        ...item // 保留原始数据，供表单下拉框使用
      }
    })
  }
  
  // 默认转换：尝试自动识别常见格式
  if (rawData.length > 0 && !rawData[0].hasOwnProperty('label') && !rawData[0].hasOwnProperty('value')) {
    // 尝试自动转换常见格式
    if (rawData[0].hasOwnProperty('id') && rawData[0].hasOwnProperty('name_unique')) {
      // 厨部格式：{ id, name_unique, ... }
      return rawData.map((item: any) => ({
        id: item.id,
        label: item.name_unique,
        value: item.id,
        ...item
      }))
    } else if (rawData[0].hasOwnProperty('value') || rawData[0].hasOwnProperty('label')) {
      // 已经是标准格式或接近标准格式
      return rawData.map((item: any) => ({
        id: item.id,
        label: item.label || item.name_unique || item.name || String(item.value || item.id),
        value: item.value !== undefined ? item.value : item.id,
        ...item
      }))
    }
  }
  
  // 如果已经是标准格式，直接返回
  return rawData
}

/**
 * 初始化选项数据（从列配置中收集 optionsApi 并获取数据）
 */
const initFieldOptions = async () => {
  // 收集所有需要获取选项数据的列
  const optionsApiMap = new Map<string, { api: () => Promise<any>; col: GridColumn }>()
  
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
        // 如果直接返回数组
        rawOptions = res
      } else if (res?.data && Array.isArray(res.data)) {
        // 如果返回 { data: [...] } 格式
        rawOptions = res.data
      } else {
        console.warn(`字段 ${field} 的选项数据格式不正确：`, res)
        rawOptions = []
      }
      
      // 根据列配置转换数据
      const transformedOptions = transformOptionsByConfig(col, rawOptions)
      
      fieldOptionsData.value[field] = transformedOptions
    } catch (err) {
      console.error(`获取字段 ${field} 的选项数据失败：`, err)
      fieldOptionsData.value[field] = []
    }
  })
  
  await Promise.all(promises)
}

// ==================== 导入功能 ====================
const router = useRouter()

/**
 * 安全数字转换函数
 * @param value - 要转换的值
 * @param fallback - 转换失败时的默认值，默认为 null
 * @returns 转换后的数字或默认值
 */
const safeNumber = (value: any, fallback: any = null): any => {
  if (value === null || value === undefined) return fallback
  const num = Number(value)
  return Number.isNaN(num) ? fallback : num
}

/**
 * 规范化图片路径
 * 移除查询参数，添加 ?original 后缀
 * @param img - 图片路径字符串
 * @returns 规范化后的图片路径
 */
const normalizeImage = (img: string): string => {
  if (typeof img !== 'string' || !img.length) return ''
  const [path] = img.split('?')
  return path ? getImageUrlWithSuffix(path, ImageQuerySuffix.ORIGINAL) : ''
}

/**
 * 检测字段是否为图片字段
 * @param fieldName - 字段名
 * @returns 是否为图片字段
 */
const isImageField = (fieldName: string): boolean => {
  const imageFieldPatterns = [
    /_images?$/i,      // 以 _images 或 _image 结尾
    /^images?$/i,       // 直接是 images 或 image
    /_image_/i,        // 包含 _image_
    /_picture/i,        // 包含 _picture
    /_photo/i,          // 包含 _photo
    /_img/i             // 包含 _img
  ]
  return imageFieldPatterns.some(pattern => pattern.test(fieldName))
}

/**
 * 标准数据转换函数
 * 自动处理图片字段、数字字段等，将行数据转换为导入格式
 * @param row - 行数据
 * @returns 转换后的数据
 */
const standardImportTransform = (row: any): any => {
  if (!row) return null
  
  const transformed: any = { ...row }
  
  // 遍历所有字段，进行标准处理
  Object.keys(row).forEach((key) => {
    const value = row[key]
    
    // 处理图片字段
    if (isImageField(key)) {
      if (Array.isArray(value)) {
        // 数组格式的图片：过滤有效图片，规范化路径
        const validImages = value.filter((img: any) => typeof img === 'string' && img)
        // 创建两个版本：display（原始）和 normalized（规范化）
        transformed[`${key}_display`] = [...validImages]
        transformed[key] = validImages.map(normalizeImageUrl).filter(Boolean)
      } else if (typeof value === 'string' && value) {
        // 字符串格式的图片：规范化路径
        transformed[key] = normalizeImageUrl(value)
      }
    }
    
    // 处理常见的数字字段（可选：如果需要，可以自动转换）
    // 这里不自动转换，因为不同业务场景的数字字段处理方式可能不同
    // 如果需要，可以通过 importTransform 自定义处理
  })
  
  // 添加 action 字段（用于导入页面的操作标识）
  if (transformed.action === undefined) {
    transformed.action = null
  }
  
  return transformed
}

/**
 * 打开导入窗口
 * 
 * 工作流程：
 * 1. 获取当前选中的记录
 * 2. 将记录转换为导入格式（如果提供了 importTransform）
 * 3. 保存到 sessionStorage（自动根据 windowId 生成 storageKey）
 * 4. 导航到导入页面
 * 
 * 如果没有选中记录，会打开空白的批量维护页
 * @param importRoute - 导入页面路由路径（如果提供，将优先使用；否则使用 props.importRoute）
 * @param importLabel - 导入按钮的标签（如果提供，将使用；否则使用 props.importLabel 或 '数据'）
 */
const openImport = async (importRoute?: string, importLabel?: string) => {
  // 优先使用传入的参数，其次使用 props 中的配置
  const route = importRoute || props.importRoute
  // 自动根据 windowId 生成 storageKey（不再从参数或 props 获取）
  const storageKey = `IMPORT_${props.windowId || 'BASE_GRID'}_PAYLOAD`
  // 优先使用传入的 label，其次使用 props.importLabel，最后使用默认值
  const label = importLabel || props.importLabel || '数据'
  
  if (!route) {
    console.warn('未配置导入路由（importRoute），无法打开导入窗口')
    return
  }
  
  try {
    // 获取选中的记录
    const selections = await tableMethods.getSelections()
    
    if (!selections?.length) {
      // 如果没有选中记录，打开空白导入页，设置标记表示需要插入空行
      sessionStorage.setItem(storageKey, JSON.stringify({ data: [], _addEmptyRow: true }))
      ElMessage.info(`未选择${label}，将打开空白批量维护页`)
      router.push(route)
      return
    }
    
    // 转换数据格式
    let payload: any[] = []
    if (props.importTransform && typeof props.importTransform === 'function') {
      // 使用自定义转换函数
      payload = selections
        .map(props.importTransform)
        .filter((item: any) => item !== null)
    } else {
      // 使用标准转换函数（自动处理图片、数字等）
      payload = selections
        .map(standardImportTransform)
        .filter((item: any) => item !== null)
    }
    
    if (!payload.length) {
      // 数据为空，设置标记表示需要插入空行
      sessionStorage.setItem(storageKey, JSON.stringify({ data: [], _addEmptyRow: true }))
      ElMessage.warning(`所选${label}异常，已打开空白批量维护页`)
      router.push(route)
      return
    }
    
    // 保存到 sessionStorage 并导航到导入页面，设置标记表示需要插入空行
    sessionStorage.setItem(storageKey, JSON.stringify({ data: payload, _addEmptyRow: true }))
    router.push(route)
  } catch (err) {
    console.error('打开导入窗口失败：', err)
    ElMessage.error('打开导入窗口失败，请稍后重试')
  }
}

/**
 * 合并后的字段选项（合并 props.fieldOptions 和自动获取的 fieldOptionsData）
 */
const mergedFieldOptions = computed(() => {
  const merged: Record<string, any[] | (() => any[])> = { ...props.fieldOptions }
  
  // 将自动获取的选项数据添加到合并结果中
  Object.keys(fieldOptionsData.value).forEach((field) => {
    if (fieldOptionsData.value[field] && fieldOptionsData.value[field].length > 0) {
      // 如果 props.fieldOptions 中已有该字段，不覆盖；否则使用自动获取的数据
      if (!merged[field]) {
        merged[field] = () => fieldOptionsData.value[field]
      }
    }
  })
  
  return merged
})

/**
 * 处理后的查询条件（自动填充选项数据）
 */
const processedSearchConditions = computed(() => {
  if (!props.searchConditions || props.searchConditions.length === 0) {
    return []
  }
  
  return props.searchConditions.map((condition) => {
    // 如果查询条件没有配置 options，但字段有自动获取的选项数据，则使用自动获取的数据
    if (!condition.options && fieldOptionsData.value[condition.field] && fieldOptionsData.value[condition.field].length > 0) {
      return {
        ...condition,
        options: () => fieldOptionsData.value[condition.field]
      }
    }
    return condition
  })
})

// ==================== 弹窗状态管理 ====================
/** 弹窗显示状态 */
const dialogVisible = ref(false)
/** 弹窗模式：'add' | 'edit' | 'view' */
const dialogMode = ref<'add' | 'edit' | 'view'>('add')
/** 当前行数据（编辑/查看时使用） */
const currentRow = ref<any>(null)
/** 保存按钮加载状态 */
const saveLoading = ref(false)

/** StatusStoragePlus 组件引用 */
const statusStoragePlusRef = ref<InstanceType<typeof StatusStoragePlus>>()

/** QueryBar 组件引用 */
const queryBarRef = ref<InstanceType<typeof QueryBar>>()

/** QueryBar 注册状态 */
const queryBarRegistered = ref(false)

// ==================== 查询条件 ====================
/** 查询参数（内部使用） */
const internalSearchParams = ref<Record<string, any>>({})

/** 表单显示值（用户输入的所有条件，包括未执行的） */
const formDisplayParams = ref<Record<string, any>>({})

/**
 * 处理查询
 */
const handleSearch = async (data: any) => {
  const rawData = toRaw(data)
  
  // 更新查询参数（已执行的查询条件）
  internalSearchParams.value = { ...rawData }
  
  // 同时更新表单显示值
  const filteredParams: Record<string, any> = {}
  Object.keys(rawData).forEach(key => {
    const value = rawData[key]
    // 只保存非空值
    if (value !== null && value !== undefined && value !== '' && 
        !(Array.isArray(value) && value.length === 0)) {
      filteredParams[key] = value
    }
  })
  formDisplayParams.value = filteredParams
  
  currentPage.value = 1
  statusStoragePlusRef.value?.saveState()
  getList()
}

/**
 * 处理 QueryBar 注册事件
 */
const handleQueryBarRegister = async () => {
  queryBarRegistered.value = true
}

/**
 * 处理 QueryBar 字段变化事件
 * 只更新表单显示值（formDisplayParams），不更新已执行的查询条件（internalSearchParams）
 */
const handleQueryBarFieldChange = (field: string, value: any) => {
  if (!pageReady.value) {
    return
  }
  
  // 只更新 formDisplayParams（表单显示值），不更新 internalSearchParams
  if (!formDisplayParams.value) {
    formDisplayParams.value = {}
  }
  
  // 如果值不为空，保存；如果为空，删除该字段
  if (value !== null && value !== undefined && value !== '' && 
      !(Array.isArray(value) && value.length === 0)) {
    formDisplayParams.value[field] = value
  } else {
    delete formDisplayParams.value[field]
  }
  
  // 自动保存状态（通过 StatusStoragePlus）
  statusStoragePlusRef.value?.saveState()
}

/**
 * 处理重置
 */
const handleReset = async () => {
  internalSearchParams.value = {}
  formDisplayParams.value = {}
  currentPage.value = 1
  statusStoragePlusRef.value?.saveState()
  getList()
}

// ==================== 快捷查询列表 ====================
/** 快捷查询列表数据 */
const quickQueryData = ref<QuickQueryItem[]>([])
/** 当前选中的快捷查询项索引 */
const activeQuickQueryIndex = ref<string>('0')

/**
 * 初始化快捷查询列表
 */
const initQuickQueryList = async () => {
  if (!props.quickQueryList) {
    return
  }

  const config = props.quickQueryList
  let data: QuickQueryItem[] = []

  // 获取数据（优先级：config.dataApi > config.data > 列定义中的 optionsApi）
  if (config.dataApi && typeof config.dataApi === 'function') {
    // 使用 dataApi 获取数据
    try {
      const res = await config.dataApi()
      let rawData: any[] = []
      
      // 处理响应数据（支持多种格式）
      if (Array.isArray(res)) {
        // 格式1: 直接返回数组
        rawData = res
      } else if (res && typeof res === 'object') {
        // 格式2: 返回对象，数据在 data 字段中
        if (Array.isArray(res.data)) {
          rawData = res.data
        } else if (Array.isArray((res as any).list)) {
          // 格式3: 数据在 list 字段中
          rawData = (res as any).list
        } else {
          console.warn('快捷查询列表数据格式不正确，期望数组或包含 data/list 字段的对象：', res)
          rawData = []
        }
      } else {
        console.warn('快捷查询列表数据格式不正确：', res)
        rawData = []
      }
      
      // 根据配置转换数据
      if (config.idField && config.labelFormat && config.labelFormat.length > 0) {
        // 使用 dsOptions.ts 格式转换
        data = rawData.map((item: any) => {
          const id = item[config.idField!]
          return {
            id,
            label: generateLabelByFormat(rawData, id, config.labelFormat!)
          }
        })
      } else if (config.idField && config.labelFields && config.labelFields.length > 0) {
        // 使用旧格式转换（向后兼容）
        data = rawData.map((item: any) => ({
          id: item[config.idField!],
          label: generateLabel(item, config.labelFields!)
        }))
      } else {
        // 默认转换：尝试自动识别格式
        if (rawData.length > 0) {
          if (rawData[0].hasOwnProperty('id') && rawData[0].hasOwnProperty('label')) {
            // 已经是标准格式
            data = rawData.map((item: any) => ({
              id: item.id,
              label: item.label
            }))
          } else if (rawData[0].hasOwnProperty('id') && rawData[0].hasOwnProperty('name_unique')) {
            // 常见格式：{ id, name_unique, ... }
            data = rawData.map((item: any) => ({
              id: item.id,
              label: item.name_unique
            }))
          } else {
            // 尝试其他格式
            data = rawData.map((item: any) => ({
              id: item.id !== undefined ? item.id : item.value,
              label: item.label || item.name_unique || item.name || String(item.id !== undefined ? item.id : item.value)
            }))
          }
        }
      }
    } catch (err) {
      console.error('获取快捷查询列表数据失败：', err)
      data = []
    }
  } else if (typeof config.data === 'function') {
    // 兼容旧的 data 函数方式
    try {
      data = await config.data()
    } catch (err) {
      console.error('获取快捷查询列表数据失败：', err)
      data = []
    }
  } else if (config.data && Array.isArray(config.data)) {
    // 兼容旧的 data 数组方式
    data = config.data
  } else {
    // 如果 quickQueryList 没有配置 data 或 dataApi，尝试从列定义中获取
    const fieldColumn = props.columns.find((col) => col.field === config.field)
    if (fieldColumn?.optionsApi && fieldOptionsData.value[config.field] && fieldOptionsData.value[config.field].length > 0) {
      // 使用列定义中自动获取的数据
      data = fieldOptionsData.value[config.field].map((item: any) => ({
        id: item.id !== undefined ? item.id : item.value,
        label: item.label || item.name_unique || String(item.id !== undefined ? item.id : item.value)
      }))
    } else {
      data = []
    }
  }

  // 添加"（全部）"选项
  const showAllOption = config.showAllOption !== false // 默认显示
  if (showAllOption) {
    const allOption: QuickQueryItem = {
      id: config.allOptionValue !== undefined ? config.allOptionValue : null,
      label: config.allOptionLabel || '（全部）'
    }
    quickQueryData.value = [allOption, ...data]
  } else {
    quickQueryData.value = data
  }

  // 只有在没有保存的索引时才初始化选中项为 '0'
  // 如果有保存的索引，会在状态恢复时设置
  if (!savedActiveQuickQueryIndex.value) {
    activeQuickQueryIndex.value = '0'
  }
  
  // 数据加载完成后，设置菜单高度
  await nextTick()
  setMenuMaxHeight()
}

/**
 * 恢复快捷查询选择（不触发查询，仅更新状态）
 */
const restoreQuickQuerySelect = (index: string) => {
  if (!props.quickQueryList) {
    return
  }

  const selected = quickQueryData.value.find((item, idx) => idx.toString() === index)
  if (selected) {
    activeQuickQueryIndex.value = index
    const config = props.quickQueryList
    const field = config.field

    // 更新查询参数（不触发查询）
    if (selected.id === null || selected.id === undefined || selected.id === '') {
      // "（全部）"选项，删除该字段
      delete internalSearchParams.value[field]
      delete formDisplayParams.value[field]
    } else {
      // 设置查询字段值
      internalSearchParams.value[field] = selected.id
      formDisplayParams.value[field] = selected.id
    }
  }
}

/**
 * 处理快捷查询列表选择（用户操作，会触发查询）
 */
const handleQuickQuerySelect = async (index: string) => {
  if (!props.quickQueryList) {
    return
  }

  const selected = quickQueryData.value.find((item, idx) => idx.toString() === index)
  if (selected) {
    activeQuickQueryIndex.value = index
    const config = props.quickQueryList
    const field = config.field

    // 更新查询参数
    if (selected.id === null || selected.id === undefined || selected.id === '') {
      // "（全部）"选项，删除该字段
      delete internalSearchParams.value[field]
      delete formDisplayParams.value[field]
    } else {
      // 设置查询字段值
      internalSearchParams.value[field] = selected.id
      formDisplayParams.value[field] = selected.id
    }

    // 重置到第一页并刷新列表
    currentPage.value = 1
    statusStoragePlusRef.value?.saveState()
    getList()
  }
}

// ==================== ElMenu 高度处理 ====================
/** ElMenu 容器引用 */
const quickQueryMenuWrapperRef = ref<HTMLElement>()
/** ElMenu 组件引用 */
const quickQueryMenuRef = ref<InstanceType<typeof ElMenu>>()

/** 上次设置的高度，用于避免重复设置 */
let lastSetHeight = 0
/** 是否正在设置高度，用于防止死循环 */
let isSettingHeight = false

/**
 * 设置 ElMenu 的最大化高度
 */
const setMenuMaxHeight = async () => {
  if (!props.quickQueryList || !quickQueryMenuWrapperRef.value) {
    return
  }
  
  if (isSettingHeight) {
    return
  }

  isSettingHeight = true
  
  try {
    await nextTick()
    await nextTick() // 确保 DOM 完全渲染
    
    const wrapper = quickQueryMenuWrapperRef.value
    
    // 获取整个布局链的元素
    const baseGridWrapper = wrapper.closest('.base-grid-wrapper') as HTMLElement
    const contentArea = wrapper.closest('.base-grid-content-area') as HTMLElement
    const quickQueryList = wrapper.closest('.base-grid-quick-query-list') as HTMLElement
    
    // quickQueryList 本身就是 ElCard (DIV.el-card)
    const card = quickQueryList
    const cardBody = card?.querySelector('.el-card__body') as HTMLElement
    const queryBar = baseGridWrapper?.querySelector('.query-bar') as HTMLElement
    
    // 向上查找 ContentWrap（从 baseGridWrapper 向上查找）
    let contentWrap: HTMLElement | null = null
    let currentElement: HTMLElement | null = baseGridWrapper
    while (currentElement && !contentWrap) {
      contentWrap = currentElement.closest('.content-wrap') as HTMLElement
      if (!contentWrap && currentElement.parentElement) {
        currentElement = currentElement.parentElement as HTMLElement
      } else {
        break
      }
    }
    const contentWrapCardBody = contentWrap?.querySelector('.el-card__body') as HTMLElement
    
    if (!cardBody || !quickQueryList || !contentArea || !baseGridWrapper) {
      return
    }

    // 获取必要的高度信息
    const contentWrapCardBodyRect = contentWrapCardBody?.getBoundingClientRect()
    const baseGridWrapperRect = baseGridWrapper.getBoundingClientRect()
    const contentAreaRect = contentArea.getBoundingClientRect()
    const cardHeader = card.querySelector('.el-card__header') as HTMLElement
    const cardHeaderHeight = cardHeader ? cardHeader.getBoundingClientRect().height : 0
    const queryBarHeight = queryBar ? queryBar.getBoundingClientRect().height : 0
    
    // 计算可用高度
    // 优先使用 ContentWrap Card body 的高度（最准确）
    // 否则使用多种方法计算，取最大值以确保充分利用空间
    const windowHeight = window.innerHeight
    const FOOTER_HEIGHT = 50 // Footer 的标准高度
    
    let baseAvailableHeight = 0
    if (contentWrapCardBodyRect && contentWrapCardBodyRect.height > 0) {
      // 使用 ContentWrap Card body 的高度（最准确）
      baseAvailableHeight = contentWrapCardBodyRect.height - queryBarHeight
    } else {
      // 获取计算所需的位置信息
      const contentAreaTop = contentAreaRect.top
      
      // 使用两种不同的方法计算可用高度，以应对不同的布局情况
      const calculatedHeights = [
        // 方法1：基于 baseGridWrapper 实际高度计算（适用于 flex 布局）
        baseGridWrapperRect.height - queryBarHeight,
        // 方法2：基于窗口高度计算（适用于全屏布局，考虑 Footer）
        windowHeight - contentAreaTop - FOOTER_HEIGHT - queryBarHeight
      ]
      
      // 取两种方法的最大值，确保充分利用可用空间
      baseAvailableHeight = Math.max(...calculatedHeights)
      
      // 安全限制：确保不超过窗口实际可用高度
      const maxPossibleHeight = windowHeight - contentAreaTop - queryBarHeight
      baseAvailableHeight = Math.min(baseAvailableHeight, maxPossibleHeight)
    }
    
    // 减去 Card header 高度和底部间距（10px）
    const availableHeight = Math.max(0, baseAvailableHeight - cardHeaderHeight - 10 - 1)
    
    // 如果高度没有变化，不需要重新设置
    if (Math.abs(availableHeight - lastSetHeight) < 1) {
      return
    }
    
    // 查找 ElMenu 元素和其包装器
    const menuElement = wrapper.querySelector('.base-grid-quick-query-menu') as HTMLElement
    let menuWrapper = wrapper.querySelector('.base-grid-quick-query-menu-wrapper') as HTMLElement
    if (!menuWrapper && quickQueryMenuWrapperRef.value) {
      menuWrapper = quickQueryMenuWrapperRef.value as HTMLElement
    }
    if (!menuWrapper && menuElement?.parentElement) {
      menuWrapper = menuElement.parentElement as HTMLElement
    }
    
    if (menuElement && availableHeight > 0) {
      // 设置 Card body 的 padding 为 0，确保底部没有额外的 padding
      if (cardBody) {
        cardBody.style.setProperty('padding', '0', 'important')
        cardBody.style.setProperty('padding-bottom', '0', 'important')
      }
      
      // 设置 menuWrapper 的高度和样式
      if (menuWrapper) {
        menuWrapper.style.setProperty('height', `${availableHeight}px`, 'important')
        menuWrapper.style.setProperty('max-height', `${availableHeight}px`, 'important')
        menuWrapper.style.setProperty('min-height', `${availableHeight}px`, 'important')
        menuWrapper.style.setProperty('overflow', 'hidden', 'important')
        menuWrapper.style.setProperty('display', 'flex', 'important')
        menuWrapper.style.setProperty('flex-direction', 'column', 'important')
        menuWrapper.style.setProperty('flex', '1', 'important')
        menuWrapper.style.setProperty('box-sizing', 'border-box', 'important')
        menuWrapper.style.setProperty('margin-bottom', '10px', 'important')
        
        // 强制重新计算布局
        void menuWrapper.offsetHeight
      }
      
      // 设置 ElMenu 的高度和样式
      menuElement.style.setProperty('height', `${availableHeight}px`, 'important')
      menuElement.style.setProperty('max-height', `${availableHeight}px`, 'important')
      menuElement.style.setProperty('min-height', `${availableHeight}px`, 'important')
      menuElement.style.setProperty('overflow-y', 'auto', 'important')
      menuElement.style.setProperty('overflow-x', 'hidden', 'important')
      menuElement.style.setProperty('width', '100%', 'important')
      menuElement.style.setProperty('display', 'block', 'important')
      menuElement.style.setProperty('box-sizing', 'border-box', 'important')
      
      // 更新上次设置的高度
      lastSetHeight = availableHeight
    }
  } finally {
    // 延迟重置标志，避免频繁触发
    setTimeout(() => {
      isSettingHeight = false
    }, 100)
  }
}

// 监听窗口大小变化，重新计算高度
let resizeTimer: ReturnType<typeof setTimeout> | null = null

// 防抖函数（延迟更长，避免频繁触发）
const debouncedSetMenuMaxHeight = () => {
  if (resizeTimer) {
    clearTimeout(resizeTimer)
  }
  resizeTimer = setTimeout(() => {
    setMenuMaxHeight()
  }, 300) // 增加延迟时间
}

onMounted(async () => {
  // 标记正在恢复状态，防止 watch 触发重复调用
  isRestoringState.value = true
  
  // 初始化选项数据（从列配置中获取）
  await initFieldOptions()
  
  // 初始化快捷查询列表（如果存在）
  if (props.quickQueryList) {
    await initQuickQueryList()
    await nextTick()
    setMenuMaxHeight()
    
    // 如果之前保存了快捷查询索引（状态恢复时 quickQueryData 还没加载），现在恢复它
    if (savedActiveQuickQueryIndex.value !== null) {
      restoreQuickQuerySelect(savedActiveQuickQueryIndex.value)
      savedActiveQuickQueryIndex.value = null
      await nextTick()
    }
  }
  
  // 等待 StatusStoragePlus 恢复状态（如果有）
  // StatusStoragePlus 会在 onMounted 时自动检查并恢复状态
  // 状态恢复完成后，会调用 handleRestoreComplete 回调
  // 在回调中会调用 getList() 加载数据
  // 如果是首次打开（没有保存的状态），也需要调用 getList()
  await nextTick()
  
  // 检查是否有保存的状态（通过 StatusStoragePlus 的 waitForRestore 方法）
  // 如果没有保存的状态，说明是首次打开，需要立即调用 getList()
  const hasSavedState = await statusStoragePlusRef.value?.waitForRestore()
  
  if (!hasSavedState) {
    // 首次打开，没有保存的状态，立即调用 getList()
    isRestoringState.value = false
    await getList()
    
    // 恢复表格选择状态（必须在数据加载完成后）
    if (savedSelectedIds.value && savedSelectedIds.value.length > 0) {
      await nextTick()
      restoreTableSelection(savedSelectedIds.value)
      savedSelectedIds.value = []
    }
    
    // 显示页面
    pageReady.value = true
    
    // 页面显示后，检查并恢复快捷查询菜单状态
    if (props.quickQueryList && quickQueryMenuRef.value && quickQueryData.value.length > 0) {
      await nextTick()
      setMenuMaxHeight()
    }
  }
  // 如果有保存的状态，handleRestoreComplete 会在状态恢复完成后被调用
  
  // 监听窗口大小变化，重新计算高度（如果快捷查询列表存在）
  if (props.quickQueryList) {
    window.addEventListener('resize', debouncedSetMenuMaxHeight)
  }
})

/**
 * 处理状态恢复完成回调
 * 当 StatusStoragePlus 完成状态恢复后，调用此函数
 * 此时查询条件和分页已经恢复，可以安全地调用 getList()
 */
const handleRestoreComplete = async (_restored: boolean) => {
  // 如果状态已恢复，查询条件和分页已经设置好
  // 如果状态未恢复（首次打开），使用默认值
  // 无论哪种情况，都需要调用 getList() 加载数据
  
  // 确保 isRestoringState 已设置为 false，允许 watch 正常工作
  isRestoringState.value = false
  
  // 调用查询（如果状态已恢复，会根据恢复的查询条件和分页进行查询）
  await getList()
  
  // 恢复表格选择状态（必须在数据加载完成后）
  if (savedSelectedIds.value && savedSelectedIds.value.length > 0) {
    await nextTick()
    restoreTableSelection(savedSelectedIds.value)
    savedSelectedIds.value = [] // 清除已恢复的选中ID
  }
  
  // 显示页面
  pageReady.value = true
  
  // 页面显示后，检查并恢复快捷查询菜单状态（如果之前没有恢复成功）
  if (props.quickQueryList && quickQueryMenuRef.value && quickQueryData.value.length > 0) {
    await nextTick()
    
    // 如果菜单选中状态还是初始值 '0'，但 executedSearchParams 中有对应的字段值，尝试恢复
    if (activeQuickQueryIndex.value === '0' && internalSearchParams.value) {
      const config = props.quickQueryList
      const field = config.field
      const fieldValue = internalSearchParams.value[field]
      
      if (fieldValue !== undefined && fieldValue !== null && fieldValue !== '') {
        // 在 quickQueryData 中查找匹配的项
        const foundIndex = quickQueryData.value.findIndex((item) => {
          return item.id === fieldValue || String(item.id) === String(fieldValue)
        })
        
        if (foundIndex !== -1) {
          const targetIndex = String(foundIndex)
          // 使用 restoreQuickQuerySelect 恢复状态，不触发查询
          restoreQuickQuerySelect(targetIndex)
          await nextTick()
        }
      }
    }
    
    setMenuMaxHeight()
  }
}

// 组件卸载前处理
onBeforeUnmount(() => {
  // 移除窗口大小监听器
  if (props.quickQueryList) {
    window.removeEventListener('resize', debouncedSetMenuMaxHeight)
  }
  // 状态保存和清理由 StatusStoragePlus 自动处理
})

watch(
  () => props.quickQueryList,
  () => {
    if (props.quickQueryList) {
      setTimeout(() => {
        setMenuMaxHeight()
      }, 100)
    }
  }
)

// 监听 quickQueryData 变化，数据加载完成后重新设置高度
watch(
  () => quickQueryData.value,
  () => {
    if (props.quickQueryList && quickQueryData.value.length > 0) {
      setTimeout(() => {
        setMenuMaxHeight()
      }, 200)
    }
  }
)

// ==================== 信息提示 ====================
/** 信息类型 */
type InfoType = 'info' | 'warn' | 'error'

/** 信息提示组件引用 */
const prompInfoRef = ref<InstanceType<typeof PrompInfo>>()

/**
 * 显示信息提示
 * @param type 信息类型：'info' | 'warn' | 'error'，为空时显示就绪状态
 * @param message 提示信息，为空时显示就绪状态
 */
const showInfo = (type?: InfoType | null, message?: string | null) => {
  if (!type || !message) {
    prompInfoRef.value?.ready()
    return
  }
  if (type === 'info') {
    prompInfoRef.value?.info(message)
  } else if (type === 'warn') {
    prompInfoRef.value?.warn(message)
  } else if (type === 'error') {
    prompInfoRef.value?.err(message)
  }
}

/**
 * 处理刷新事件
 */
const handleRefresh = () => {
  showInfo() // 清空提示信息，显示就绪状态
  getList()
}
// ==================== 表格状态管理 ====================
const { tableRegister, tableState, tableMethods } = useTable({
  immediate: false, // 禁用自动初始化查询，改为手动控制，避免在查询条件恢复之前执行查询
  fetchDataApi: async () => {
    // 如果正在恢复状态，不执行查询（状态恢复完成后会手动调用 getList）
    if (isRestoringState.value) {
      return {
        list: [],
        total: 0
      }
    }
    
    const { pageSize, currentPage } = tableState
    try {
      const res = await props.fetchDataApi({
        page: unref(currentPage),
        limit: unref(pageSize),
        ...unref(internalSearchParams.value) // 使用查询条件参数
      })

      // 处理返回格式：支持多种 API 返回格式
      // 格式1: { data: [...], count: number }
      // 格式2: { data: [...], code: 200, count: number }
      // 格式3: 直接返回数组（兼容处理）
      let dataList: any[] = []
      let totalCount: number = 0

      if (Array.isArray(res)) {
        // 如果直接返回数组
        dataList = res
        totalCount = res.length
      } else if (res && typeof res === 'object') {
        // 如果返回对象
        dataList = (res as any).data || []
        totalCount = (res as any).count || (res as any).total || 0
      }

      // 处理图片字段（排序并移除排序前缀）
      // 从列配置中提取 type === 'image' 的字段名
      const imageFields = props.columns
        .filter((col) => col.type === 'image')
        .map((col) => col.field)
      
      const processedData = dataList.map((row: any) => 
        processImageFields(row, imageFields, {
          processList: true,
          cleanArray: false
        })
      )

      return {
        list: processedData,
        total: totalCount
      }
    } catch (err: any) {
      console.error('获取数据失败：', err.message || err)
      return {
        list: [],
        total: 0
      }
    }
  },
  fetchDelApi: props.fetchDelApi ? async (ids: string[] | number[] | number | string) => {
    // 调用删除接口
    const res = await props.fetchDelApi!(ids)
    // 如果返回的是响应对象，检查 code === 200；如果返回的是 boolean，直接返回
    if (typeof res === 'boolean') {
      return res
    }
    // 处理响应对象
    return res?.code === 200
  } : undefined
})

const { dataList, loading, total, pageSize, currentPage } = tableState
const { getList, getSelections } = tableMethods

const { showAction, nodeKey, reserveSelection } = props

// ==================== 页面状态管理 ====================
/**
 * 保存的选中行ID（用于恢复表格选择状态）
 */
const savedSelectedIds = ref<any[]>([])

/**
 * 当前选中的行ID（用于状态保存）
 */
const currentSelectedIds = ref<any[]>([])

/**
 * 保存的快捷查询索引（用于在 quickQueryData 加载完成后恢复）
 */
const savedActiveQuickQueryIndex = ref<string | null>(null)

/**
 * 标记是否正在恢复状态
 */
const isRestoring = ref(false)

/**
 * 监听表格选择变化，立即保存状态（不防抖，确保选择状态及时保存）
 */
const handleSelectionChange = async () => {
  if (pageReady.value && !isRestoring.value) {
    // 更新当前选中的行ID
    try {
      const selections = typeof getSelections === 'function' ? await getSelections() : []
      currentSelectedIds.value = selections
        .map((row: any) => row?.[nodeKey])
        .filter((id: any) => id !== undefined)
    } catch (err) {
      currentSelectedIds.value = []
    }
    statusStoragePlusRef.value?.saveState()
  }
}

/**
 * 恢复表格的选择状态
 * 
 * 功能说明：
 * 根据保存的 selectedIds，在表格中恢复对应的行选中状态
 * 
 * 实现策略：
 * 1. 使用微任务队列（Promise.resolve().then()）确保每个 toggleRowSelection 都在独立的微任务中执行
 * 2. 避免使用 setTimeout 延时，优先使用精确的操作
 * 3. 如果恢复不完整，使用 watchEffect 监听数据变化，自动重试恢复
 * 
 * 技术细节：
 * - Element Plus 的 toggleRowSelection 在同一个 tick 中批量调用时，可能只有最后一个生效
 *   可能只有最后一个生效，所以需要在独立的微任务中执行每个选择操作
 * - 使用 requestAnimationFrame 确保在浏览器渲染后执行
 * - 使用 watchEffect 监听数据变化，自动重试恢复不完整的选中状态
 * 
 * @param selectedIds - 需要恢复选中的行ID数组
 */
const restoreTableSelection = async (selectedIds: any[]) => {
  if (!selectedIds || !Array.isArray(selectedIds) || selectedIds.length === 0) return
  
  try {
    // ========== 步骤1：获取表格实例和数据 ==========
    const elTable = await tableMethods.getElTableExpose()
    if (!elTable) {
      return
    }
    
    // 确保数据已经加载
    if (!dataList.value || dataList.value.length === 0) {
      return
    }
    
    // ========== 步骤2：收集需要选中的行 ==========
    const rowsToSelect = selectedIds
      .map(id => dataList.value.find((item: any) => item?.[nodeKey] === id))
      .filter(row => row !== undefined)
    
    if (rowsToSelect.length === 0) {
      return
    }
    
    // ========== 步骤3：清除现有选中状态 ==========
    elTable.clearSelection()
    await nextTick()
    
    // ========== 步骤4：批量恢复选中状态 ==========
    // 使用 requestAnimationFrame 确保在浏览器渲染后执行
    await new Promise(resolve => requestAnimationFrame(resolve))
    
    // 使用微任务队列，确保每个 toggleRowSelection 都在独立的微任务中执行
    // 原因：Element Plus 的 toggleRowSelection 在同一个 tick 中批量调用时，可能只有最后一个生效
    for (const row of rowsToSelect) {
      await Promise.resolve().then(() => {
        elTable.toggleRowSelection(row, true)
      })
    }
    
    await nextTick()
    
    // ========== 步骤5：验证恢复结果 ==========
    const currentSelections = elTable.getSelectionRows()
    const currentSelectedIds = currentSelections.map((row: any) => row?.[nodeKey])
    const restoredCount = selectedIds.filter(id => currentSelectedIds.includes(id)).length
    
    // ========== 步骤6：如果恢复不完整，使用 watchEffect 自动重试 ==========
    if (restoredCount < selectedIds.length) {
      // 使用 watchEffect 监听数据变化，自动重试恢复
      const stopWatcher = watchEffect(async () => {
        if (!dataList.value || dataList.value.length === 0) return
        
        // 获取当前已选中的行
        const currentSelections = elTable.getSelectionRows()
        const currentSelectedIds = currentSelections.map((row: any) => row?.[nodeKey])
        
        // 找出未选中的行
        const missingIds = selectedIds.filter(id => !currentSelectedIds.includes(id))
        
        if (missingIds.length > 0) {
          // 收集需要选中的行
          const missingRows = missingIds
            .map(id => dataList.value.find((item: any) => item?.[nodeKey] === id))
            .filter(row => row !== undefined)
          
          if (missingRows.length > 0) {
            // 使用微任务队列批量恢复
            for (const row of missingRows) {
              await Promise.resolve().then(() => {
                elTable.toggleRowSelection(row, true)
              })
            }
            
            await nextTick()
            
            // 验证恢复结果
            const finalSelections = elTable.getSelectionRows()
            const finalSelectedIds = finalSelections.map((row: any) => row?.[nodeKey])
            const finalRestoredCount = selectedIds.filter(id => finalSelectedIds.includes(id)).length
            
            // 如果恢复成功，停止监听
            if (finalRestoredCount === selectedIds.length) {
              stopWatcher()
            }
          }
        } else {
          // 所有行都已选中，停止监听
          stopWatcher()
        }
      })
      
      // 设置超时，避免无限监听（约1秒，60fps）
      let frameCount = 0
      const maxFrames = 60
      const checkTimeout = () => {
        frameCount++
        if (frameCount >= maxFrames) {
          stopWatcher()
        } else {
          requestAnimationFrame(checkTimeout)
        }
      }
      requestAnimationFrame(checkTimeout)
    }
  } catch (err) {
    console.error('BaseGrid: 恢复表格选择状态失败', err)
  }
}

/**
 * 配置 StatusStoragePlus 的状态存储
 */
const stateStores = computed<StatusStoreItem[]>(() => {
  const stores: StatusStoreItem[] = [
    {
      name: 'baseGrid',
      getState: () => {
        // 收集查询条件（使用 toRaw 确保获取原始值，避免响应式对象）
        const formDisplayParamsRaw = toRaw(formDisplayParams.value) || {}
        const executedSearchParams = toRaw(internalSearchParams.value) || {}
        
        return {
          formDisplayParams: formDisplayParamsRaw,
          executedSearchParams,
          currentPage: currentPage.value,
          pageSize: pageSize.value,
          activeQuickQueryIndex: activeQuickQueryIndex.value,
          selectedIds: currentSelectedIds.value
        }
      },
      setState: async (state: any) => {
        isRestoring.value = true
        // 设置 isRestoringState，防止 useTable 的 watch 触发查询
        isRestoringState.value = true
        
        try {
          // 恢复查询条件
          if (state.formDisplayParams) {
            formDisplayParams.value = { ...state.formDisplayParams }
            // 通过 QueryBar 组件恢复表单显示值
            if (queryBarRef.value && typeof queryBarRef.value.setValues === 'function') {
              await nextTick()
              await queryBarRef.value.setValues(state.formDisplayParams)
            }
          }
          
          if (state.executedSearchParams) {
            internalSearchParams.value = { ...state.executedSearchParams }
          }
          
          // 恢复分页（需要特殊处理，避免触发多次 getList）
          // 注意：此时 isRestoringState = true，useTable 的 watch 虽然会触发，但不会执行查询
          if (state.pageSize !== undefined) {
            const targetPageSize = typeof state.pageSize === 'number' && state.pageSize > 0 ? state.pageSize : 10
            const targetCurrentPage = typeof state.currentPage === 'number' && state.currentPage > 0 ? state.currentPage : 1
            
            const pageSizeChanged = targetPageSize !== pageSize.value
            const currentPageChanged = targetCurrentPage !== currentPage.value
            
            // 如果 pageSize 变化且 currentPage !== 1，先设置 currentPage = 1
            if (pageSizeChanged && targetCurrentPage !== 1) {
              currentPage.value = 1
              await nextTick()
            }
            
            // 恢复 pageSize
            if (pageSizeChanged) {
              pageSize.value = targetPageSize
              await nextTick()
            }
            
            // 恢复 currentPage
            if (currentPageChanged && targetCurrentPage !== currentPage.value) {
              currentPage.value = targetCurrentPage
              await nextTick()
            }
          }
          
          // 恢复快捷查询选择
          // 注意：需要确保 quickQueryData 已经加载完成
          if (state.activeQuickQueryIndex !== undefined && props.quickQueryList && quickQueryData.value.length > 0) {
            const targetIndex = String(state.activeQuickQueryIndex)
            restoreQuickQuerySelect(targetIndex)
          } else if (state.activeQuickQueryIndex !== undefined && props.quickQueryList) {
            // 如果 quickQueryData 还没有加载完成，保存索引等待后续恢复
            savedActiveQuickQueryIndex.value = String(state.activeQuickQueryIndex)
          }
          
          // 保存选中的行ID，等待数据加载完成后恢复
          if (state.selectedIds && Array.isArray(state.selectedIds)) {
            savedSelectedIds.value = state.selectedIds
          }
          
          await nextTick()
        } finally {
          isRestoring.value = false
          // 注意：isRestoringState 在 handleRestoreComplete 中设置为 false
          // 这样可以确保状态恢复完成后才允许查询
        }
      },
      componentRef: {
        ref: queryBarRef,
        methodName: 'setValues',
        getRestoreParams: (state: any) => state.formDisplayParams || {}
      }
    }
  ]
  
  return stores
})

// ==================== 工具函数 ====================
/**
 * 渲染操作按钮
 * @param options 操作按钮配置数组
 * @param row 当前行数据
 * @param col 列配置（可选）
 */
const renderActionButtons = (
  options: ActionOption[],
  row: any,
  col?: GridColumn
) => {
  return (
    <>
      {options.map((option, index) => {
        const { type, label, onClick, permission, ...buttonProps } = option

        // 默认按钮文字
        const buttonLabel = label || (type === 'edit' ? '修改' : type === 'delete' ? '删除' : '操作')
        // 默认按钮类型
        const buttonType = buttonProps.type || (type === 'delete' ? 'danger' : 'primary')

        // 处理点击事件
        const handleClick = () => {
          if (onClick) {
            onClick(row)
          } else if (type === 'edit' && col?.onEdit) {
            col.onEdit(row)
          } else if (type === 'delete' && col?.onDelete) {
            col.onDelete(row)
          } else if (type === 'delete' && props.fetchDelApi && tableMethods) {
            tableMethods.delList(true, [row[props.nodeKey]])
          }
        }

        return (
          <BaseButton
            key={index}
            type={buttonType}
            link
            size="small"
            onClick={handleClick}
            {...buttonProps}
          >
            {buttonLabel}
          </BaseButton>
        )
      })}
    </>
  )
}

// ==================== 列转换函数 ====================
/**
 * 将 GridColumn 配置转换为 TableColumn
 * @param columns 列配置数组
 * @returns TableColumn 数组
 */
const convertColumns = (columns: GridColumn[]): TableColumn[] => {
  return columns.map((col) => {
    // 基础列配置
    const baseColumn: TableColumn = {
      field: col.field,
      label: col.label,
      show: col.show !== false,
      width: col.width,
      minWidth: col.minWidth,
      align: col.align,
      headerAlign: col.headerAlign || 'center', // 表头默认居中对齐
      fixed: col.fixed,
      // showConfig：是否可配置显示/隐藏，默认 true
      showConfig: col.showConfig !== undefined ? col.showConfig : true
    }

    // 根据列类型进行特殊处理
    switch (col.type) {
      case 'selection':
        return {
          ...baseColumn,
          type: 'selection',
          show: col.show !== false
        }

      case 'image':
        // 图片列：使用 ImageSingle 组件自动处理图片数据（支持字符串或数组格式）
        return {
          ...baseColumn,
          slots: {
            default: (data: any) => {
              const row = data.row
              // 获取图片字段名（优先使用 imageField，否则使用 field）
              const imageField = col.imageField || col.field
              // 获取图片尺寸（normal 或 small，默认 normal）
              const imageSize = col.imageSize || 'normal'
              
              // 获取图片数据（ImageSingle 组件会自动处理数组格式）
              const imageValue = row[imageField] ?? null

              return (
                <div class="resource-image-name flex items-center">
                  <ImageSingle
                    modelValue={imageValue}
                    disabled={true}
                    size={imageSize}
                    defaultImage={DEFAULT_IMAGE}
                  />
                </div>
              )
            }
          }
        }

      case 'status':
        // 状态列：根据状态值映射显示文字
        return {
          ...baseColumn,
          formatter: (row: any) => {
            // 优先使用自定义格式化函数
            if (col.formatter) {
              return col.formatter(row)
            }
            // 获取状态选项（优先级：statusOptions > fieldOptionsData > 空数组）
            let statusOptions: Array<{ label: string; value: any }> | undefined
            if (col.statusOptions) {
              statusOptions = typeof col.statusOptions === 'function' 
                ? col.statusOptions() 
                : col.statusOptions
            } else if (fieldOptionsData.value[col.field] && fieldOptionsData.value[col.field].length > 0) {
              // 如果配置了 optionsApi，使用自动获取的数据
              statusOptions = fieldOptionsData.value[col.field]
            }
            // 构建状态映射表并返回对应文字
            if (statusOptions && Array.isArray(statusOptions)) {
              const statusMap = statusOptions.reduce(
                (acc, item) => {
                  acc[item.value] = item.label
                  return acc
                },
                {} as Record<any, string>
              )
              return statusMap[row[col.field]] || '未知'
            }
            return row[col.field]
          }
        }

      case 'action':
        // 操作列：渲染操作按钮（默认显示修改、查看、删除三个按钮，支持自定义）
        // 宽度处理：如果用户指定了 width，使用指定值；否则默认使用 160px
        return {
          ...baseColumn,
          align: col.align || 'center',
          fixed: col.fixed || 'right',
          width: col.width || 160,
          minWidth: col.minWidth,
          slots: {
            default: (data: any) => {
              // 优先使用自定义插槽
              if (col.actionSlots) {
                return col.actionSlots(data)
              }

              const row = data.row
              const options = col.actionOptions

              // 如果没有配置操作选项（undefined 或空数组），使用默认的修改、查看和删除按钮
              if (!options || options.length === 0) {
                const defaultOptions: ActionOption[] = []
                
                // 1. 修改按钮
                // 优先级：列配置的 onEdit 回调 > 集成的 editAction 函数
                // 显示条件：enableEdit 不为 false（默认 true）
                // 注意：修改功能需要配置 formSchema 才能正常工作
                if (col.onEdit) {
                  defaultOptions.push({ type: 'edit', onClick: col.onEdit })
                } else if (props.enableEdit !== false) {
                  defaultOptions.push({ type: 'edit', onClick: (row: any) => editAction(row) })
                }
                
                // 2. 查看按钮
                // 显示条件：enableView 不为 false（默认 true）
                // 注意：查看功能需要配置 formSchema 才能正常工作
                if (props.enableView !== false) {
                  defaultOptions.push({ 
                    type: 'other', 
                    label: '查看', 
                    onClick: (row: any) => viewAction(row) 
                  })
                }
                
                // 3. 删除按钮
                // 优先级：列配置的 onDelete 回调 > 集成的 delData 函数
                // 显示条件：enableDelete 不为 false（默认 true）
                // 注意：删除功能需要配置 fetchDelApi 才能正常工作
                if (col.onDelete) {
                  defaultOptions.push({ type: 'delete', onClick: col.onDelete })
                } else if (props.enableDelete !== false) {
                  defaultOptions.push({ type: 'delete', onClick: (row: any) => delData(row) })
                }
                
                return renderActionButtons(defaultOptions, row, col)
              }

              // 如果配置了自定义操作选项，使用自定义配置
              return renderActionButtons(options, row, col)
            }
          }
        }

      case 'text':
      default:
        // 文本列：默认类型，支持自定义格式化
        return {
          ...baseColumn,
          show: true,
          formatter: col.formatter
        }
    }
  })
}

// ==================== 表格列配置 ====================
/**
 * 转换列配置，过滤掉 show: false 的列
 * @param columns 原始列配置
 * @param preserveShowState 保留现有列的 show 状态映射（用于列配置弹窗中的用户操作）
 * @returns 转换后的列配置数组（已过滤掉 show: false 的列）
 */
const convertAndFilterColumns = (
  columns: GridColumn[],
  preserveShowState?: Map<string, boolean>
): TableColumn[] => {
  // 先转换所有列
  const converted = convertColumns(columns)
  
  // 过滤掉 show: false 的列，并保留用户的 show 状态设置
  return converted.filter((col) => {
    const originalCol = columns.find((c) => c.field === col.field)
    
    // 如果原始配置中 show: false，完全过滤掉该列
    if (originalCol && originalCol.show === false) {
      return false
    }
    
    // 使用保留的 show 状态（用户在列配置弹窗中的操作）
    if (preserveShowState && preserveShowState.has(col.field)) {
      col.show = preserveShowState.get(col.field)!
    }
    
    return true
  })
}

/** 转换后的表格列配置（使用 reactive 确保响应式） */
const tableColumns = reactive<TableColumn[]>(convertAndFilterColumns(props.columns))

/**
 * 监听 props.columns 变化，同步更新 tableColumns
 * 注意：show: false 的列会被完全过滤掉，不会出现在列配置选项中
 */
watch(
  () => props.columns,
    (newColumns) => {
      // 创建现有列的字段映射，用于保留 show 属性（用户通过列配置弹窗修改的）
      const existingShowMap = new Map<string, boolean>()
      tableColumns.forEach((col) => {
        existingShowMap.set(col.field, col.show)
      })
      
      // 转换并过滤列，保留用户的 show 设置
      const newTableColumns = convertAndFilterColumns(newColumns, existingShowMap)
      
      // 清空并重新填充数组
      tableColumns.length = 0
      newTableColumns.forEach((newCol) => {
        tableColumns.push(newCol)
      })
    },
    { deep: false }
)

// ==================== 工具栏按钮处理 ====================
/**
 * 处理工具栏按钮点击事件
 * 如果按钮没有提供 onClick，则根据按钮类型使用默认操作
 */
const handleToolbarButtonClick = (btn: ToolbarButton) => {
  if (btn.onClick) {
    // 如果提供了自定义 onClick，直接调用
    btn.onClick()
    return
  }
  
  // 根据按钮类型使用默认操作
  switch (btn.stype) {
    case 'new':
      // 新增按钮：使用集成的 addAction
      if (props.enableAdd && props.formSchema) {
        addAction()
      }
      break
    case 'batch':
      // 批量删除按钮：使用集成的 delData
      if (props.enableDelete && props.fetchDelApi) {
        delData()
      }
      break
    case 'import':
      // 导入按钮：使用集成的 openImport
      // 优先使用按钮配置中的路由，其次使用 props 中的配置
      // importStorageKey 会自动根据 windowId 生成，无需配置
      // importLabel 使用按钮的 label，如果按钮没有 label 则使用 props.importLabel 或默认值
      const importRoute = (btn as any).importRoute || props.importRoute
      const importLabel = btn.label || (btn as any).importLabel || props.importLabel
      
      if (importRoute) {
        openImport(importRoute, importLabel)
      } else {
        console.warn('未配置导入路由（importRoute），无法执行导入操作。请在 toolbarButtons 的 import 按钮配置中添加 importRoute，或在 BaseGrid 的 props 中配置 importRoute')
      }
      break
    default:
      // 其他按钮类型，如果没有提供 onClick，则不执行任何操作
      break
  }
}

// ==================== 操作函数 ====================
/**
 * 新增操作
 */
const addAction = () => {
  if (!props.enableAdd || !props.formSchema) {
    return
  }
  dialogMode.value = 'add'
  currentRow.value = null
  dialogVisible.value = true
}

/**
 * 编辑操作
 */
const editAction = (row: any) => {
  if (!props.enableEdit || !props.formSchema) {
    return
  }
  dialogMode.value = 'edit'
  // 复制行数据，避免直接修改原数据
  currentRow.value = { ...row }
  dialogVisible.value = true
}

/**
 * 查看操作
 */
const viewAction = (row: any) => {
  if (!props.enableView || !props.formSchema) {
    return
  }
  dialogMode.value = 'view'
  currentRow.value = { ...row }
  dialogVisible.value = true
}

/**
 * 删除操作
 */
const delData = async (row?: any) => {
  if (!props.enableDelete || !props.fetchDelApi) {
    return
  }
  
  if (row) {
    // 删除单行
    await tableMethods.delList(true, [row[props.nodeKey]])
  } else {
    // 批量删除
    await tableMethods.delList(true)
  }
  // delList 方法会自动刷新列表并显示消息
}

/**
 * 提交接口（新增或修改）
 * @param data - 表单数据
 * @param mode - 操作模式（'add' | 'edit'），如果提供则优先使用，否则使用 dialogMode
 */
const submitApi = async (data: any, mode?: 'add' | 'edit') => {
  // 优先使用传入的 mode 参数（支持继续新增/拷贝新增时的模式切换）
  // 如果没有传入 mode，则使用 dialogMode（向后兼容）
  const operationMode = mode || dialogMode.value
  
  // 如果提供了 submitApi，优先使用
  if (props.submitApi) {
    return await props.submitApi(data, operationMode)
  }
  
  // 否则根据模式调用对应的 API
  if (operationMode === 'add') {
    if (props.addApi) {
      return await props.addApi(data)
    }
    throw new Error('未配置新增接口（addApi）')
  } else {
    if (props.editApi) {
      return await props.editApi(data)
    }
    throw new Error('未配置编辑接口（editApi）')
  }
}

/**
 * 保存成功回调
 */
const handleSuccess = () => {
  // 刷新列表
  getList()
  // 调用用户自定义回调
  if (props.onSuccess) {
    props.onSuccess()
  }
}

/**
 * 取消操作
 */
const handleCancel = () => {
  dialogVisible.value = false
  currentRow.value = null
  // 调用用户自定义回调
  if (props.onCancel) {
    props.onCancel()
  }
}

// ==================== 暴露方法 ====================
defineExpose({
  getList, // 刷新列表
  getSelections, // 获取选中的行
  tableMethods, // 表格方法集合
  tableState, // 表格状态
  showInfo, // 显示信息提示
  addAction, // 新增操作
  editAction, // 编辑操作
  viewAction, // 查看操作
  delData // 删除操作
})
</script>

<template>
  <StatusStoragePlus
    ref="statusStoragePlusRef"
    :stores="stateStores"
    :storage-prefix="props.windowId || 'BASE_GRID_STATE_'"
    :on-restore-complete="handleRestoreComplete"
  >
    <div class="base-grid-wrapper" v-show="pageReady">
    <!-- 查询条件区域 -->
    <QueryBar 
      v-if="processedSearchConditions && processedSearchConditions.length > 0"
      ref="queryBarRef"
      :conditions="processedSearchConditions"
      @search="handleSearch"
      @reset="handleReset"
      @register="handleQueryBarRegister"
      @field-change="handleQueryBarFieldChange"
    />

    <!-- 内容区域：左侧快捷查询列表 + 右侧表格 -->
    <div v-if="props.quickQueryList" class="base-grid-content-area">
    <!-- 左侧快捷查询列表 -->
    <ElCard class="base-grid-quick-query-list" :header="props.quickQueryList.title" shadow="never" :body-style="{ padding: '0', paddingBottom: '0' }">
      <div ref="quickQueryMenuWrapperRef" class="base-grid-quick-query-menu-wrapper">
        <ElMenu
          ref="quickQueryMenuRef"
          class="base-grid-quick-query-menu"
          shadow="never"
          :default-active="activeQuickQueryIndex"
          :key="`menu-${activeQuickQueryIndex}`"
          @select="handleQuickQuerySelect"
        >
          <ElMenuItem
            v-for="(item, index) in quickQueryData"
            :key="item.id ?? index"
            :index="index.toString()"
          >
            {{ item.label }}
          </ElMenuItem>
        </ElMenu>
      </div>
    </ElCard>
    <!-- 右侧表格 -->
    <div class="base-grid-right-table">
      <Table
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :show-action="showAction"
        :columns="tableColumns"
        :node-key="nodeKey"
        :data="dataList"
        :loading="loading"
        :pagination="{
          total
        }"
        :reserve-selection="reserveSelection"
        @register="tableRegister"
        @refresh="handleRefresh"
        @selection-change="handleSelectionChange"
      >
        <template #toolbar>
          <div class="base-grid-toolbar-wrapper">
            <div class="base-grid-toolbar-left">
              <template v-if="props.toolbarButtons && props.toolbarButtons.length > 0">
                <template v-for="btn in props.toolbarButtons" :key="btn.stype">
                  <ButtonPlus :stype="btn.stype" @click="() => handleToolbarButtonClick(btn)">
                    <template v-if="btn.label">{{ btn.label }}</template>
                  </ButtonPlus>
                </template>
              </template>
              <slot name="toolbar-left"></slot>
            </div>

            <div class="base-grid-toolbar-info">
              <PrompInfo ref="prompInfoRef" />
            </div>
          </div>
          <slot name="toolbar"></slot>
        </template>
      </Table>
    </div>
  </div>
  <!-- 无快捷查询列表时，直接显示表格 -->
  <Table
    v-else
    v-model:current-page="currentPage"
    v-model:page-size="pageSize"
    :show-action="showAction"
    :columns="tableColumns"
    :node-key="nodeKey"
    :data="dataList"
    :loading="loading"
    :pagination="{
      total
    }"
    :reserve-selection="reserveSelection"
    @register="tableRegister"
    @refresh="handleRefresh"
    @selection-change="handleSelectionChange"
  >
    <template #toolbar>
      <div class="base-grid-toolbar-wrapper">
        <div class="base-grid-toolbar-left">
          <template v-if="props.toolbarButtons && props.toolbarButtons.length > 0">
            <template v-for="btn in props.toolbarButtons" :key="btn.stype">
              <ButtonPlus :stype="btn.stype" @click="() => handleToolbarButtonClick(btn)">
                <template v-if="btn.label">{{ btn.label }}</template>
              </ButtonPlus>
            </template>
          </template>
          <slot name="toolbar-left"></slot>
        </div>

        <div class="base-grid-toolbar-info">
          <PrompInfo ref="prompInfoRef" />
        </div>
      </div>
      <slot name="toolbar"></slot>
    </template>
  </Table>
  </div>
  
  <!-- 弹窗：新增/编辑/查看 -->
  <BaseFree
    v-if="props.formSchema && props.formSchema.length > 0"
    v-model="dialogVisible"
    :page-title="props.pageTitle"
    :mode="dialogMode"
    :save-loading="saveLoading"
    :form-schema="props.formSchema"
    :rules="props.rules"
    :current-row="currentRow"
    :submit-api="submitApi"
    :tabs="props.tabs"
    @success="handleSuccess"
    @cancel="handleCancel"
  />
  </StatusStoragePlus>
</template>

<style scoped>
/* 确保 ContentWrap 内部的布局正确 */
:deep(.content-wrap) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

:deep(.content-wrap .el-card) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
}

:deep(.content-wrap .el-card__body) {
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
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

/* BaseGrid 根容器 */
.base-grid-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
}

/* 内容区域：左侧快捷查询列表 + 右侧表格 */
.base-grid-content-area {
  display: flex;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  align-items: stretch;
  height: 100%;
}

/* 左侧快捷查询列表 */
.base-grid-quick-query-list {
  width: 160px;
  margin-right: 10px;
  flex-shrink: 0;
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  min-height: 0;
  align-self: stretch;
}

.base-grid-quick-query-list :deep(.el-card) {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
}

.base-grid-quick-query-list :deep(.el-card__header) {
  padding: 15px 20px !important;
  margin-bottom: 0 !important;
}

/* ElCard 内部布局 */
.base-grid-quick-query-list :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0 !important;
  padding-bottom: 0 !important;
  overflow: hidden;
}

/* 菜单包装器 */
.base-grid-quick-query-menu-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 10px !important;
  height: 100%;
  box-sizing: border-box;
}

/* ElMenu - 高度通过 JavaScript 动态设置 */
.base-grid-quick-query-menu {
  width: 100% !important;
  box-sizing: border-box !important;
}

/* 右侧表格 */
.base-grid-right-table {
  flex: 1;
  overflow-x: auto;
}

/* 图片列容器样式 */
.resource-image-name {
  display: flex;
  align-items: center;
}

/* 让 Table 组件的左侧 div 占据全部可用空间 */
:deep(.flex.justify-between > div:first-child) {
  flex: 1;
  min-width: 0;
  display: flex;
}

/* 工具栏容器 */
.base-grid-toolbar-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 10px;
  margin-right: 10px;
  min-width: 0;
}

/* 工具栏左侧按钮区域 */
.base-grid-toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* 工具栏中间信息显示区域 */
.base-grid-toolbar-info {
  flex: 1;
  display: flex;
  align-items: center;
  min-width: 0;
  overflow: hidden;
}
</style>

