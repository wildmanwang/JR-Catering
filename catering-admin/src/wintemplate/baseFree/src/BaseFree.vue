<script setup lang="tsx">
import { computed, ref, watch, nextTick } from 'vue'
import { ElDrawer, ElScrollbar, ElTabs, ElTabPane, ElMessage, ElMessageBox } from 'element-plus'
import { ButtonPlus } from '@/components/ButtonPlus'
import { PromptInfo } from '@/components/PromptInfo'
import { Form, FormSchema } from '@/components/Form'
import { useForm } from '@/hooks/web/useForm'
import { ImagePlus } from '@/components/ImagePlus'
import { processImageFields, ImageQuerySuffix, getImageUrlWithSuffix } from '@/utils/imageList'
import { formatDataItem } from '@/utils/dsOptions'

defineOptions({
  name: 'BaseFree'
})

// ==================== 类型定义 ====================
/**
 * 表单字段配置接口
 * 扩展了 FormSchema，添加了 BaseFree 模板特有的字段配置选项
 */
export interface FreeFormField extends FormSchema {
  /** 
   * 字段类型，用于决定字段的显示组件和处理逻辑
   * - 'image': 图片字段（使用 ImagePlus 组件）
   * - 'text': 文本字段（使用 Input 组件）
   * - 'status': 状态字段（使用 Select 组件，支持 statusOptions）
   * - 'number': 数字字段（使用 InputNumber 组件）
   * - 'select': 下拉选择字段（使用 ElSelect 组件，支持 options/optionsApi/原始值三种情况）
   *   - 如果配置了 options（在 componentProps 中），则按此规则渲染
   *   - 如果配置了 optionsApi，则按 dsOptions 规则自动获取并渲染
   *   - 否则，按原始值在下拉组件中显示
   * - 'dropdown': 下拉字段（使用 Dropdown 组件）
   * 
   * 注意：selection 类型已合并到 select 类型，请使用 type: 'select'
   * 
   * @example 'image' | 'text' | 'status' | 'number' | 'select' | 'dropdown'
   */
  type?: 'image' | 'text' | 'status' | 'number' | 'select' | 'dropdown' | 'selection'
  
  /** 
   * ImagePlus 组件尺寸（仅当 type='image' 时有效）
   * @default 'normal'
   * @example 'normal' | 'small'
   */
  size?: 'normal' | 'small'
  
  /** 
   * 拷贝新增时是否保留上一条记录的值
   * - true: 拷贝新增时，该字段保留上一条记录的值
   * - false: 拷贝新增时，该字段使用初始化新增时的默认值
   * @default false
   * @example 
   * // 在表单字段配置中设置
   * { field: 'name', label: '名称', newCopy: true }
   */
  newCopy?: boolean
  
  /** 
   * 自定义字段转换函数
   * 如果提供，将使用此函数替代模板的默认处理逻辑
   * 
   * @param field - 字段配置对象
   * @param data - 当前表单数据
   * @param mode - 当前操作模式（'add' | 'edit' | 'view'）
   * @returns FormSchema 或 null（返回 null 表示使用模板默认处理）
   * 
   * @example
   * customConvert: (field, data, mode) => {
   *   if (mode === 'edit') {
   *     return { ...field, disabled: true }
   *   }
   *   return null // 使用默认处理
   * }
   */
  customConvert?: (field: FreeFormField, data: any, mode: 'add' | 'edit' | 'view') => FormSchema | null
  /** 
   * 选项数据获取接口（用于自动获取该字段的选项数据，仅当 type='select' 时有效）
   * 如果提供，BaseFree 会自动调用此接口获取选项数据，并按 dsOptions 规则转换
   * 返回格式：{ data: [...], code: 200 } 或直接返回数组
   * 
   * 使用场景：
   * 1. 如果配置了 options（在 componentProps 中），优先使用 options
   * 2. 如果配置了 optionsApi，使用自动获取的数据（按 dsOptions 规则）
   * 3. 否则，按原始值在下拉组件中显示
   * 
   * @example
   * optionsApi: () => getBranchListApi({ is_active: true })
   */
  optionsApi?: () => Promise<any>
  /** 
   * 选项数据的 id 字段名（用于简化配置，配合 optionsLabelFormat 使用）
   * 如果不提供 optionsTransform，将使用此字段作为唯一标识
   * @example 'id' 或 'value'
   */
  optionsIdField?: string
  /** 
   * 选项数据的 label 格式配置（用于简化配置，使用 dsOptions.ts 的格式）
   * 配合 optionsIdField 使用，用于从选项数据中生成显示标签
   * 
   * @example 
   * // 只显示 name_unique 字段
   * optionsLabelFormat: [['field', 'name_unique']]
   * // 显示 name_unique 和 status，中间用 '-' 连接
   * optionsLabelFormat: [['field', 'name_unique'], ['value', '-'], ['field', 'status']]
   */
  optionsLabelFormat?: Array<['field' | 'value', string]>
}

/** Tab 配置 */
export interface FreeTab {
  label: string // Tab 标签
  name: string // Tab 名称
  fields?: string[] // 字段列表，为空时显示所有字段
  customContent?: boolean // 是否使用自定义内容（如果为 true，将使用插槽内容）
}

/** 组件 Props */
interface Props {
  modelValue: boolean // 抽屉显示状态
  title?: string // 抽屉标题（如果提供，将直接使用此标题，忽略 pageTitle）
  pageTitle?: string // 主窗口标题（例如："菜品"）
  mode?: 'add' | 'edit' | 'view' // 模式：新增、修改、查看
  width?: string | number // 抽屉宽度
  saveLoading?: boolean // 保存按钮加载状态
  showFooter?: boolean // 是否显示底部按钮
  closeOnClickModal?: boolean // 点击遮罩是否关闭，默认 true
  // 表单相关
  formSchema: FreeFormField[] // 表单字段配置
  rules?: Record<string, any> // 表单验证规则
  currentRow?: any // 当前行数据（编辑/查看时使用）
  // 数据接口
  submitApi?: (data: any, mode?: 'add' | 'edit') => Promise<any> // 提交接口（新增/编辑），mode 参数用于区分新增/修改
  // Tab 配置
  tabs?: FreeTab[] // Tab 配置，fields 为空时显示所有字段
  // 扩展钩子函数
  beforeSubmit?: (data: any) => Promise<any> | any // 提交前的数据处理钩子
  afterInit?: (data: any) => void // 初始化后的钩子
  customFieldConvert?: (field: FreeFormField, data: any) => FormSchema | null // 全局字段转换函数
  // 选项数据映射（字段名 -> 选项数组），用于从主窗口传递下拉框选项，避免重复请求
  // 注意：已废弃，请使用 formSchema 中的 optionsApi 配置
  fieldOptions?: Record<string, any[] | (() => any[])> // 字段选项数据映射（已废弃）
}

// ==================== Props 定义 ====================
const props = withDefaults(defineProps<Props>(), {
  mode: 'add',
  width: '700px',
  saveLoading: false,
  showFooter: false,
  closeOnClickModal: true,
  rules: () => ({}),
  currentRow: () => null,
  tabs: () => [
    { label: '基础信息', name: 'basic' }
  ],
  fieldOptions: () => ({})
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'save': [data: any] // 保存事件，返回表单数据
  'cancel': [] // 取消事件
  'success': [] // 提交成功事件
}>()

// ==================== Store ====================
// ImagePlus 组件内部会处理 token，这里不需要单独获取 token

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
 * 根据字段配置转换选项数据
 * @param field - 字段配置
 * @param rawOptions - 原始选项数据
 * @returns 转换后的选项数据
 */
const transformOptionsByConfig = (field: FreeFormField, rawOptions: any[]): any[] => {
  if (!rawOptions || rawOptions.length === 0) return []
  
  // 如果配置了 optionsLabelFormat，使用 dsOptions.ts 格式转换
  if (field.optionsIdField && field.optionsLabelFormat && field.optionsLabelFormat.length > 0) {
    return rawOptions.map((item: any) => {
      const id = item[field.optionsIdField!]
      const label = generateLabelByFormat(rawOptions, id, field.optionsLabelFormat!)
      return {
        label,
        value: id,
        ...item // 保留原始数据
      }
    })
  }
  
  // 默认转换：尝试自动识别格式
  if (rawOptions.length > 0) {
    if (rawOptions[0].hasOwnProperty('label') && rawOptions[0].hasOwnProperty('value')) {
      // 已经是标准格式
      return rawOptions
    } else if (rawOptions[0].hasOwnProperty('id') && rawOptions[0].hasOwnProperty('name_unique')) {
      // 常见格式：{ id, name_unique, ... }
      return rawOptions.map((item: any) => ({
        label: item.name_unique,
        value: item.id,
        ...item
      }))
    } else {
      // 尝试其他格式
      return rawOptions.map((item: any) => ({
        label: item.label || item.name_unique || item.name || String(item.id || item.value),
        value: item.value !== undefined ? item.value : item.id,
        ...item
      }))
    }
  }
  
  return rawOptions
}

/**
 * 初始化选项数据（从表单字段配置中收集 optionsApi 并获取数据）
 */
const initFieldOptions = async () => {
  // 收集所有需要获取选项数据的字段
  const optionsApiMap = new Map<string, { api: () => Promise<any>; field: FreeFormField }>()
  
  props.formSchema.forEach((field) => {
    if (field.optionsApi && field.field) {
      optionsApiMap.set(field.field, {
        api: field.optionsApi,
        field
      })
    }
  })
  
  // 并行获取所有选项数据
  const promises = Array.from(optionsApiMap.entries()).map(async ([fieldName, { api, field }]) => {
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
        console.warn(`字段 ${fieldName} 的选项数据格式不正确：`, res)
        rawOptions = []
      }
      
      // 根据字段配置转换数据
      const transformedOptions = transformOptionsByConfig(field, rawOptions)
      
      fieldOptionsData.value[fieldName] = transformedOptions
    } catch (err) {
      console.error(`获取字段 ${fieldName} 的选项数据失败：`, err)
      fieldOptionsData.value[fieldName] = []
    }
  })
  
  await Promise.all(promises)
}

// ==================== 计算属性 ====================
/** 抽屉显示状态 */
const drawerVisible = computed({
  get: () => props.modelValue,
  set: (val) => {
    emit('update:modelValue', val)
  }
})

/** 抽屉关闭前的回调（用于拦截关闭操作） */
const handleBeforeClose = async (done: () => void) => {
  // 如果数据已被修改，且不是查看模式，显示确认对话框
  if (isFormModified.value && props.mode !== 'view') {
    try {
      await ElMessageBox.confirm('数据未保存，要退出吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      // 用户确认退出，关闭抽屉
      isFormModified.value = false
      initialFormData.value = null
      done()
    } catch {
      // 用户取消，不关闭抽屉（不调用 done）
      return
    }
  } else {
    // 没有修改或查看模式，直接关闭
    done()
  }
}

/** 抽屉标题 */
// ==================== 内部模式管理 ====================
/**
 * 当前实际的操作模式
 * 用于处理拷贝新增时从修改模式切换到新增模式的情况
 * - 初始值：props.mode
 * - 拷贝新增时：切换为 'add'
 * - 窗口打开时：重置为 props.mode
 */
const currentMode = ref<'add' | 'edit' | 'view'>(props.mode)

// 监听 props.mode 变化，同步更新内部模式（窗口重新打开时）
watch(() => props.mode, (newMode) => {
  currentMode.value = newMode
})

// 监听窗口打开/关闭，重置内部模式
watch(() => drawerVisible.value, (val) => {
  if (val) {
    // 窗口打开时，重置为 props.mode
    currentMode.value = props.mode
  }
})

const drawerTitle = computed(() => {
  // 如果提供了 title，直接使用（优先级最高）
  if (props.title) {
    return props.title
  }
  
  // 根据模式生成操作方式（使用内部模式，支持拷贝新增时的模式切换）
  const operationMap = {
    add: '新增',
    edit: '修改',
    view: '查看'
  }
  const operation = operationMap[currentMode.value] || '操作'
  
  // 如果提供了 pageTitle，返回 "主窗口标题 - 操作方式"
  if (props.pageTitle) {
    return `${props.pageTitle} - ${operation}`
  }
  
  // 否则只返回操作方式
  return operation
})

/** 是否只读模式（查看模式） */
const isViewMode = computed(() => currentMode.value === 'view')

// ==================== 按钮显示控制 ====================
/** 
 * 是否显示保存按钮
 * 在新增和修改模式下显示，查看模式下隐藏
 */
const showSaveButton = computed(() => !isViewMode.value)

/** 
 * 是否显示继续新增按钮
 * 仅在新增模式下显示，用于保存当前数据后继续新增下一条记录
 */
const showContinueNewButton = computed(() => currentMode.value === 'add')

/** 
 * 是否显示拷贝新增按钮
 * 在新增和修改模式下显示，用于保存当前数据后创建新记录并保留标记字段的值
 */
const showCopyNewButton = computed(() => currentMode.value === 'add' || currentMode.value === 'edit')

/** 计算抽屉宽度：左侧留600px，最小700px */
const drawerWidth = computed(() => {
  const defaultWidth = '700px'
  if (props.width) {
    if (typeof props.width === 'string' && props.width !== defaultWidth) {
      return props.width
    }
    if (typeof props.width === 'number') {
      return props.width
    }
  }
  return 'calc(100vw - 600px)'
})

// ==================== Tab 管理 ====================
/** Tab 列表（支持多 Tab 模式，可根据需要扩展） */
const filteredTabs = computed(() => {
  return props.tabs
})

const activeTab = ref('basic')

// 监听模式变化和过滤后的 tabs，确保 activeTab 始终有效
watch([() => props.mode, filteredTabs], ([, tabs]) => {
  if (tabs.length > 0) {
    const currentTabExists = tabs.find(tab => tab.name === activeTab.value)
    if (!currentTabExists) {
      activeTab.value = tabs[0].name
    }
  }
}, { immediate: true })

// ==================== 表单处理 ====================
const { formRegister, formMethods } = useForm()
const { getFormData, setValues, getElFormExpose, getComponentExpose } = formMethods

// 表单注册状态
const isFormRegistered = ref(false)

// 表单数据是否被修改（用于关闭前提示）
const isFormModified = ref(false)
// 初始表单数据（用于比较是否有修改）
const initialFormData = ref<any>(null)

// 表单实例引用（用于监听表单数据变化）
const formInstanceRef = ref<any>(null)

// ImagePlus 组件引用映射（字段名 -> ImagePlus 组件实例）
const imagePlusRefs = ref<Record<string, InstanceType<typeof ImagePlus>>>({})

// 表单注册回调
const handleFormRegister = (formRef: any, elFormRef: any) => {
  formRegister(formRef, elFormRef)
  formInstanceRef.value = formRef
  isFormRegistered.value = true
  // 表单注册后，初始化数据
  nextTick(() => {
    initFormData()
  })
}

/**
 * 转换表单字段配置，处理特殊字段类型
 * 确保与 Dish/components/Response.vue 的字段转换逻辑和样式保持一致
 */
const convertFormSchema = (schema: FreeFormField[]): FormSchema[] => {
  return schema.map((field) => {
    // ==================== 扩展点1：字段级别的自定义转换 ====================
    // 优先使用字段自身的 customConvert
    if (field.customConvert) {
      const customResult = field.customConvert(field, props.currentRow || {}, props.mode)
      if (customResult !== null) {
        return customResult
      }
      // 如果返回 null，继续使用模板默认处理
    }
    
    // ==================== 扩展点2：全局自定义字段转换 ====================
    // 如果提供了全局转换函数，优先使用
    if (props.customFieldConvert) {
      const globalResult = props.customFieldConvert(field, props.currentRow || {})
      if (globalResult !== null) {
        return globalResult
      }
    }
    
    let baseField: FormSchema & { type?: string } = {
      ...field,
      type: field.type,
      componentProps: field.componentProps ? {
        ...field.componentProps,
        // 设置默认样式：width: 100%（如果未定义或未设置 width）
        style: {
          width: '100%',
          ...(field.componentProps.style || {})
        },
        // 只在查看模式下禁用，保留原有的 disabled 设置
        disabled: isViewMode.value || field.componentProps?.disabled || false
      } : {
        style: {
          width: '100%'
        },
        disabled: isViewMode.value || false
      }
    }
    
    // ==================== 选项数据处理：支持 options、optionsApi、原始值三种情况 ====================
    // 情况1：如果配置了 options（在 componentProps 中），优先使用 options
    // 情况2：如果配置了 optionsApi，使用自动获取的数据（按 dsOptions 规则）
    // 情况3：否则，按原始值在下拉组件中显示（如果字段类型是 select）
    
    // 检查字段类型是否为 select（包括原来的 select 和 selection）
    const isSelectType = field.type === 'select' || field.type === 'selection'
    
    if (isSelectType) {
      // 情况1：如果 componentProps 中已有 options，保留它（优先级最高）
      if (baseField.componentProps && (baseField.componentProps as any).options) {
        // 已有 options，不做处理
      }
      // 情况2：如果字段配置了 optionsApi，使用自动获取的数据
      else if (fieldOptionsData.value[field.field] && fieldOptionsData.value[field.field].length > 0) {
        baseField = {
          ...baseField,
          componentProps: {
            ...baseField.componentProps,
            options: fieldOptionsData.value[field.field]
          },
          optionApi: undefined // 移除 optionApi，避免重复请求
        }
      } 
      // 兼容旧的方式：如果主窗口提供了该字段的选项数据，使用主窗口的数据（已废弃）
      else if (props.fieldOptions && props.fieldOptions[field.field]) {
        const optionsData = props.fieldOptions[field.field]
        const options = typeof optionsData === 'function' ? optionsData() : optionsData
        baseField = {
          ...baseField,
          componentProps: {
            ...baseField.componentProps,
            options: options
          },
          optionApi: undefined // 移除 optionApi，避免重复请求
        }
      }
      // 情况3：如果没有配置 options 或 optionsApi，确保组件类型为 Select，让原始值在下拉组件中显示
      else {
        // 确保组件类型为 Select
        if (!baseField.component || baseField.component !== 'Select') {
          baseField = {
            ...baseField,
            component: 'Select'
          }
        }
      }
    } else {
      // 非 select 类型字段，保持原有逻辑
      if (fieldOptionsData.value[field.field] && fieldOptionsData.value[field.field].length > 0) {
        baseField = {
          ...baseField,
          componentProps: {
            ...baseField.componentProps,
            options: fieldOptionsData.value[field.field]
          },
          optionApi: undefined // 移除 optionApi，避免重复请求
        }
      } else if (props.fieldOptions && props.fieldOptions[field.field]) {
        // 兼容旧的方式：如果主窗口提供了该字段的选项数据，使用主窗口的数据（已废弃）
        const optionsData = props.fieldOptions[field.field]
        const options = typeof optionsData === 'function' ? optionsData() : optionsData
        baseField = {
          ...baseField,
          componentProps: {
            ...baseField.componentProps,
            options: options
          },
          optionApi: undefined // 移除 optionApi，避免重复请求
        }
      }
    }

    // 处理图片字段
    if (field.type === 'image') {
      return {
        ...baseField,
        formItemProps: {
          ...field.formItemProps,
          slots: {
            default: (data: any) => {
              const imageField = field.field

              // 初始化图片数据
              if (!data[imageField]) {
                data[imageField] = []
              }

              return (
                <ImagePlus
                  ref={(el: any) => {
                    if (el) {
                      imagePlusRefs.value[imageField] = el
                    }
                  }}
                  modelValue={data[imageField]}
                  // @ts-ignore - TSX 中 onUpdate:modelValue 的类型定义问题，但实际运行时是支持的
                  onUpdate:modelValue={(val: any[]) => {
                    // 直接赋值，data 是响应式对象 formModel.value 的引用
                    data[imageField] = val
                  }}
                  disabled={isViewMode.value}
                  limit={10}
                  size={field.size || 'normal'}
                />
              )
            }
          }
        }
      }
    }

    return baseField
  })
}

/** 转换后的表单字段配置 */
const convertedFormSchema = computed(() => convertFormSchema(props.formSchema))

/**
 * 根据当前 Tab 过滤字段
 */
const getFieldsByTab = (tabName: string) => {
  const tab = props.tabs.find(t => t.name === tabName)
  if (!tab || !tab.fields || tab.fields.length === 0) {
    return convertedFormSchema.value
  }
  return convertedFormSchema.value.filter(field => tab.fields!.includes(field.field))
}

// ==================== 数据初始化 ====================
/**
 * 创建默认表单数据
 * 
 * 根据 formSchema 生成包含所有字段默认值的表单数据对象
 * 用于新增模式的表单初始化
 * 
 * 处理逻辑：
 * 1. 如果字段配置中有 value，使用该值
 * 2. 图片类型字段如果没有 value，默认值为空数组
 * 3. 必填的文本类型字段如果没有 value，默认值为空字符串（与 ImportGrid 保持一致）
 * 
 * @returns {object} 默认表单数据对象
 */
const createDefaultFormData = (): any => {
  const defaultData: any = {}
  
  // 遍历 formSchema，设置所有有默认值的字段
  props.formSchema.forEach(field => {
    if (field.value !== undefined) {
      // 如果字段配置中有 value，使用该值
      defaultData[field.field] = field.value
    } else if (field.type === 'image') {
      // 图片类型字段如果没有默认值，初始化为空数组
      defaultData[field.field] = []
    } else if (field.component === 'Input' && field.formItemProps?.required) {
      // 必填的文本输入字段如果没有默认值，初始化为空字符串（与 ImportGrid 保持一致）
      defaultData[field.field] = ''
    }
    // 其他类型默认值为 undefined，不需要设置
  })
  
  return defaultData
}

/**
 * 初始化表单数据
 */
const initFormData = async () => {
  // 等待表单注册完成
  await nextTick()
  
  let formData: any = {}
  
  if (props.currentRow && (props.mode === 'edit' || props.mode === 'view')) {
    formData = { ...props.currentRow }
    // 处理图片字段（排序并移除排序前缀）
    // 从表单字段配置中提取 type === 'image' 的字段名
    const imageFields = (props.formSchema || [])
      .filter((field) => field.type === 'image')
      .map((field) => field.field)
    
    formData = processImageFields(formData, imageFields, {
      processList: true,
      cleanArray: false
    })
    await setValues(formData)
  } else {
    // 新增模式：使用默认表单数据
    formData = createDefaultFormData()
    await setValues(formData)
  }
  
  // ==================== 扩展点4：初始化后的钩子 ====================
  if (props.afterInit) {
    props.afterInit(formData)
  }
  
  // 保存初始表单数据，用于后续比较是否有修改
  initialFormData.value = JSON.parse(JSON.stringify(formData))
  isFormModified.value = false
}

// 监听 currentRow 变化（仅在表单已注册时更新）
watch(() => props.currentRow, () => {
  if (isFormRegistered.value) {
    initFormData()
  }
}, { deep: true })

// 监听 drawerVisible 变化，关闭时清空表单，打开时初始化选项数据
watch(() => drawerVisible.value, async (val) => {
  if (val) {
    // 窗口打开时，初始化选项数据
    await initFieldOptions()
    // 抽屉打开时，重置注册状态，等待表单注册
    isFormRegistered.value = false
    isFormModified.value = false
    initialFormData.value = null
  } else {
    // 抽屉关闭时，重置状态
    isFormRegistered.value = false
    isFormModified.value = false
    initialFormData.value = null
  }
})

// 监听表单数据变化，标记为已修改（仅在新增和编辑模式下）
watch(() => {
  if (!isFormRegistered.value || !formInstanceRef.value || props.mode === 'view') {
    return null
  }
  // 直接访问表单实例的 formModel
  return formInstanceRef.value?.formModel
}, (newData) => {
  if (!newData || !initialFormData.value || props.mode === 'view') {
    return
  }
  
  // 比较当前表单数据与初始数据是否一致
  try {
    const currentDataStr = JSON.stringify(newData)
    const initialDataStr = JSON.stringify(initialFormData.value)
    isFormModified.value = currentDataStr !== initialDataStr
  } catch {
    // 如果比较失败，不更新修改状态
  }
}, { deep: true, immediate: false })

// ==================== 方法 ====================
/**
 * 重置表单为新增模式的初始值
 * 
 * 功能说明：
 * - 将所有字段重置为初始化新增时的默认值
 * - 不保留上次的输入结果，确保表单完全清空
 * - 逻辑与 initFormData 的新增模式保持一致
 * 
 * 使用场景：
 * - 继续新增功能：保存当前数据后，重置表单继续新增下一条记录
 * - 表单初始化：确保表单处于干净的新增状态
 * 
 * @see resetFormToCopyNew - 重置表单为拷贝新增模式的初始值（保留标记字段）
 */
const resetFormToInitial = async () => {
  // ==================== 1. 重置表单字段 ====================
  // 清除所有字段的值和验证状态
  const formInstance = await getElFormExpose()
  if (formInstance) {
    formInstance.resetFields()
    await nextTick()
  }
  
  // ==================== 2. 构建新增模式的初始表单数据 ====================
  // 复用 createDefaultFormData 函数，避免重复代码
  const newFormData = createDefaultFormData()
  
  // ==================== 3. 应用初始值到表单 ====================
  await setValues(newFormData)
  await nextTick()
  
  // ==================== 4. 清除验证状态 ====================
  if (formInstance) {
    formInstance.clearValidate()
  }
  
  // ==================== 5. 更新表单状态 ====================
  // 保存新的初始表单数据，用于后续的修改检测
  initialFormData.value = JSON.parse(JSON.stringify(newFormData))
  isFormModified.value = false
  
  // ==================== 6. 扩展点：初始化后的钩子 ====================
  if (props.afterInit) {
    props.afterInit(newFormData)
  }
}

/**
 * 公共的保存数据流程
 * 
 * 功能说明：
 * 这是一个统一的保存数据流程，包含完整的保存前处理逻辑。
 * 所有保存操作（保存、继续新增、拷贝新增）都使用此函数，确保逻辑一致。
 * 
 * 处理流程：
 * 1. 等待表单注册完成
 * 2. 数据校验（失败则中断，返回 null）
 * 3. 获取表单数据
 * 4. 图片上传处理（失败则中断，在 PromptInfo 中显示错误信息，返回 null）
 * 5. 提交前钩子处理（失败则中断，在 PromptInfo 中显示错误信息，返回 null）
 * 6. 数据提交（失败则中断，在 PromptInfo 中显示错误信息，返回 null）
 * 7. 保存成功后：重置修改标记，触发 success 事件，执行成功回调
 * 
 * 使用场景：
 * - handleSave：保存后关闭窗口
 * - handleContinueNew：保存后重置表单继续新增
 * - handleCopyNew：保存后重置表单并保留标记字段
 * 
 * @param onSuccess - 保存成功后的回调函数，参数为保存的表单数据
 * @returns 返回处理后的表单数据，如果处理失败则返回 null
 * 
 * @example
 * await processSaveData(async (formData) => {
 *   // 保存成功后的处理逻辑
 *   console.log('保存成功', formData)
 * })
 */
const processSaveData = async (onSuccess?: (formData: any) => Promise<void> | void): Promise<any | null> => {
  // 等待表单注册完成
  if (!isFormRegistered.value) {
    // 等待多个 nextTick 确保表单已注册
    await nextTick()
    await nextTick()
  }
  
  const elForm = await getElFormExpose()
  if (!elForm) {
    ElMessage.error('表单未注册，请稍后重试')
    return null
  }
  
  // ==================== 1. 数据校验 ====================
  const valid = await elForm.validate()
  if (!valid) {
    // 校验失败，操作中断，显示校验错误信息（逻辑不变）
    return null
  }

  let formData = await getFormData()
  
  // ==================== 处理模式切换（继续新增/拷贝新增）====================
  // 如果当前模式是新增，但数据中包含 id 字段，需要清除 id 以确保调用新增API
  // 这是因为继续新增/拷贝新增时，currentMode 已切换为 'add'，但 formData 可能仍包含原记录的 id
  if (currentMode.value === 'add' && formData && 'id' in formData) {
    // 创建新对象，避免直接修改原对象
    formData = { ...formData }
    delete formData.id
  }
  
  // ==================== 处理图片字段上传 ====================
  // 如果存在未上传的图片，则处理上传（参考 Test/components/Response.vue 第 207-211 行）
  try {
    // 遍历所有图片字段，上传待上传的图片
    for (const field of props.formSchema) {
      if (field.type === 'image') {
        const imageField = field.field
        const imagePlusRef = imagePlusRefs.value[imageField]
        
        // 如果 ImagePlus 组件引用存在，使用组件的方法上传图片
        if (imagePlusRef && typeof imagePlusRef.uploadPendingImages === 'function') {
          await imagePlusRef.uploadPendingImages()
        }
      }
    }
    
    // 上传完成后，重新获取表单数据（因为图片数据已更新）
    // 注意：直接返回 getFormData() 的数据，不要使用 getNormalizedImages
    // 因为后端需要接收包含 ?add、?delete、?original 等标记的完整图片列表
    formData = await getFormData()
    
    // 处理模式切换（重新获取数据后，需要再次处理 id 字段）
    if (currentMode.value === 'add' && formData && 'id' in formData) {
      formData = { ...formData }
      delete formData.id
    }
    
    // 处理图片字段：确保只保留字符串格式的图片（过滤掉数组格式的未上传图片）
    // 因为 uploadPendingImages 已经将数组格式转换为字符串格式了
    for (const field of props.formSchema) {
      if (field.type === 'image') {
        const imageField = field.field
        if (formData[imageField] && Array.isArray(formData[imageField])) {
          // 过滤掉数组格式的项（如果还有未上传的图片，说明上传失败）
          formData[imageField] = formData[imageField].filter((item: any) => typeof item === 'string')
        }
      }
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '图片上传失败'
    // 在 PromptInfo 中显示错误信息
    showInfo('error', errorMessage)
    return null
  }
  
  // ==================== 扩展点3：提交前的数据处理钩子 ====================
  if (props.beforeSubmit) {
    try {
      formData = await props.beforeSubmit(formData) || formData
    } catch (error) {
      // 如果钩子抛出错误，在 PromptInfo 中显示错误信息
      const errorMessage = error instanceof Error ? error.message : '数据处理失败'
      showInfo('error', errorMessage)
      return null
    }
  }
  
  // ==================== 2. 数据保存 ====================
  if (props.submitApi) {
    try {
      // 调用 submitApi，传入 formData 和 currentMode
      // 如果 submitApi 支持 mode 参数，则使用 currentMode（支持继续新增/拷贝新增时的模式切换）
      // 如果 submitApi 不支持 mode 参数，则只传入 formData（向后兼容）
      // 为了确保调用新增API，我们已经在前面清除了 formData 中的 id 字段
      if (props.submitApi.length > 1) {
        // submitApi 支持 mode 参数
        // 确保 mode 是 'add' 或 'edit'（不会是 'view'，因为 view 模式下不会调用保存）
        const mode: 'add' | 'edit' = currentMode.value === 'view' ? 'edit' : currentMode.value
        await props.submitApi(formData, mode)
      } else {
        // submitApi 不支持 mode 参数，只传入 formData（向后兼容）
        await props.submitApi(formData)
      }
      // 保存成功后，重置修改标记
      isFormModified.value = false
      initialFormData.value = null
      emit('success')
      
      // 执行成功回调，传递保存的表单数据
      if (onSuccess) {
        await onSuccess(formData)
      }
      
      return formData
    } catch (error) {
      // 保存失败，不关闭窗口，在 PromptInfo 中显示错误信息
      const errorMessage = error instanceof Error ? error.message : '保存失败'
      showInfo('error', errorMessage)
      return null
    }
  } else {
    // 否则触发 save 事件，由父组件处理
    emit('save', formData)
    // 执行成功回调（如果父组件处理成功），传递表单数据
    if (onSuccess) {
      await nextTick()
      await onSuccess(formData)
    }
    return formData
  }
}

/**
 * 处理保存操作
 * 
 * 功能流程：
 * 1. 数据校验（失败则中断）
 * 2. 图片上传处理（失败则中断）
 * 3. 提交前钩子处理（失败则中断）
 * 4. 数据保存（失败则中断，在 PromptInfo 中显示错误信息）
 * 5. 保存成功后：显示成功消息并关闭窗口
 * 
 * 使用场景：
 * - 新增模式：保存新记录后关闭窗口
 * - 修改模式：保存修改后关闭窗口
 * 
 * @see processSaveData - 公共的保存数据流程
 */
const handleSave = async () => {
  await processSaveData(async () => {
    // ==================== 保存成功后的处理 ====================
    // 显示成功消息（使用内部模式，支持拷贝新增时的模式切换）
    ElMessage.success(currentMode.value === 'add' ? '新增成功' : '修改成功')
    
    // 关闭窗口
    drawerVisible.value = false
  })
}

// ==================== 特殊字段处理函数 ====================

/**
 * 处理 order_number 字段的特殊计算
 * 将原排序号向上取整到10的倍数，再加10
 * 
 * @param originalValue - 原排序号的值
 * @returns 计算后的新排序号，如果不是有效数字则返回原值
 * 
 * @example
 * processOrderNumber(20) // 30 (20 -> 20 -> 30)
 * processOrderNumber(21) // 40 (21 -> 30 -> 40)
 * processOrderNumber(25) // 40 (25 -> 30 -> 40)
 * processOrderNumber('abc') // 'abc' (无效数字，返回原值)
 */
const processOrderNumber = (originalValue: any): any => {
  if (originalValue === null || originalValue === undefined) {
    return originalValue
  }
  
  // 尝试转换为数字
  const numValue = Number(originalValue)
  
  // 检查是否为有效数字
  if (!isNaN(numValue) && isFinite(numValue)) {
    // 向上取整到10的倍数，再加10
    const roundedToTen = Math.ceil(numValue / 10) * 10
    return roundedToTen + 10
  }
  
  // 如果不是有效数字，直接返回原值
  return originalValue
}

/**
 * 处理 name_unique 字段的焦点定位
 * 在完成拷贝后，将焦点定位到该字段并全选文字
 * 
 * @param fieldName - 字段名，默认为 'name_unique'
 */
const focusNameUniqueField = async (fieldName: string = 'name_unique') => {
  // 等待 DOM 更新完成
  await nextTick()
  await nextTick() // 多等待一次，确保表单组件已完全渲染
  
  try {
    // 获取字段的组件实例
    const componentExpose = await getComponentExpose(fieldName)
    
    if (componentExpose) {
      // Element Plus Input 组件支持 focus 和 select 方法
      // 等待一下再设置焦点，确保组件已完全渲染
      setTimeout(() => {
        if (componentExpose.focus) {
          componentExpose.focus()
        }
        // 如果是 Input 组件，尝试全选文字
        if (componentExpose.select) {
          componentExpose.select()
        } else if (componentExpose.$el) {
          // 如果组件没有 select 方法，尝试直接操作 DOM
          const inputElement = componentExpose.$el.querySelector('input') || componentExpose.$el
          if (inputElement && inputElement.select) {
            inputElement.select()
          }
        }
      }, 100)
    }
  } catch (error) {
    // 如果获取组件实例失败，静默处理（不影响主要功能）
    console.warn(`无法定位 ${fieldName} 字段焦点:`, error)
  }
}

/**
 * 特殊字段值处理映射表
 * 定义哪些字段需要进行特殊处理，以及对应的处理函数
 * 
 * 扩展方式：
 * 1. 在此对象中添加新的字段名和处理函数
 * 2. 处理函数接收原值，返回处理后的值
 * 
 * @example
 * // 添加新的特殊字段处理
 * specialFieldProcessors: {
 *   order_number: processOrderNumber,
 *   custom_field: (value) => value + '_suffix'
 * }
 */
const specialFieldProcessors: Record<string, (value: any) => any> = {
  order_number: processOrderNumber
}

/**
 * 特殊字段后处理映射表
 * 定义哪些字段在表单初始化后需要进行额外的处理（如焦点定位）
 * 
 * 扩展方式：
 * 1. 在此对象中添加新的字段名和处理函数
 * 2. 处理函数应该是异步函数，用于执行后处理操作
 * 
 * @example
 * // 添加新的特殊字段后处理
 * specialFieldPostProcessors: {
 *   name_unique: focusNameUniqueField,
 *   custom_field: async () => { await someCustomAction() }
 * }
 */
const specialFieldPostProcessors: Record<string, () => Promise<void>> = {
  name_unique: () => focusNameUniqueField('name_unique')
}

/**
 * 重置表单为拷贝新增模式的初始值
 * 
 * 功能说明：
 * - 对标记了 newCopy=true 的字段，保留上一条记录的值
 * - 对其他字段，使用初始化新增时的默认值
 * - 图片字段特殊处理：保留图片但重新标记为 ?add（新增操作）
 * - 支持特殊字段的自定义处理（如 order_number、name_unique 等）
 * 
 * 使用场景：
 * - 拷贝新增功能：保存当前数据后，创建新记录并保留部分字段值
 * 
 * 特殊字段处理：
 * - order_number: 自动计算新的排序号（向上取整到10的倍数 + 10）
 * - name_unique: 完成拷贝后自动定位焦点并全选文字
 * 
 * @param savedData - 已保存的数据，用于拷贝标记字段的值
 * 
 * @example
 * // 在字段配置中设置 newCopy=true
 * { field: 'name', label: '名称', newCopy: true }
 * // 拷贝新增时，name 字段会保留上一条记录的值
 * 
 * // 特殊字段示例
 * { field: 'order_number', label: '排序号', newCopy: true }
 * // 拷贝新增时，order_number 会自动计算新值（如 20 -> 30）
 */
const resetFormToCopyNew = async (savedData: any) => {
  // ==================== 1. 重置表单字段 ====================
  // 清除所有字段的值和验证状态
  const formInstance = await getElFormExpose()
  if (formInstance) {
    formInstance.resetFields()
    await nextTick()
  }
  
  // ==================== 2. 构建拷贝新增模式的初始表单数据 ====================
  // 先获取默认表单数据（复用 createDefaultFormData 函数）
  const newFormData = createDefaultFormData()
  
  // ==================== 2.1 处理普通字段 ====================
  // 根据 newCopy 标记决定使用哪个值
  props.formSchema.forEach(field => {
    // 跳过图片字段，图片字段需要特殊处理
    if (field.type === 'image') {
      return
    }
    
    if (field.newCopy === true) {
      // 标记了 newCopy=true 的字段：保留上一条记录的值
      if (savedData && savedData[field.field] !== undefined) {
        const originalValue = savedData[field.field]
        
        // ==================== 特殊字段值处理 ====================
        // 检查是否有特殊字段处理器，如果有则使用处理器处理值
        if (specialFieldProcessors[field.field]) {
          newFormData[field.field] = specialFieldProcessors[field.field](originalValue)
        } else {
          // 普通字段：直接使用原值
          newFormData[field.field] = originalValue
        }
      }
    }
    // 如果 newCopy !== true，使用默认值（已在 createDefaultFormData 中设置）
  })
  
  // ==================== 2.2 处理图片字段 ====================
  // ImagePlus 组件会自动维护显示数据，不需要 imageDisplayField
  props.formSchema.forEach(field => {
    if (field.type === 'image') {
      const imageField = field.field
      
      if (field.newCopy === true && savedData) {
        // 图片字段标记了 newCopy=true：保留图片并重新标记为 ?add
        const savedImages = savedData[imageField]
        
        if (savedImages && Array.isArray(savedImages) && savedImages.length > 0) {
          // 拷贝图片数据，移除原有操作标记，重新标记为 ?add（新增操作）
          newFormData[imageField] = savedImages.map((img: any) => {
            if (typeof img === 'string') {
              // 移除操作标记（?original、?delete、?add 等），只保留路径
              const path = img.split('?')[0]
              return getImageUrlWithSuffix(path, ImageQuerySuffix.ADD)
            }
            return img
          })
        } else {
          // 如果没有图片数据，重置为空数组
          newFormData[imageField] = []
        }
      }
      // 如果 newCopy !== true，使用默认值（已在 createDefaultFormData 中设置为空数组）
    }
  })
  
  // ==================== 3. 应用初始值到表单 ====================
  await setValues(newFormData)
  await nextTick()
  
  // ==================== 4. 清除验证状态 ====================
  if (formInstance) {
    formInstance.clearValidate()
  }
  
  // ==================== 5. 更新表单状态 ====================
  // 保存新的初始表单数据，用于后续的修改检测
  initialFormData.value = JSON.parse(JSON.stringify(newFormData))
  isFormModified.value = false
  
  // ==================== 6. 扩展点：初始化后的钩子 ====================
  if (props.afterInit) {
    props.afterInit(newFormData)
  }
  
  // ==================== 7. 特殊字段后处理 ====================
  // 遍历所有标记了 newCopy=true 的字段，检查是否有后处理函数
  for (const field of props.formSchema) {
    if (field.newCopy === true && specialFieldPostProcessors[field.field]) {
      // 执行特殊字段的后处理（如焦点定位等）
      await specialFieldPostProcessors[field.field]()
      // 注意：如果有多个特殊字段需要后处理，这里会依次执行
      // 如果需要只处理第一个，可以添加 break
    }
  }
}

// ==================== 保存操作处理函数 ====================

/**
 * 处理继续新增操作
 * 
 * 功能流程：
 * 1. 数据校验（失败则中断）
 * 2. 图片上传处理（失败则中断）
 * 3. 提交前钩子处理（失败则中断）
 * 4. 数据保存（失败则中断，在 PromptInfo 中显示错误信息）
 * 5. 保存成功后：重置表单为新增状态，显示成功提示
 * 
 * 使用场景：
 * - 新增模式下，保存当前数据后继续新增下一条记录
 * - 所有字段都会被重置为初始值，不保留上次输入
 * 
 * @see processSaveData - 公共的保存数据流程
 * @see resetFormToInitial - 重置表单为新增模式的初始值
 */
const handleContinueNew = async () => {
  await processSaveData(async () => {
    // ==================== 保存成功后的处理 ====================
    // 切换模式为新增（确保后续保存时是新增操作，而不是修改操作）
    currentMode.value = 'add'
    
    // 重置表单为新增状态的初始值（所有字段都重置，不保留上次输入）
    await resetFormToInitial()
    
    // 显示成功提示信息
    showInfo('info', '数据保存成功，继续新增下一条...')
  })
}

/**
 * 处理拷贝新增操作
 * 
 * 功能流程：
 * 1. 检查数据是否被修改
 *    - 如果数据未修改：直接切换模式为新增，重置表单为拷贝新增状态，跳过保存
 *    - 如果数据已修改：执行保存流程
 * 2. 数据校验（失败则中断）
 * 3. 图片上传处理（失败则中断）
 * 4. 提交前钩子处理（失败则中断）
 * 5. 数据保存（失败则中断，在 PromptInfo 中显示错误信息）
 * 6. 保存成功后：切换模式为新增，重置表单为拷贝新增状态，保留标记字段的值，显示成功提示
 * 
 * 使用场景：
 * - 新增或修改模式下，保存当前数据后创建新记录
 * - 标记了 newCopy=true 的字段会保留上一条记录的值
 * - 其他字段使用初始化新增时的默认值
 * 
 * 与继续新增的区别：
 * - 继续新增：所有字段都重置为初始值
 * - 拷贝新增：标记字段保留上一条记录的值，其他字段重置为初始值
 * 
 * @see processSaveData - 公共的保存数据流程
 * @see resetFormToCopyNew - 重置表单为拷贝新增模式的初始值
 */
const handleCopyNew = async () => {
  // ==================== 检查数据是否被修改 ====================
  // 如果数据没有变化，跳过保存，直接重置表单为拷贝新增状态
  if (!isFormModified.value) {
    // 获取当前表单数据，用于拷贝标记字段的值
    const currentFormData = await getFormData()
    
    // 切换模式为新增（确保后续保存时是新增操作，而不是修改操作）
    currentMode.value = 'add'
    
    // 重置表单为拷贝新增状态（标记字段保留当前记录的值）
    await resetFormToCopyNew(currentFormData)
    
    // 显示提示信息（注意：这里没有保存，所以提示信息不同）
    showInfo('info', '已拷貝，請編輯數據...')
    return
  }
  
  // ==================== 数据已修改，执行保存流程 ====================
  await processSaveData(async (formData) => {
    // ==================== 保存成功后的处理 ====================
    // 切换模式为新增（确保后续保存时是新增操作，而不是修改操作）
    currentMode.value = 'add'
    
    // 重置表单为拷贝新增状态（标记字段保留上一条记录的值）
    await resetFormToCopyNew(formData)
    
    // 显示成功提示信息
    showInfo('info', '已保存並拷貝，請編輯數據...')
  })
}

/**
 * 处理取消
 */
const handleCancel = () => {
  drawerVisible.value = false
  emit('cancel')
}

// ==================== 信息提示 ====================
/** 信息类型 */
type InfoType = 'info' | 'warn' | 'error'

/** 信息提示组件引用 */
const prompInfoRef = ref<InstanceType<typeof PromptInfo>>()

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

// ==================== 暴露方法 ====================
defineExpose({
  submit: handleSave,
  getFormData,
  setValues,
  getElFormExpose,
  showInfo // 显示信息提示
})
</script>

<template>
  <ElDrawer
    v-model="drawerVisible"
    :size="drawerWidth"
    direction="rtl"
    :close-on-click-modal="props.closeOnClickModal"
    :with-header="true"
    :title="drawerTitle"
    :before-close="handleBeforeClose"
    destroy-on-close
    class="base-free-drawer"
  >
    <!-- 表单内容区域（可滚动） -->
    <div class="base-free-content-wrapper">
      <ElScrollbar class="base-free-scrollbar">
        <div class="base-free-content">
          <div class="response-container">
            <!-- 按钮区域：提示信息 + 按钮 -->
            <!-- ==================== 扩展点6：按钮区域自定义 ==================== -->
            <slot name="buttons" :save="handleSave" :cancel="handleCancel" :continue-new="handleContinueNew" :copy-new="handleCopyNew" :mode="props.mode" :save-loading="props.saveLoading" :show-continue-new="showContinueNewButton" :show-copy-new="showCopyNewButton">
              <div class="response-buttons-wrapper">
                <div class="response-buttons-info">
                  <PromptInfo ref="prompInfoRef" />
                </div>
                <div class="response-buttons">
                  <ButtonPlus
                    v-if="showSaveButton"
                    stype="save"
                    :loading="props.saveLoading"
                    @click="handleSave"
                  />
                  <ButtonPlus
                    v-if="showContinueNewButton"
                    stype="newcontinue"
                    :loading="props.saveLoading"
                    @click="handleContinueNew"
                  />
                  <ButtonPlus
                    v-if="showCopyNewButton"
                    stype="newcopy"
                    :loading="props.saveLoading"
                    @click="handleCopyNew"
                  />
                  <ButtonPlus
                    stype="return"
                    @click="handleCancel"
                  />
                </div>
              </div>
            </slot>
            
            <!-- Tab 组件 -->
            <ElTabs v-model="activeTab">
              <ElTabPane
                v-for="tab in filteredTabs"
                :key="tab.name"
                :label="tab.label"
                :name="tab.name"
              >
                <!-- ==================== 扩展点5：Tab 级别的自定义内容 ==================== -->
                <!-- 如果 Tab 配置了 customContent: true，使用插槽内容 -->
                <template v-if="tab.customContent">
                  <slot :name="`tab-${tab.name}`" :tab="tab" :current-row="props.currentRow" :mode="props.mode">
                    <!-- 默认插槽内容为空，由使用方提供 -->
                  </slot>
                </template>
                <!-- 默认 Tab：显示表单 -->
                <template v-else>
                  <Form
                    :key="`form-${tab.name}-${drawerVisible}`"
                    :rules="props.rules"
                    :validate-on-rule-change="false"
                    @register="handleFormRegister"
                    :schema="getFieldsByTab(tab.name)"
                  />
                </template>
              </ElTabPane>
            </ElTabs>
          </div>
        </div>
      </ElScrollbar>
    </div>
  </ElDrawer>
</template>

<style lang="less">
:deep(.base-free-drawer) {
  .el-drawer {
    width: max(700px, calc(100vw - 600px)) !important;
    right: 0 !important;
    left: auto !important;
  }
}

:global(.base-free-drawer .el-drawer) {
  width: max(700px, calc(100vw - 600px)) !important;
  right: 0 !important;
  left: auto !important;
}

.base-free-content-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.base-free-scrollbar {
  flex: 1;
  min-height: 0;
  
  :deep(.el-scrollbar__wrap) {
    overflow-x: hidden;
  }
  
  .base-free-content {
    padding: 0 20px 20px 20px;
    max-width: 720px;
    margin-left: 0;
    margin-right: auto;
    
    :deep(.el-tabs) {
      padding: 0;
    }
    
    :deep(.el-tabs__header) {
      margin: 0;
      padding: 0;
    }
    
    :deep(.el-tabs__content) {
      padding: 0;
    }
  }
}

.response-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.response-buttons-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 0;
  margin-bottom: 15px;
}

.response-buttons-info {
  flex: 1;
  min-width: 0;
}

.response-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  
  // ButtonPlus 组件已内置 margin-left: 0，无需额外设置
  // 仅保留对原生 ElButton 的样式覆盖（如果有使用）
  :deep(.el-button:not(.my-button)) {
    margin: 0 !important;
  }
}

.base-free-drawer {
  :deep(.el-drawer__header) {
    margin-bottom: 0;
    padding: 15px 20px;
    border-bottom: 1px solid var(--el-border-color);
  }

  :deep(.el-drawer__body) {
    padding: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  :deep(.el-drawer__footer) {
    padding: 15px 20px;
    border-top: 1px solid var(--el-border-color);
  }
}

// 图片上传样式（与 Dish/components/Response.vue 保持一致）
.base-free-content {
  .image-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    padding: 0;
  }

  .image-container {
    .image-group {
      position: relative;
      width: 100px;
      height: 100px;
      margin: 0;
    }

    .image-item {
      width: 100%;
      height: 100%;
      border-radius: 6px;
      border: 1px solid #dcdfe6;
      transition: all 0.3s ease;
      cursor: pointer;
    }

    .image-item:hover {
      transform: scale(1.05);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    // ElImage 组件样式
    .image-group :deep(.el-image) {
      width: 100%;
      height: 100%;
      border-radius: 6px;
    }

    .image-group :deep(.el-image__inner) {
      border-radius: 6px;
      object-fit: cover;
    }

    .remove-btn {
      position: absolute;
      top: -6px;
      right: -6px;
      width: 24px;
      height: 24px;
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
    }

    .image-group:hover .remove-btn {
      opacity: 1;
    }

    .image-group.dragging {
      opacity: 0.5;
      border-color: #409eff;
      transform: scale(0.95);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
      cursor: grabbing;
      z-index: 1000;
    }

    .image-group.drag-over {
      transform: scale(1.15);
      border: 2px solid #3b82f6;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
      transform: scale(1.05);
      z-index: 10;
      transition: all 0.2s ease;
    }

    .image-group-uploader {
      width: 180px;
      height: 100px;
      flex-shrink: 0;
    }

    .image-group-uploader .el-upload {
      border: 2px dashed #c0c4cc;
      width: 100% !important;
      height: 96px !important;
      margin: 0 !important;
      border-radius: 6px;
    }

    .el-upload:hover {
      border-color: #409eff;
      background: #f0f7ff;
      color: #409eff;
    }

    .image-group-uploader .el-upload-dragger {
      width: 100% !important;
      height: 100% !important;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .el-icon--upload {
      width: 54px;
      height: 54px;
      margin-top: 0;
    }

    .upload-text {
      font-size: 12px;
      margin-top: -20px;
      text-align: center;
    }
  }
}
</style>
